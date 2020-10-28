extern crate machine_uid;

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

static AGENT_PID_FILE: &str = "/tmp/fos_agent.pid";


#[derive(Clone)]
struct Agent {
    z : Arc<zenoh::Zenoh>,
    connector : Arc<fog05_sdk::zconnector::ZConnector>,
    pid : u32,
    node_uuid : Uuid,
    networking : Option<NetworkingPluginClient>,
    hypervisors : HashMap<String,HypervisorPluginClient>,
}

impl Agent {
    async fn run(&self, stop: async_std::sync::Receiver<()>) {
        info!("Agent main loop starting...");
        //this should return a channel to send the stop and a task handler to wait for

        let a2p_server = AgentPluginInterface::get_server((*self).clone(),self.z.clone());
        a2p_server.connect();
        a2p_server.initialize();
        a2p_server.register();

        let (sa2p, ha2p) = a2p_server.start();

        let l = async {
            loop {
                task::sleep(Duration::from_secs(10)).await;
            }
        };
        l.race(stop.recv()).await;

        a2p_server.stop(sa2p);
        a2p_server.unregister();
        a2p_server.disconnect();

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
    }

}

#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl AgentPluginInterface for Agent {
    async fn fdu_info(&mut self, fdu_uuid : Uuid) -> FResult<im::fdu::FDUDescriptor> {
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
        match kind {
            types::PluginKind::HYPERVISOR(hv) => {
                match self.hypervisors.get(&hv) {
                    Some(_) => Err(FError::AlreadyPresent),
                    None => {
                        let hv_client = HypervisorPluginClient::new(self.z.clone(), plugin_uuid);
                        self.hypervisors.insert(hv, hv_client);
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

async fn read_file(path : &Path) -> String {
    fs::read_to_string(path).await.unwrap()
}


async fn write_file(path : &Path, content : Vec<u8>) {
    let mut file = fs::File::create(path).await.unwrap();
    file.write_all(&content).await.unwrap();
    file.sync_all().await.unwrap();

}

#[async_std::main]
async fn main() {
    // Init logging
    env_logger::init_from_env(env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"));


    info!("Eclipse fog05 Agent -- bootstrap");

    //Getting PID
    let my_pid = process::id();

    info!("PID is {}", my_pid);

    let pid_file_path = Path::new(AGENT_PID_FILE);

    //Read Agent PID file
    let old_pid : Option<u32> = if pid_file_path.exists().await {
        Some(read_file(pid_file_path).await.parse::<u32>().unwrap())
    } else {
        None
    };

    if let Some(pid) = old_pid {
        // There is a PID for an old agent
        // we check if it is still running
        trace!("There is an old PID file existing, checking if the process {} is still running", pid);

        match psutil::process::Process::new(pid) {
            Ok(old_proc) => {
                if old_proc.is_running() {
                    error!("There is an agent already running, panic!");
                    // We panic if there is already an agent running on this machine
                    panic!("A fog05 Agent is already running in this machine!!!")
                }
            },
            _ => trace!("Old agent is not running, removing the PID file..."),
        }

        // If the process is not running we remove the file
        fs::remove_file(pid_file_path).await.unwrap();
    }

    //We create a file with the new PID

    write_file(pid_file_path, my_pid.to_string().into_bytes()).await;

    // Getting Node UUID
    let node_id_raw = machine_uid::get().unwrap();
    let node_str : &str = &node_id_raw;
    let node_uuid = Uuid::parse_str(node_str).unwrap();
    info!("Node UUID is {}", node_uuid);


    //Creating the Zenoh and ZConnector
    let zenoh = Arc::new(Zenoh::new(zenoh::config::client(Some(format!("tcp/127.0.0.1:7447").to_string()))).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    // Creating Agent
    let agent = Agent{
        z : zenoh.clone(),
        connector : zconnector.clone(),
        pid : my_pid,
        node_uuid : node_uuid,
        networking : None,
        hypervisors : HashMap::new(),
    };

    //Starting the agent
    let (s, h) = agent.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);
    while let Some((_, _)) = stream.next().await {
        trace!("Received Ctrl-C start teardown");
        break;
    }

    //ctrlc.race(h).await;

    //Here we send the stop signal to the agent object and waits that it ends
    agent.stop(s).await;

    //wait for the futures to ends
    h.await;


    //zconnector.close();
    //zenoh.close();

    info!("Bye!")

}