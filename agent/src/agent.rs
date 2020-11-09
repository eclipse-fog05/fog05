#![allow(unused_variables)]

extern crate machine_uid;
extern crate serde;
extern crate serde_json;
extern crate serde_yaml;
extern crate pnet_datalink;

use std::collections::HashMap;
use std::convert::TryInto;
use std::str;
use std::str::FromStr;
use std::time::Duration;

use async_std::fs;
use async_std::path::Path;
use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};
use async_std::task;

use async_std::io::ReadExt;

use log::{error, info, trace};

use zrpc::ZServe;
use zrpc_macros::zserver;

use fog05_sdk::agent::{AgentOrchestratorInterface, AgentPluginInterface, OS};
use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::im;
use fog05_sdk::plugins::{HypervisorPluginClient, NetworkingPluginClient};
use fog05_sdk::types;
use fog05_sdk::types::{IPAddress, InterfaceKind};

use uuid::Uuid;

use sysinfo::{DiskExt, ProcessorExt, SystemExt, NetworksExt, NetworkExt};

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AgentConfig {
    pub system: Uuid,
    pub pid_file: Box<std::path::Path>,
    pub zlocator: String,
    pub path: Box<std::path::Path>,
    pub mgmt_interface: String,
    pub monitoring_interveal: u64,
}

//should be AgentInner that contains the state
// and agent that is an Arc<RwLock<AgentInner>>
#[derive(Clone)]
pub struct AgentInner {
    pub pid: u32,
    pub networking: Option<NetworkingPluginClient>,
    pub hypervisors: HashMap<String, HypervisorPluginClient>,
    pub config: AgentConfig,
}

#[derive(Clone)]
pub struct Agent {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub node_uuid: Uuid,
    pub agent: Arc<RwLock<AgentInner>>,
}

impl Agent {
    async fn run(&self, stop: async_std::sync::Receiver<()>) {
        info!("Agent main loop starting...");
        //this should return a channel to send the stop and a task handler to wait for

        //starting the Agent-Plugin Server
        let a2p_server = self
            .clone()
            .get_agent_plugin_interface_server(self.z.clone());
        a2p_server.connect();
        a2p_server.initialize();
        a2p_server.register();

        //starting the OS Server
        let os_server = self.clone().get_os_server(self.z.clone());
        os_server.connect();
        os_server.initialize();
        os_server.register();

        let (sa2p, ha2p) = a2p_server.start();

        let (sos, hos) = os_server.start();

        let monitoring = async {
            let guard = self.agent.read().await;
            info!(
                "Monitoring loop started with interveal {}",
                guard.config.monitoring_interveal
            );
            drop(guard);
            let mut system = sysinfo::System::new_all();
            loop {
                let guard = self.agent.read().await;
                let interveal = guard.config.monitoring_interveal;
                trace!("Monitoring loop, with interveal {}", interveal);
                let mut disks = Vec::<im::node::DiskStatus>::new();
                let mut ifaces = Vec::<im::node::NetworkInterfaceStatus>::new();

                system.refresh_all();
                let mem = im::node::RAMStatus {
                    total: (system.get_total_memory() as f64) / 1024.0,
                    free: (system.get_free_memory() as f64) / 1024.0,
                };
                for disk in system.get_disks() {
                    let disk_status = im::node::DiskStatus {
                        mount_point: String::from(disk.get_mount_point().to_str().unwrap()),
                        total: (disk.get_total_space() as f64) / 1024.0 / 1024.0,
                        free: (disk.get_available_space() as f64) / 1024.0 / 1024.0,
                    };
                    disks.push(disk_status);
                }

                for iface in pnet::datalink::interfaces() {


                    // TODO: psutil-rust is not yet implementing net_if_stats for Linux, macOS and Windows...
                    //let ps_ifaces = psutil::network::net_if_stats().unwrap();
                    //let ps_iface = ps_ifaces.get(&iface.name).ok_or(FError::NotFound).unwrap();
                    let (_, sys_iface) = system.get_networks().iter().find(|(name,_)| **name == iface.name ).ok_or(FError::NotFound).unwrap();
                    let face = im::node::NetworkInterfaceStatus {
                        name : iface.name,
                        index : iface.index,
                        mac : iface.mac,
                        ips : iface.ips,
                        flags : iface.flags,
                        is_up : true,  //ps_iface.is_up(), //Filling because psutil-rust is not yet working
                        mtu : 1500,    //ps_iface.mtu(),
                        speed : 100,   //ps_iface.speed(),
                        sent_pkts : sys_iface.get_total_packets_transmitted(),
                        recv_pkts : sys_iface.get_total_packets_received(),
                        sent_bytes : sys_iface.get_total_transmitted(),
                        recv_bytes : sys_iface.get_total_received(),
                    };

                    ifaces.push(face);
                }

                let hvs: Vec<String> = guard.hypervisors.keys().map(|x| (*x).clone()).collect();
                let status = match guard.networking {
                    Some(_) => match hvs.len() {
                        0 => im::node::NodeStatusEnum::NOTREADY,
                        _ => im::node::NodeStatusEnum::READY,
                    },
                    None => im::node::NodeStatusEnum::NOTREADY,
                };
                let node_status = im::node::NodeStatus {
                    uuid: self.node_uuid,
                    status,
                    ram: mem,
                    disk: disks,
                    supported_hypervisors: hvs,
                    interfaces : ifaces,
                    neighbors: Vec::new(), //not yet...
                };

                self.connector
                    .global
                    .add_node_status(node_status)
                    .await
                    .unwrap();
                drop(guard);
                task::sleep(Duration::from_secs(interveal)).await;
            }
        };
        match monitoring.race(stop.recv()).await {
            Ok(_) => trace!("Monitoring ending correct"),
            Err(e) => trace!("Monitoring ending got error: {}", e),
        }

        a2p_server.stop(sa2p);
        a2p_server.unregister();
        a2p_server.disconnect();

        os_server.stop(sos);
        os_server.unregister();
        os_server.disconnect();

        info!("Agent main loop exiting...");
    }

