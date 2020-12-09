/*********************************************************************************
* Copyright (c) 2018,2020 ADLINK Technology Inc.
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
* which is available at https://www.apache.org/licenses/LICENSE-2.0.
*
* SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
* Contributors:
*   ADLINK fog05 team, <fog05@adlink-labs.tech>
*********************************************************************************/
#![allow(unused)]
#![allow(unused_variables)]
#![allow(unused_mut)]

use std::collections::HashMap;
use std::fs::File;
use std::process::{Command, Stdio};
use std::time::Duration;

use async_std::prelude::*;
use async_std::sync::{Arc, Mutex};
use async_std::task;

use nix::sys::signal::{kill, Signal};
use nix::unistd::Pid;

use zrpc::ZServe;
use zrpc_macros::zserver;

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::im::fdu::*;
use fog05_sdk::im::fdu::{FDUDescriptor, FDURecord, FDUState};
use fog05_sdk::plugins::{HypervisorPlugin, NetworkingPluginClient};
use fog05_sdk::types::PluginKind;

use uuid::Uuid;

use crate::types::{
    deserialize_native_specific_descriptor, deserialize_native_specific_info,
    serialize_native_specific_info, NativeHVSpecificInfo, NativeHypervisor,
};

#[zserver]
impl HypervisorPlugin for NativeHypervisor {
    async fn define_fdu(&mut self, fdu: FDUDescriptor) -> FResult<FDURecord> {
        log::debug!("Define FDU {:?}", fdu);

        if fdu.hypervisor_specific.is_none() {
            return Err(FError::MalformedDescriptor);
        }

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
            .add_node_instance(node_uuid, &instance)
            .await?;
        log::debug!("Instance status {:?}", instance.status);
        Ok(instance)
    }

