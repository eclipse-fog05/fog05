extern crate machine_uid;
extern crate serde;
extern crate serde_json;
extern crate serde_yaml;

use std::fmt;
use std::io::Write;
use std::process;
use std::str;
use std::str::FromStr;
use std::convert::TryFrom;
use std::convert::TryInto;
use std::time::Duration;
use std::collections::HashMap;

use async_std::task;
use async_std::sync::Arc;
use async_std::fs;
use async_std::path::Path;
use async_std::prelude::*;
//use async_std::prelude::{StreamExt,FutureExt};
use async_std::io::ReadExt;
// use futures::prelude::*;

use thiserror::Error;

use log::{info, debug, warn, error, trace};

use zenoh::*;

use zrpc_macros::{zservice, zserver};
use zrpc::ZServe;

use fog05_sdk::types;
use fog05_sdk::fresult::{FResult, FError};
use fog05_sdk::types::{IPAddress, InterfaceKind};
use fog05_sdk::agent::{OS, AgentPluginInterface};
use fog05_sdk::zconnector::ZConnector;
use fog05_sdk::im;
use fog05_sdk::plugins::{NetworkingPluginClient, HypervisorPluginClient};

use uuid::Uuid;
use async_ctrlc::CtrlC;

use sysinfo;
use sysinfo::{SystemExt, ProcessorExt, ProcessExt, DiskExt};


use serde::{Serialize, Deserialize};


#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AgentConfig {
    pub system : Uuid,
    pub pid_file : Box<std::path::Path>,
    pub zlocator : String,
    pub path : Box<std::path::Path>,
    pub mgmt_interface : String,
    pub monitoring_interveal : u64,
}


#[derive(Clone)]
pub struct Agent {
    pub z : Arc<zenoh::Zenoh>,
    pub connector : Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid : u32,
    pub node_uuid : Uuid,
    pub networking : Option<NetworkingPluginClient>,
    pub hypervisors : HashMap<String,HypervisorPluginClient>,
    pub config : AgentConfig,
}

impl Agent {
    async fn run(&self, stop: async_std::sync::Receiver<()>) {
        info!("Agent main loop starting...");
        //this should return a channel to send the stop and a task handler to wait for

        //starting the Agent-Plugin Server
        let a2p_server = self.clone().get_agent_plugin_interface_server(self.z.clone());
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
            info!("Monitoring loop started, with interveal {}", self.config.monitoring_interveal);
            let mut system = sysinfo::System::new_all();
            loop {
                let mut disks = Vec::<im::node::DiskStatus>::new();
                system.refresh_all();
                let mem = im::node::RAMStatus {
                    total : (system.get_total_memory() as f64)/1024.0,
                    free : (system.get_free_memory() as f64)/1024.0,
                };
                for disk in system.get_disks() {
                    let disk_status = im::node::DiskStatus {
                        mount_point : String::from(disk.get_mount_point().to_str().unwrap()),
                        total : (disk.get_total_space() as f64)/1024.0/1024.0,
                        free : (disk.get_available_space() as f64)/1024.0/1024.0
                    };
                    disks.push(disk_status);
                }

                let hvs : Vec<String> = self.hypervisors.keys().map(|x| (*x).clone()).collect();
                let status = match self.networking {
                    Some(_) => {
                        match hvs.len() {
                            0 => im::node::NodeStatusEnum::NOTREADY,
                            _ => im::node::NodeStatusEnum::READY,
                        }
                    },
                    None => im::node::NodeStatusEnum::NOTREADY
                };
                let node_status = im::node::NodeStatus {
                    uuid : self.node_uuid.clone(),
                    status : status,
                    ram : mem,
                    disk : disks,
                    supported_hypervisors : hvs,
                    neighbors : Vec::new(), //not yet...
                };

                self.connector.global.add_node_status(node_status).await.unwrap();

                task::sleep(Duration::from_secs(self.config.monitoring_interveal)).await;
            }
        };
        monitoring.race(stop.recv()).await;

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
        //let disks = Vec::new();

        //When starting we first get all node informations
        let mut system = sysinfo::System::new_all();
        //let arch = heim::host::platform().await.unwrap().architecture().as_str();
        let arch = std::env::consts::ARCH.to_string();