    pub async fn start(&self) -> (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {
        let mut processors = Vec::<im::node::CPUSpec>::new();
        let mut disks = Vec::<im::node::DiskSpec>::new();
        let mut ifaces = Vec::<im::node::NetworkInterface>::new();
        //let disks = Vec::new();

        //When starting we first get all node informations
        let mut system = sysinfo::System::new_all();
        //let arch = heim::host::platform().await.unwrap().architecture().as_str();
        let arch = std::env::consts::ARCH.to_string();

        //refresh information
        system.refresh_all();

        for processor in system.get_processors() {
            let cpu_spec = im::node::CPUSpec {
                model: processor
                    .get_vendor_id()
                    .trim_end_matches('\u{0}')
                    .to_string(),
                frequency: processor.get_frequency(),
                arch: arch.clone(),
            };

            processors.push(cpu_spec);
        }

        let mem = im::node::RAMSpec {
            size: (system.get_total_memory() as f64) / 1024.0,
        };
        let os = String::from(std::env::consts::OS);
        let name = String::from(hostname::get().unwrap().to_str().unwrap());

        for disk in system.get_disks() {
            let disk_spec = im::node::DiskSpec {
                local_address: String::from(disk.get_name().to_os_string().to_str().unwrap()),
                dimension: (disk.get_total_space() as f64) / 1024.0 / 1024.0,
                mount_point: String::from(disk.get_mount_point().to_str().unwrap()),
                file_system: String::from(std::str::from_utf8(disk.get_file_system()).unwrap()),
            };

            disks.push(disk_spec);
        }

        for iface in pnet::datalink::interfaces() {
            let face = im::node::NetworkInterface {
                name : iface.name,
                index : iface.index,
                mac : iface.mac,
                ips : iface.ips,
                flags : iface.flags,
            };

            ifaces.push(face);
        }

        let ni = im::node::NodeInfo {
            uuid: self.node_uuid,
            name,
            os,
            cpu: processors,
            ram: mem,
            disks,
            interfaces : ifaces,
            io: Vec::new(),
            accelerators: Vec::new(),
            position: None,
        };

        trace!("Node Info: {:?}", ni);

        self.connector.global.add_node_info(ni).await.unwrap();

        // Starting main loop in a task
        let (s, r) = async_std::sync::channel::<()>(1);
        let agent = self.clone();
        let h = async_std::task::spawn(async move {
            agent.run(r).await;
        });
        (s, h)
    }

    pub async fn stop(&self, stop: async_std::sync::Sender<()>) {
        stop.send(()).await;
        self.connector
            .global
            .remove_node_status(self.node_uuid)
            .await
            .unwrap();
        self.connector
            .global
            .remove_node_info(self.node_uuid)
            .await
            .unwrap();
    }
}

#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl AgentPluginInterface for Agent {
    async fn fdu_info(&self, fdu_uuid: Uuid) -> FResult<im::fdu::FDUDescriptor> {
        trace!("Called fdu_info with {:?}", fdu_uuid);
        Err(FError::Unimplemented)
    }
    async fn image_info(&self, image_uuid: Uuid) -> FResult<im::fdu::Image> {
        Err(FError::Unimplemented)
    }
    async fn node_fdu_info(
        &self,
        fdu_uuid: Uuid,
        node_uuid: Uuid,
        instance_uuid: Uuid,
    ) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }
    async fn network_info(&self, network_uuid: Uuid) -> FResult<types::VirtualNetwork> {
        Err(FError::Unimplemented)
    }
    async fn connection_point_info(&self, cp_uuid: Uuid) -> FResult<types::ConnectionPoint> {
        Err(FError::Unimplemented)
    }
    async fn node_management_address(&self, node_uuid: Uuid) -> FResult<IPAddress> {
        Err(FError::Unimplemented)
    }

    async fn create_virtual_network(
        &self,
        vnet: types::VirtualNetworkConfig,
    ) -> FResult<types::VirtualNetwork> {
        Err(FError::Unimplemented)
    }
    async fn remove_virtual_network(&self, vnet_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn create_connection_point(
        &self,
        cp: types::ConnectionPointConfig,
    ) -> FResult<types::ConnectionPoint> {
        Err(FError::Unimplemented)
    }
    async fn remove_connection_point(&self, cp_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn bind_cp_to_fdu_face(
        &self,
        cp_uuid: Uuid,
        instance_uuid: Uuid,
        interface: String,
    ) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }
    async fn unbind_co_from_fdu_face(
        &self,
        cp_uuid: Uuid,
        instance_uuid: Uuid,
        interface: String,
    ) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn bind_cp_to_network(&self, cp_uuid: Uuid, vnet_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }
    async fn unbind_cp_from_network(&self, cp_uuid: Uuid, vnet_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn get_node_uuid(&self) -> FResult<Uuid> {
        Ok(self.node_uuid)
    }

    async fn register_plugin(
        &mut self,
        plugin_uuid: Uuid,
        kind: types::PluginKind,
    ) -> FResult<Uuid> {
        trace!("register_plugin called with {} {}", plugin_uuid, kind);
        let mut guard = self.agent.write().await;
        trace!("register_plugin took WriteLock!");
        match kind.clone() {
            types::PluginKind::HYPERVISOR(hv) => match guard.hypervisors.get(&hv) {
                Some(_) => Err(FError::AlreadyPresent),
                None => {
                    trace!("Adding Hypervisor plugin {} {}", plugin_uuid, hv);
                    let hv_client = HypervisorPluginClient::new(self.z.clone(), plugin_uuid);
                    guard.hypervisors.insert(hv.clone(), hv_client);
                    trace!("Added Hypervisor plugin {} {}", plugin_uuid, hv);
                    let pl_info = types::PluginInfo {
                        uuid: plugin_uuid,
                        kind: kind.clone(),
                        name: format!("{}Plugin", kind),
                    };
                    self.connector
                        .global
                        .add_plugin(self.node_uuid, pl_info)
                        .await?;
                    Ok(plugin_uuid)
                }
            },
            types::PluginKind::NETWORKING => match guard.networking {
                Some(_) => Err(FError::AlreadyPresent),
                None => {
                    let nw_client = NetworkingPluginClient::new(self.z.clone(), plugin_uuid);
                    guard.networking = Some(nw_client);
                    let pl_info = types::PluginInfo {
                        uuid: plugin_uuid,
                        kind: kind.clone(),
                        name: format!("{}Plugin", kind),
                    };
                    self.connector
                        .global
                        .add_plugin(self.node_uuid, pl_info)
                        .await?;
                    Ok(plugin_uuid)
                }
            },
            _ => Err(FError::UnknownError("Not yet...".to_string())),
        }
    }

    async fn unregister_plugin(&mut self, plugin_uuid: Uuid) -> FResult<Uuid> {
        trace!("unregister_plugin called with {}", plugin_uuid);
        let mut guard = self.agent.write().await;
        trace!("register_plugin took WriteLock!");
        let pl_info = self
            .connector
            .global
            .get_plugin(self.node_uuid, plugin_uuid)
            .await?;
        match pl_info.kind {
            types::PluginKind::HYPERVISOR(hv) => {
                guard.hypervisors.remove(&hv);
                self.connector
                    .global
                    .remove_plugin(self.node_uuid, plugin_uuid)
                    .await?;
                Ok(plugin_uuid)
            }
            types::PluginKind::NETWORKING => {
                guard.networking = None;
                self.connector
                    .global
                    .remove_plugin(self.node_uuid, plugin_uuid)
                    .await?;
                Ok(plugin_uuid)
            }
            _ => Err(FError::Unimplemented),
        }
    }
}

#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl OS for Agent {
    async fn dir_exists(&self, dir_path: String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        if !path.exists().await {
            return Ok(false);
        }
        let file_type = fs::metadata(path).await?.file_type();
        if file_type.is_dir() {
            return Ok(true);
        }
        Ok(false)
    }
    async fn create_dir(&self, dir_path: String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        fs::create_dir(path).await?;
        Ok(true)
    }
    async fn rm_dir(&self, dir_path: String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        fs::remove_dir(path).await?;
        Ok(true)
    }

    async fn download_file(&self, url: url::Url, dest_path: String) -> FResult<bool> {
        task::spawn(async move {
            trace!("Start downloading: {}", url);
            match reqwest::blocking::get(url.clone()) {
                Err(err) => error!("Error in getting {} error: {}", url, err),
                Ok(resp) => {
                    let out = fs::File::create(dest_path.clone()).await;
                    match out {
                        Err(err) => error!(
                            "Unable to create destination file {} for {} error: {}",
                            dest_path, url, err
                        ),
                        Ok(mut f) => {
                            let bytes = resp.bytes().unwrap();
                            let mut slice: &[u8] = bytes.as_ref();
                            match async_std::io::copy(&mut slice, &mut f).await {
                                Ok(_) => trace!("Done downloading: {} info {}", url, dest_path),
                                Err(err) => error!("Unable to copy content: {}", err),
                            }
                        }
                    }
                }
            }
        });
        Ok(true)
    }

    async fn create_file(&self, file_path: String) -> FResult<bool> {
        let path = Path::new(&file_path);
        if !path.exists().await {
            let file = fs::File::create(path).await?;
            file.sync_all().await?;
            return Ok(true);
        }
        Ok(false)
    }

    async fn rm_file(&self, file_path: String) -> FResult<bool> {
        let path = Path::new(&file_path);
        fs::remove_file(path).await?;
        Ok(true)
    }

    async fn store_file(&self, content: Vec<u8>, file_path: String) -> FResult<bool> {
        Ok(true)
    }

    async fn read_file(&self, file_path: String) -> FResult<Vec<u8>> {
        let path = Path::new(&file_path);
        let mut file = fs::File::open(path).await?;
        let mut content: Vec<u8> = Vec::new();
        file.read_to_end(&mut content).await?;
        Ok(content)
    }
    async fn file_exists(&self, file_path: String) -> FResult<bool> {
        let path = Path::new(&file_path);
        if !path.exists().await {
            return Ok(false);
        }
        let file_type = fs::metadata(path).await?.file_type();
        if file_type.is_file() {
            return Ok(true);
        }
        Ok(false)
    }

    async fn execute_command(&self, cmd: String) -> FResult<String> {
        Err(FError::Unimplemented)
    }

    async fn send_signal(&self, signal: u8, pid: u32) -> FResult<bool> {
        let mut system = sysinfo::System::new_all();
        system.refresh_all();
        let process = system.get_process(pid.try_into()?);
        match process {
            Some(p) => {
                Err(FError::UnknownError("Not yet...".to_string()))
                //Ok(p.kill(signal))
            }
            None => Err(FError::NotFound),
        }
    }

    async fn check_if_pid_exists(&self, pid: u32) -> FResult<bool> {
        let mut system = sysinfo::System::new_all();
        system.refresh_all();
        let process = system.get_process(pid.try_into()?);
        match process {
            Some(_) => Ok(true),
            None => Ok(false),
        }
    }

    async fn get_interface_type(&self, iface: String) -> FResult<InterfaceKind> {
        Err(FError::Unimplemented)
    }

    async fn set_interface_unavailable(&self, iface: String) -> FResult<bool> {
        Err(FError::Unimplemented)
    }

    async fn set_interface_available(&self, iface: String) -> FResult<bool> {
        Err(FError::Unimplemented)
    }

    async fn get_local_mgmt_address(&self) -> FResult<IPAddress> {
        Err(FError::Unimplemented)
    }
}

