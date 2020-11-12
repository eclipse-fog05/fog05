#![allow(unused_variables)]

extern crate machine_uid;
extern crate serde;
extern crate serde_json;
extern crate serde_yaml;

use std::collections::HashMap;
use std::process;
use std::time::Duration;

use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};
use async_std::task;

use log::{error, info, trace};

use zenoh::*;

use zrpc::ZServe;
use zrpc_macros::zserver;

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::im::fdu::*;
use fog05_sdk::im::fdu::{FDUDescriptor, FDURecord, FDUState};
use fog05_sdk::plugins::{HypervisorPlugin, NetworkingPluginClient};
use fog05_sdk::types::PluginKind;
use fog05_sdk::zconnector::ZConnector;

use serde::{Deserialize, Serialize};

use async_ctrlc::CtrlC;
use uuid::Uuid;

use structopt::StructOpt;

#[derive(StructOpt, Debug)]
struct DummyArgs {
    /// Config file
    #[structopt(short, long, default_value = "tcp/127.0.0.1:7447")]
    zenoh: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DummyHVSpecificInfo {
    pub netns: Uuid,
}

#[derive(Clone)]
pub struct DummyHVState {
    pub fdus: HashMap<Uuid, FDURecord>,
    pub uuid: Option<Uuid>,
}

#[derive(Clone)]
pub struct DummyHypervisor {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid: u32,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub net: Option<NetworkingPluginClient>,
    pub fdus: Arc<RwLock<DummyHVState>>,
}

#[zserver]
impl HypervisorPlugin for DummyHypervisor {
    async fn define_fdu(&mut self, fdu: FDUDescriptor) -> FResult<FDURecord> {
        log::debug!("Define FDU {:?}", fdu);
        log::trace!("Get node UUID");
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        log::trace!("Get RwLock");
        let mut guard = self.fdus.write().await;
        log::trace!("Creating instance UUID");
        let instance_uuid = Uuid::new_v4();
        log::trace!("Creating instance object");
        let instance = FDURecord {
            uuid: instance_uuid,
            fdu_uuid: fdu.uuid.unwrap(), //this is present because it is populated by the agent/orchestrator
            node: node_uuid,
            interfaces: Vec::new(),
            connection_points: Vec::new(),
            status: FDUState::DEFINED,
            error: None,
            hypervisor_specific: None,
        };
        log::trace!("Add instance to local state");
        guard.fdus.insert(instance_uuid, instance.clone());
        log::trace!("Add instance in zenoh");
        self.connector
            .global
            .add_node_instance(node_uuid, instance.clone())
            .await?;
        log::trace!("Instance status {:?}", instance.status);
        Ok(instance)
    }

    async fn undefine_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let instance = self
            .connector
            .global
            .get_node_instance(node_uuid, instance_uuid)
            .await?;
        match instance.status {
            FDUState::DEFINED => {
                let mut guard = self.fdus.write().await;
                guard.fdus.remove(&instance_uuid);
                self.connector
                    .global
                    .remove_node_instance(node_uuid, instance_uuid)
                    .await?;

                Ok(instance_uuid)
            }
            _ => Err(FError::TransitionNotAllowed),
        }
    }