    async fn undefine_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid> {
        log::debug!("Undefine FDU {:?}", instance_uuid);
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
                log::debug!("Instance status {} undefined", instance_uuid);
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

                let hv_info = deserialize_native_specific_descriptor(
                    &descriptor
                        .hypervisor_specific
                        .unwrap()
                        .into_bytes()
                        .as_slice(),
                )?;

                // Creating network namespace only if isolation feature is enabled
                let fdu_ns: Option<Uuid> = if cfg!(feature = "isolation") {
                    let ns = self
                        .net
                        .as_ref()
                        .unwrap()
                        .create_network_namespace()
                        .await??;
                    Some(ns.uuid)
                } else {
                    None
                };

                let instance_path = self
                    .get_run_path()
                    .join(format!("{}", instance_uuid))
                    .to_str()
                    .ok_or(FError::EncodingError)?
                    .to_string();
                let hv_specific = NativeHVSpecificInfo {
                    pid: 0,
                    env: hv_info.env.clone(),
                    // the base path need to be configurable from a configuration file
                    instance_path,
                    instance_files: Vec::new(),
                    netns: fdu_ns,
                };

                //creating instance path
                let descriptor = self
                    .os
                    .as_ref()
                    .unwrap()
                    .create_dir(hv_specific.clone().instance_path)
                    .await??;

                // Adding hv specific info
                instance.hypervisor_specific = Some(serialize_native_specific_info(&hv_specific)?);
                //

                log::trace!("Created instance info {:?}", hv_specific);

                let mut interfaces: Vec<FDURecordInterface> = Vec::new();

                // This is to be sure the ns-manager is already up on the networking
                //TODO the zrpc should check with a timeout if the service is up,
                // and return error only if it is not present
                task::sleep(Duration::from_millis(1000)).await;

                let mut cps: HashMap<String, FDURecordConnectionPoint> = HashMap::new();

                //Creating just an interface to be attached to the default vnet

                if cfg!(feature = "isolation") {
                    let viface_config = fog05_sdk::types::VirtualInterfaceConfig {
                        if_name: "eth0".to_string(),
                        kind: fog05_sdk::types::VirtualInterfaceConfigKind::VETH,
                    };
                    let viface = self
                        .net
                        .as_ref()
                        .unwrap()
                        .create_virtual_interface_in_namespace(viface_config, fdu_ns.unwrap())
                        .await??;

                    log::trace!("Created virtual interface {:?}", viface);

                    let pair = match viface.kind {
                        fog05_sdk::types::VirtualInterfaceKind::VETH(info) => info.pair,
                        _ => return Err(FError::MalformedDescriptor),
                    };

                    // Moving pair interface into default network namespace
                    self.net
                        .as_ref()
                        .unwrap()
                        .move_interface_into_default_namespace(pair)
                        .await??;

                    // Attaching interface to default network virtual bridge
                    self.net
                        .as_ref()
                        .unwrap()
                        .attach_interface_to_bridge(pair, Uuid::nil())
                        .await??;

                    // Getting address with DHCP
                    self.net
                        .as_ref()
                        .unwrap()
                        .assing_address_to_interface(viface.uuid, None)
                        .await??;

                    let fdu_intf = FDURecordInterface {
                        name: "eth0".to_string(),
                        kind: fog05_sdk::im::fdu::InterfaceKind::VIRTUAL,
                        mac_address: None,
                        cp_uuid: None,
                        intf_uuid: viface.uuid,
                        virtual_interface: FDURecordVirtualInterface {
                            vif_kind: VirtualInterfaceKind::E1000,
                            bandwidht: None,
                        },
                    };
                    interfaces.push(fdu_intf)
                }
                // Not creating any connection point or interface
                // for cp in descriptor.connection_points {
                //     let vcp = self
                //         .net
                //         .as_ref()
                //         .unwrap()
                //         .create_connection_point()
                //         .await??;

                //     let fdu_cp = FDURecordConnectionPoint {
                //         uuid: vcp.uuid,
                //         id: cp.id.clone(),
                //     };

                //     log::trace!("Created connection point {:?} {:?}", vcp, fdu_cp);

                //     cps.insert(cp.id, fdu_cp);
                //     // we should ask the connection of the cp to the virtual network here
                // }

                // for intf in descriptor.interfaces {
                //     let viface_config = fog05_sdk::types::VirtualInterfaceConfig {
                //         if_name: intf.name.clone(),
                //         kind: fog05_sdk::types::VirtualInterfaceConfigKind::VETH,
                //     };
                //     let viface = self
                //         .net
                //         .as_ref()
                //         .unwrap()
                //         .create_virtual_interface_in_namespace(viface_config, fdu_ns.uuid)
                //         .await??;

                //     log::trace!("Created virtual interface {:?}", viface);

                //     let pair = match viface.kind {
                //         fog05_sdk::types::VirtualInterfaceKind::VETH(info) => info.pair,
                //         _ => return Err(FError::MalformedDescriptor),
                //     };
                //     let cp_uuid = match intf.cp_id {
                //         Some(cp_id) => {
                //             let cp = cps.get(&cp_id).ok_or(FError::NotFound)?;
                //             self.net
                //                 .as_ref()
                //                 .unwrap()
                //                 .bind_interface_to_connection_point(pair, cp.uuid)
                //                 .await??;
                //             Some(cp.uuid)
                //         }
                //         None => {
                //             self.net
                //                 .as_ref()
                //                 .unwrap()
                //                 .move_interface_into_default_namespace(pair)
                //                 .await??;
                //             None
                //         }
                //     };

                //     // dummy hv creates all the faces as veth pairs
                //     let fdu_intf = FDURecordInterface {
                //         name: intf.name,
                //         kind: intf.kind,
                //         mac_address: intf.mac_address,
                //         cp_uuid,
                //         intf_uuid: viface.uuid,
                //         virtual_interface: FDURecordVirtualInterface {
                //             vif_kind: VirtualInterfaceKind::E1000,
                //             bandwidht: None,
                //         },
                //     };
                //     interfaces.push(fdu_intf)
                // }

                instance.interfaces = interfaces;
                instance.connection_points = cps.into_iter().map(|(_, v)| v).collect();
                instance.status = FDUState::CONFIGURED;
                self.connector
                    .global
                    .add_node_instance(node_uuid, &instance)
                    .await?;
                log::debug!("Instance status {:?}", instance.status);
                guard.fdus.insert(instance_uuid, instance);
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

                let mut hv_specific = deserialize_native_specific_info(
                    &instance.clone().hypervisor_specific.unwrap().as_slice(),
                )?;

                for iface in instance.interfaces {
                    self.net
                        .as_ref()
                        .unwrap()
                        .delete_virtual_interface(iface.intf_uuid)
                        .await??;
                    log::trace!("Deleted virtual interface {:?}", iface);
                }

                self.net
                    .as_ref()
                    .unwrap()
                    .delete_network_namespace(hv_specific.netns.unwrap())
                    .await??;

                // for cp in instance.connection_points {
                //     self.net
                //         .as_ref()
                //         .unwrap()
                //         .delete_connection_point(cp.uuid)
                //         .await??;
                //     log::trace!("Deletted connection point {:?}", cp);
                // }

                // removing all instance files
                for filename in hv_specific.clone().instance_files {
                    match std::fs::remove_file(filename.clone()) {
                        Ok(_) => log::trace!("Removed {}", filename),
                        Err(e) => log::warn!("file {} {}", filename, e),
                    }
                }

                //removing instance directory
                let descriptor = self
                    .os
                    .as_ref()
                    .unwrap()
                    .rm_dir(hv_specific.clone().instance_path)
                    .await??;

                hv_specific.instance_files = Vec::new();
                hv_specific.env = HashMap::new();

                instance.hypervisor_specific = Some(serialize_native_specific_info(&hv_specific)?);
                instance.interfaces = Vec::new();
                instance.connection_points = Vec::new();
                instance.status = FDUState::DEFINED;
                self.connector
                    .global
                    .add_node_instance(node_uuid, &instance)
                    .await?;
                log::debug!("Instance status {:?}", instance.status);
                guard.fdus.insert(instance_uuid, instance);

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

                let descriptor = self
                    .agent
                    .as_ref()
                    .unwrap()
                    .fdu_info(instance.fdu_uuid)
                    .await??;

                let hv_info = deserialize_native_specific_descriptor(
                    &descriptor.hypervisor_specific.unwrap().into_bytes(),
                )?;

                let mut hv_specific = deserialize_native_specific_info(
                    &instance.clone().hypervisor_specific.unwrap().as_slice(),
                )?;

                let mut cmd = if cfg!(feature = "isolation") {
                    let ns = self
                        .net
                        .as_ref()
                        .unwrap()
                        .get_network_namespace(hv_specific.netns.unwrap())
                        .await??;

                    let mut cmd = Command::new("native-isolate");
                    cmd.arg(ns.ns_name);
                    cmd.arg(hv_info.cmd);
                    for arg in hv_info.args {
                        cmd.arg(arg);
                    }
                    cmd
                } else {
                    let mut cmd = Command::new(hv_info.cmd);
                    for arg in hv_info.args {
                        cmd.arg(arg);
                    }
                    cmd
                };

                cmd.envs(hv_specific.env.clone());

                // rearranging stdin,stdout, stderr
                cmd.stdin(Stdio::null());

                // creating file for stdout and stderr
                let out_filename = format!("{}/{}.out", hv_specific.instance_path, instance_uuid);
                let err_filename = format!("{}/{}.out", hv_specific.instance_path, instance_uuid);

                hv_specific.instance_files.push(out_filename.clone());
                hv_specific.instance_files.push(err_filename.clone());

                let out = File::create(out_filename)?;
                let err = File::create(err_filename)?;

                cmd.stdout(Stdio::from(out));
                cmd.stderr(Stdio::from(err));

                log::trace!("Native CMD is : {:?}", cmd);
                let child = cmd.spawn()?;
                log::debug!("Child PID {}", child.id());

                hv_specific.pid = child.id();

                instance.hypervisor_specific = Some(serialize_native_specific_info(&hv_specific)?);

                instance.status = FDUState::RUNNING;
                self.connector
                    .global
                    .add_node_instance(node_uuid, &instance)
                    .await?;
                guard
                    .childs
                    .insert(instance_uuid, Arc::new(Mutex::new(child)));
                log::debug!("Instance status {:?}", instance.status);
                guard.fdus.insert(instance_uuid, instance);
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

                let mut hv_specific = deserialize_native_specific_info(
                    &instance.clone().hypervisor_specific.unwrap(),
                )?;

                let c = guard
                    .childs
                    .remove(&instance_uuid)
                    .ok_or(FError::NotFound)?;
                let mut child = c.lock().await;
                log::trace!("Child PID {:?}", child.id());
                if cfg!(feature = "isolation") {
                    log::trace!(
                        "Isolation is active sending kill with sudo to PID {:?}",
                        child.id()
                    );
                    let pid = child.id();
                    kill(Pid::from_raw(pid as i32), Signal::SIGINT)
                        .map_err(|e| FError::HypervisorError(format!("{}", e)))?;
                    log::trace!("Waiting child to exit...");
                    child.wait()?;
                } else {
                    child.kill()?;
                }

                hv_specific.pid = 0;

                instance.hypervisor_specific = Some(serialize_native_specific_info(&hv_specific)?);

                self.connector
                    .global
                    .add_node_instance(node_uuid, &instance)
                    .await?;

                log::trace!("Instance status {:?}", instance.status);
                guard.fdus.insert(instance_uuid, instance);

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

impl NativeHypervisor {
    async fn run(&self, stop: async_std::sync::Receiver<()>) -> FResult<()> {
        log::info!("NativeHypervisor main loop starting...");

        //starting the Agent-Plugin Server
        let hv_server = self
            .clone()
            .get_hypervisor_plugin_server(self.z.clone(), None);
        hv_server.connect().await?;
        hv_server.initialize().await?;

        let mut guard = self.fdus.write().await;
        guard.uuid = Some(hv_server.instance_uuid());
        drop(guard);

        self.agent
            .clone()
            .unwrap()
            .register_plugin(
                self.fdus.read().await.uuid.unwrap(),
                PluginKind::HYPERVISOR(String::from("bare")),
            )
            .await??;

        hv_server.register().await?;

        let (shv, hhv) = hv_server.start().await?;

        let monitoring = async {
            loop {
                log::info!("Monitoring loop started");
                task::sleep(Duration::from_secs(60)).await;
            }
        };

        match monitoring.race(stop.recv()).await {
            Ok(_) => log::trace!("Monitoring ending correct"),
            Err(e) => log::trace!("Monitoring ending got error: {}", e),
        }

        self.agent
            .clone()
            .unwrap()
            .unregister_plugin(self.fdus.read().await.uuid.unwrap())
            .await??;

        hv_server.stop(shv).await?;
        hv_server.unregister().await?;
        hv_server.disconnect().await?;

        log::info!("DummyHypervisor main loop exiting");
        Ok(())
    }

    pub async fn start(
        &mut self,
    ) -> (
        async_std::sync::Sender<()>,
        async_std::task::JoinHandle<FResult<()>>,
    ) {
        let local_os = OSClient::find_local_servers(self.z.clone()).await.unwrap();
        if local_os.is_empty() {
            log::error!("Unable to find a local OS interface");
            panic!("No OS Server");
        }

        let local_agent = AgentPluginInterfaceClient::find_local_servers(self.z.clone())
            .await
            .unwrap();
        if local_agent.is_empty() {
            log::error!("Unable to find a local Agent interface");
            panic!("No Agent Server");
        }

        let local_net = NetworkingPluginClient::find_local_servers(self.z.clone())
            .await
            .unwrap();
        if local_net.is_empty() {
            log::error!("Unable to find a local Network plugin interface");
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
        let h = async_std::task::spawn_blocking(move || {
            async_std::task::block_on(async { plugin.run(r).await })
        });
        (s, h)
    }

    pub async fn stop(&self, stop: async_std::sync::Sender<()>) {
        stop.send(()).await;
    }

    fn get_path(&self) -> Box<std::path::Path> {
        self.config.path.clone()
    }

    fn get_run_path(&self) -> Box<std::path::Path> {
        self.config.run_path.clone()
    }
}