        //refresh information
        system.refresh_all();

        for processor in system.get_processors() {
            let cpu_spec = im::node::CPUSpec {
                model : processor.get_vendor_id().trim_end_matches("\u{0}").to_string(),
                frequency : processor.get_frequency(),
                arch : arch.clone(),
            };

            processors.push(cpu_spec);
        }

        let mem = im::node::RAMSpec{
            size : (system.get_total_memory() as f64)/1024.0,
        };
        let os =  String::from(std::env::consts::OS);
        let name = String::from(hostname::get().unwrap().to_str().unwrap());

        for disk in system.get_disks() {
            let disk_spec = im::node::DiskSpec {
                local_address : String::from(disk.get_name().to_os_string().to_str().unwrap()),
                dimension : (disk.get_total_space() as f64)/1024.0/1024.0,
                mount_point : String::from(disk.get_mount_point().to_str().unwrap()),
                file_system : String::from(std::str::from_utf8(disk.get_file_system()).unwrap()),
            };

            disks.push(disk_spec);
        }

        let ni = im::node::NodeInfo{
            uuid : self.node_uuid.clone(),
            name : name,
            os : os,
            cpu : processors,
            ram : mem,
            disks : disks,
            io : Vec::new(),
            accelerators : Vec::new(),
            position : None,
        };

        trace!("Node Info: {:?}", ni);

        self.connector.global.add_node_info(ni).await.unwrap();

        // Starting main loop in a task
        let (s, r) = async_std::sync::channel::<()>(1);
        let agent = self.clone();
        let h = async_std::task::spawn(
            async move {
                agent.run(r).await;
            }
        );
        (s,h)
    }

    pub async fn stop(&self, stop : async_std::sync::Sender<()>) {
        stop.send(()).await;
        self.connector.global.remove_node_status(self.node_uuid).await.unwrap();
        self.connector.global.remove_node_info(self.node_uuid).await.unwrap();
    }

}