    async fn configure_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        log::debug!("Configure FDU {:?}", instance_uuid);
        log::trace!("Get node UUID");
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        log::trace!("Get instance");
        let mut instance = self
            .connector
            .global
            .get_node_instance(node_uuid, instance_uuid)
            .await?;
        log::trace!("Check FDU status: {:?}", instance.status);
        match instance.status {
            FDUState::DEFINED => {
                let mut guard = self.fdus.write().await; //taking lock

                // Here we should create the network interfaces
                // connection points, etc...
                // dummy ask the creation of a namespace for FDU networking
                let descriptor = self
                    .agent
                    .as_ref()
                    .unwrap()
                    .fdu_info(instance.fdu_uuid)
                    .await??;
                let fdu_ns = self
                    .net
                    .as_ref()
                    .unwrap()
                    .create_network_namespace()
                    .await??;

                let hv_specific = DummyHVSpecificInfo { netns: fdu_ns.uuid };

                // Adding hv specific info
                instance.hypervisor_specific = Some(serde_json::to_string(&hv_specific).unwrap());
                //

                log::trace!("Created instance network namespace: {:?}", fdu_ns);

                let mut interfaces: Vec<FDURecordInterface> = Vec::new();
                let mut cps: HashMap<String, FDURecordConnectionPoint> = HashMap::new();
                for cp in descriptor.connection_points {
                    let vcp = self
                        .net
                        .as_ref()
                        .unwrap()
                        .create_connection_point()
                        .await??;

                    let fdu_cp = FDURecordConnectionPoint {
                        uuid: vcp.uuid,
                        id: cp.id.clone(),
                    };

                    log::trace!("Created connection point {:?} {:?}", vcp, fdu_cp);

                    cps.insert(cp.id, fdu_cp);
                    // we should ask the connection of the cp to the virtual network here
                }

                for intf in descriptor.interfaces {
                    let viface_config = fog05_sdk::types::VirtualInterfaceConfig {
                        if_name: intf.name.clone(),
                        kind: fog05_sdk::types::VirtualInterfaceConfigKind::VETH,
                    };
                    let viface = self
                        .net
                        .as_ref()
                        .unwrap()
                        .create_virtual_interface_in_namespace(viface_config, fdu_ns.uuid)
                        .await??;

                    log::trace!("Created virtual interface {:?}", viface);

                    let pair = match viface.kind {
                        fog05_sdk::types::VirtualInterfaceKind::VETH(info) => info.pair,
                        _ => return Err(FError::MalformedDescriptor),
                    };
                    let cp_uuid = match intf.cp_id {
                        Some(cp_id) => {
                            let cp = cps.get(&cp_id).ok_or(FError::NotFound)?;
                            self.net
                                .as_ref()
                                .unwrap()
                                .bind_interface_to_connection_point(pair, cp.uuid)
                                .await??;
                            Some(cp.uuid)
                        }
                        None => {
                            self.net
                                .as_ref()
                                .unwrap()
                                .move_interface_into_default_namespace(pair)
                                .await??;
                            None
                        }
                    };

                    // dummy hv creates all the faces as veth pairs
                    let fdu_intf = FDURecordInterface {
                        name: intf.name,
                        kind: intf.kind,
                        mac_address: intf.mac_address,
                        cp_uuid,
                        intf_uuid: viface.uuid,
                        virtual_interface: FDURecordVirtualInterface {
                            vif_kind: VirtualInterfaceKind::E1000,
                            bandwidht: None,
                        },
                    };
                    interfaces.push(fdu_intf)
                }
                instance.interfaces = interfaces;
                instance.connection_points = cps.into_iter().map(|(_, v)| v).collect();
                instance.status = FDUState::CONFIGURED;
                self.connector
                    .global
                    .add_node_instance(node_uuid, instance.clone())
                    .await?;
                guard.fdus.insert(instance_uuid, instance.clone());
                log::trace!("Instance status {:?}", instance.status);
                Ok(instance_uuid)
            }
            _ => Err(FError::TransitionNotAllowed),
        }
    }

    async fn clean_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        log::debug!("Clean FDU {:?}", instance_uuid);
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut instance = self
            .connector
            .global
            .get_node_instance(node_uuid, instance_uuid)
            .await?;
        match instance.status {
            FDUState::CONFIGURED => {
                let mut guard = self.fdus.write().await;

                let hv_specific = serde_json::from_str::<DummyHVSpecificInfo>(
                    &instance.clone().hypervisor_specific.unwrap(),
                )
                .unwrap();

                self.net
                    .as_ref()
                    .unwrap()
                    .delete_network_namespace(hv_specific.netns)
                    .await??;

                for iface in instance.interfaces {
                    self.net
                        .as_ref()
                        .unwrap()
                        .delete_virtual_interface(iface.intf_uuid)
                        .await??;
                    log::trace!("Deleted virtual interface {:?}", iface);
                }

                for cp in instance.connection_points {
                    self.net
                        .as_ref()
                        .unwrap()
                        .delete_connection_point(cp.uuid)
                        .await??;
                    log::trace!("Deletted connection point {:?}", cp);
                }

                instance.interfaces = Vec::new();
                instance.connection_points = Vec::new();
                instance.status = FDUState::DEFINED;
                self.connector
                    .global
                    .add_node_instance(node_uuid, instance.clone())
                    .await?;
                guard.fdus.insert(instance_uuid, instance.clone());
                log::trace!("Instance status {:?}", instance.status);
                Ok(instance_uuid)
            }
            _ => Err(FError::TransitionNotAllowed),
        }
    }

    async fn start_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        log::debug!("Start FDU {:?}", instance_uuid);
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut instance = self
            .connector
            .global
            .get_node_instance(node_uuid, instance_uuid)
            .await?;
        log::trace!("Instance status {:?}", instance.status);
        match instance.status {
            FDUState::CONFIGURED => {
                let mut guard = self.fdus.write().await;
                instance.status = FDUState::RUNNING;
                self.connector
                    .global
                    .add_node_instance(node_uuid, instance.clone())
                    .await?;
                guard.fdus.insert(instance_uuid, instance.clone());
                log::trace!("Instance status {:?}", instance.status);
                Ok(instance_uuid)
            }
            _ => Err(FError::TransitionNotAllowed),
        }
    }

    async fn run_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn log_fdu(&mut self, instance_uuid: Uuid) -> FResult<String> {
        Err(FError::Unimplemented)
    }
    async fn ls_fdu(&mut self, instance_uuid: Uuid) -> FResult<Vec<String>> {
        Err(FError::Unimplemented)
    }

    async fn file_fdu(&mut self, instance_uuid: Uuid, file_name: String) -> FResult<String> {
        Err(FError::Unimplemented)
    }

    async fn stop_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        log::debug!("Stop instance {:?}", instance_uuid);
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut instance = self
            .connector
            .global
            .get_node_instance(node_uuid, instance_uuid)
            .await?;
        log::trace!("Instance status {:?}", instance.status);
        match instance.status {
            FDUState::RUNNING => {
                let mut guard = self.fdus.write().await;
                instance.status = FDUState::CONFIGURED;
                self.connector
                    .global
                    .add_node_instance(node_uuid, instance.clone())
                    .await?;
                guard.fdus.insert(instance_uuid, instance.clone());
                log::trace!("Instance status {:?}", instance.status);
                Ok(instance_uuid)
            }
            _ => Err(FError::TransitionNotAllowed),
        }
    }

    async fn migrate_fdu(&mut self, instance_uuid: Uuid, destination_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn get_fdu_status(&self, instance_uuid: Uuid) -> FResult<FDURecord> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        self.connector
            .global
            .get_node_instance(node_uuid, instance_uuid)
            .await
    }
}