#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl AgentOrchestratorInterface for Agent {
    async fn check_fdu_compatibility(&self, fdu_uuid: Uuid) -> FResult<bool> {
        let descriptor = self.connector.global.get_fdu(fdu_uuid).await?;
        let node_info = self.connector.global.get_node_info(self.node_uuid).await?;
        let node_status = self
            .connector
            .global
            .get_node_status(self.node_uuid)
            .await?;

        let has_plugin = self
            .agent
            .read()
            .await
            .hypervisors
            .get(&descriptor.hypervisor)
            .is_some();
        let cpu_arch = node_info.cpu[0].arch == descriptor.computation_requirements.cpu_arch;
        let cpu_number =
            (node_info.cpu.len() as u8) == descriptor.computation_requirements.cpu_min_count;
        let cpu_freq =
            node_info.cpu[0].frequency >= descriptor.computation_requirements.cpu_min_freq;
        let ram_size =
            node_status.ram.free >= (descriptor.computation_requirements.ram_size_mb as f64);
        let disk_size = (node_status
            .disk
            .iter()
            .find(|x| x.mount_point == *"/") //TODO This should be OS independent...
            .unwrap()
            .free
            * 1024.0)
            >= (descriptor.computation_requirements.storage_size_mb as f64);

        let image = match descriptor.image {
            None => true,
            Some(img) => {
                if img.uri.as_str().starts_with("file://") {
                    let img_path = img.uri.as_str().strip_prefix("file://").unwrap();
                    Path::new(&img_path).exists().await
                } else {
                    true
                }
            }
        };

        // let interfaces = descriptor.interfaces.iter().filter(|x|
        //     match x.virtual_interface.vif_kind {
        //         im::fdu::VirtualInterfaceKind::BRIDGED | im::fdu::VirtualInterfaceKind::PHYSICAL => true,
        //         _ => false
        //     });
        // let faces = interfaces.iter().fold(
        //     true, |res, x| {
        //         match
        //     }
        // )



        let compatible = has_plugin && cpu_arch && cpu_number && cpu_freq && ram_size && disk_size && image;

        Ok(compatible)
    }

    async fn schedule_fdu(&self, fdu_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn onboard_fdu(&self, fdu: im::fdu::FDUDescriptor) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn define_fdu(&self, fdu_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn configure_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn start_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn run_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn log_fdu(&self, instance_uuid: Uuid) -> FResult<String> {
        Err(FError::Unimplemented)
    }

    async fn ls_fdu(&self, instance_uuid: Uuid) -> FResult<Vec<String>> {
        Err(FError::Unimplemented)
    }

    async fn file_fdu(&self, instance_uuid: Uuid, file_name: String) -> FResult<String> {
        Err(FError::Unimplemented)
    }

    async fn stop_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn clean_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn undefine_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn offload_fdu(&self, fdu_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn fdu_status(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn create_floating_ip(&self) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn delete_floating_ip(&self, ip_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn assing_floating_ip(&self, ip_uuid: Uuid, cp_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn retain_floating_ip(&self, ip_uuid: Uuid, cp_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }
}