#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl AgentPluginInterface for Agent {
    async fn fdu_info(&mut self, fdu_uuid : Uuid) -> FResult<im::fdu::FDUDescriptor> {
        trace!("Called fdu_info with {:?}", fdu_uuid);
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn image_info(&mut self, image_uuid : Uuid) -> FResult<im::fdu::Image> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn node_fdu_info(&mut self, fdu_uuid : Uuid, node_uuid : Uuid, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn network_info(&mut self, network_uuid : Uuid) -> FResult<types::VirtualNetwork> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn connection_point_info(&mut self, cp_uuid : Uuid) -> FResult<types::ConnectionPoint> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn node_management_address(&mut self, node_uuid : Uuid) -> FResult<IPAddress> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn create_virtual_network(&mut self, vnet : types::VirtualNetworkConfig) -> FResult<types::VirtualNetwork> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn remove_virtual_network(&mut self, vnet_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn create_connection_point(&mut self, cp : types::ConnectionPointConfig) -> FResult<types::ConnectionPoint> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn remove_connection_point(&mut self, cp_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn bind_cp_to_fdu_face(&mut self, cp_uuid : Uuid, instance_uuid : Uuid, interface : String) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn unbind_co_from_fdu_face(&mut self, cp_uuid : Uuid, instance_uuid : Uuid, interface : String) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn bind_cp_to_network(&mut self, cp_uuid : Uuid, vnet_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
    async fn unbind_cp_from_network(&mut self, cp_uuid : Uuid, vnet_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn register_plugin(&mut self, plugin_uuid : Uuid, kind : types::PluginKind) -> FResult<Uuid> {
        trace!("register_plugin called with {} {:?}", plugin_uuid, kind);
        match kind {
            types::PluginKind::HYPERVISOR(hv) => {
                match self.hypervisors.get(&hv) {
                    Some(_) => Err(FError::AlreadyPresent),
                    None => {
                        trace!("Adding Hypervisor plugin {} {}", plugin_uuid, hv);
                        let hv_client = HypervisorPluginClient::new(self.z.clone(), plugin_uuid);
                        self.hypervisors.insert(hv.clone(), hv_client);
                        trace!("Added Hypervisor plugin {} {}", plugin_uuid, hv);
                        Ok(plugin_uuid)
                    },
                }
            },
            types::PluginKind::NETWORKING => {
                match self.networking {
                    Some(_) => Err(FError::AlreadyPresent),
                    None => {
                        let nw_client = NetworkingPluginClient::new(self.z.clone(), plugin_uuid);
                        self.networking = Some(nw_client);
                        Ok(plugin_uuid)
                    },
                }
            }
            _ => Err(FError::UnknownError("Not yet...".to_string())),
        }
    }

    async fn unregister_plugin(&mut self, plugin_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }
}




#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl OS for Agent {
    async fn dir_exists(&mut self, dir_path : String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        if !path.exists().await {
            return Ok(false)
        }
        let file_type = fs::metadata(path).await?.file_type();
        if file_type.is_dir() {
            return Ok(true);
        }
        Ok(false)
    }
    async fn create_dir(&mut self, dir_path : String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        fs::create_dir(path).await?;
        Ok(true)
    }
    async fn rm_dir(&mut self, dir_path : String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        fs::remove_dir(path).await?;
        Ok(true)
    }

    async fn download_file(&mut self, url : url::Url, dest_path : String) -> FResult<bool> {
        task::spawn(
            async move {
                trace!("Start downloading: {}", url);
                match reqwest::blocking::get(url.clone()) {
                    Err(err) => error!("Error in getting {} error: {}", url, err),
                    Ok(resp) => {
                        let mut out = fs::File::create(dest_path.clone()).await;
                        match out {
                            Err(err) => error!("Unable to create destination file {} for {} error: {}", dest_path, url, err),
                            Ok(mut f) => {
                                let bytes = resp.bytes().unwrap();
                                let mut slice: &[u8] = bytes.as_ref();
                                match async_std::io::copy(&mut slice, &mut f).await {
                                    Ok(_) => trace!("Done downloading: {} info {}", url, dest_path),
                                    Err(err) => error!("Unable to copy content: {}", err),
                                }
                            },
                        }
                    },
                }
            }
        );
        Ok(true)
    }

    async fn create_file(&mut self, file_path : String) -> FResult<bool> {
        let path = Path::new(&file_path);
        if !path.exists().await {
            let file = fs::File::create(path).await?;
            file.sync_all().await?;
            return Ok(true);
        }
        Ok(false)
    }

    async fn rm_file(&mut self, file_path : String) -> FResult<bool> {
        let path = Path::new(&file_path);
        fs::remove_file(path).await?;
        Ok(true)
    }

    async fn store_file(&mut self, content : Vec<u8>, file_path : String) -> FResult<bool> {
        Ok(true)
    }

    async fn read_file(&mut self, file_path : String) -> FResult<Vec<u8>> {
        let path = Path::new(&file_path);
        let mut file = fs::File::open(path).await?;
        let mut content : Vec<u8> = Vec::new();
        file.read_to_end(&mut content).await?;
        Ok(content)
    }
    async fn file_exists(&mut self, file_path : String) -> FResult<bool> {
        let path = Path::new(&file_path);
        if !path.exists().await {
            return Ok(false)
        }
        let file_type = fs::metadata(path).await?.file_type();
        if file_type.is_file() {
            return Ok(true);
        }
        Ok(false)
    }

    async fn execute_command(&mut self, cmd : String) -> FResult<String> {
        Ok("".to_string())
    }

    async fn send_signal(&mut self, signal : u8, pid : u32) -> FResult<bool> {
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

    async fn check_if_pid_exists(&mut self, pid : u32) -> FResult<bool> {
        let mut system = sysinfo::System::new_all();
        system.refresh_all();
        let process = system.get_process(pid.try_into()?);
        match process {
            Some(_) => Ok(true),
            None => Ok(false),
        }
    }

    async fn get_interface_type(&mut self, iface : String) -> FResult<InterfaceKind> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn set_interface_unavailable(&mut self, iface : String) -> FResult<bool> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn set_interface_available(&mut self, iface : String) -> FResult<bool> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn get_local_mgmt_address(&mut self) -> FResult<IPAddress> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

}