impl DummyHypervisor {
    async fn run(&self, stop: async_std::sync::Receiver<()>) {
        info!("DummyHypervisor main loop starting...");

        //starting the Agent-Plugin Server
        let hv_server = self.clone().get_hypervisor_plugin_server(self.z.clone());
        hv_server.connect();
        hv_server.initialize();

        let mut guard = self.fdus.write().await;
        guard.uuid = Some(hv_server.instance_uuid());
        drop(guard);

        self.agent
            .clone()
            .unwrap()
            .register_plugin(
                self.fdus.read().await.uuid.unwrap(),
                PluginKind::HYPERVISOR(String::from("dummy")),
            )
            .await
            .unwrap()
            .unwrap();

        hv_server.register();

        let (shv, hhv) = hv_server.start();

        let monitoring = async {
            loop {
                info!("Monitoring loop started");
                task::sleep(Duration::from_secs(60)).await;
            }
        };

        match monitoring.race(stop.recv()).await {
            Ok(_) => trace!("Monitoring ending correct"),
            Err(e) => trace!("Monitoring ending got error: {}", e),
        }

        self.agent
            .clone()
            .unwrap()
            .unregister_plugin(self.fdus.read().await.uuid.unwrap())
            .await
            .unwrap()
            .unwrap();

        hv_server.stop(shv);
        hv_server.unregister();
        hv_server.disconnect();

        info!("DummyHypervisor main loop exiting")
    }

    pub async fn start(
        &mut self,
    ) -> (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {
        let local_os = OSClient::find_local_servers(self.z.clone()).await.unwrap();
        if local_os.is_empty() {
            error!("Unable to find a local OS interface");
            panic!("No OS Server");
        }

        let local_agent = AgentPluginInterfaceClient::find_local_servers(self.z.clone())
            .await
            .unwrap();
        if local_agent.is_empty() {
            error!("Unable to find a local Agent interface");
            panic!("No Agent Server");
        }

        let local_net = NetworkingPluginClient::find_local_servers(self.z.clone())
            .await
            .unwrap();
        if local_net.is_empty() {
            error!("Unable to find a local Network plugin interface");
            panic!("No Network Server");
        }

        let os = OSClient::new(self.z.clone(), local_os[0]);
        let agent = AgentPluginInterfaceClient::new(self.z.clone(), local_agent[0]);
        let net = NetworkingPluginClient::new(self.z.clone(), local_net[0]);

        self.agent = Some(agent);
        self.os = Some(os);
        self.net = Some(net);

        // Starting main loop in a task
        let (s, r) = async_std::sync::channel::<()>(1);
        let plugin = self.clone();
        let h = async_std::task::spawn(async move {
            plugin.run(r).await;
        });
        (s, h)
    }

    pub async fn stop(&self, stop: async_std::sync::Sender<()>) {
        stop.send(()).await;
    }
}

#[async_std::main]
async fn main() {
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    let args = DummyArgs::from_args();
    info!("Dummy Hypervisor Plugin -- bootstrap");
    let my_pid = process::id();
    info!("PID is {}", my_pid);

    let properties = format!("mode=client;peer={}", args.zenoh.clone());
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let mut dummy = DummyHypervisor {
        z: zenoh.clone(),
        connector: zconnector.clone(),
        pid: my_pid,
        agent: None,
        os: None,
        net: None,
        fdus: Arc::new(RwLock::new(DummyHVState {
            uuid: None,
            fdus: HashMap::new(),
        })),
    };

    let (s, h) = dummy.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);
    stream.next().await;
    trace!("Received Ctrl-C start teardown");

    //Here we send the stop signal to the agent object and waits that it ends
    dummy.stop(s).await;

    //wait for the futures to ends
    h.await;

    //zconnector.close();
    //zenoh.close();

    info!("Bye!")
}
