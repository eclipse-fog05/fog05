extern crate machine_uid;

use thiserror::Error;
use zenoh::*;
use std::fmt;

use log::{info, debug, warn, error, trace};

use async_std::task;
use async_std::sync::Arc;
use async_std::prelude::FutureExt;
use async_std::fs;
use async_std::path::Path;
use std::time::Duration;
use futures::prelude::*;
use std::process;
use std::str;
use std::str::FromStr;
use std::convert::TryFrom;
use std::convert::TryInto;
use uuid::Uuid;
use async_ctrlc::CtrlC;

//importing the macros
use zrpc_macros::{zservice, zserver};
use zrpc::ZServe;

use fog05_sdk::fresult::{FResult, FError};
use fog05_sdk::types::{IPAddress, InterfaceKind};
use fog05_sdk::agent::OS;
use fog05_sdk::zconnector::ZConnector;
use fog05_sdk::im;


use sysinfo;
use sysinfo::{SystemExt, ProcessorExt, ProcessExt, DiskExt};

static AGENT_PID_FILE: &str = "/tmp/fos_agent.pid";


#[derive(Clone)]
struct Agent {
    z : Arc<zenoh::Zenoh>,
    connector : Arc<fog05_sdk::zconnector::ZConnector>,
    pid : u32,
    node_uuid : Uuid,
}

impl Agent {
    pub async fn run(&self) {
        //this should return a channel to send the stop and a task handler to wait for
        loop {
            task::sleep(Duration::from_secs(10)).await;
        }
    }

    pub async fn start(&self) {

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

        for disk in system.get_disks() {
            let disk_spec = im::node::DiskSpec {
                local_address : String::from(disk.get_name().to_os_string().to_str().unwrap()),
                dimension : (disk.get_total_space() as f64)/1024.0/1024.0,
                mount_point : String::from(disk.get_mount_point().to_str().unwrap()),
                file_system : String::from(std::str::from_utf8(disk.get_file_system()).unwrap()),
            };

            disks.push(disk_spec);
        }

        trace!("OS: {}", os);
        trace!("Processors: {:?}", processors);
        trace!("RAM: {:?}", mem);
        trace!("Disks: {:?}", disks);




    }
}

#[zserver(uuid = "00000000-0000-0000-0000-000000000001")]
impl OS for Agent {
    async fn dir_exists(self, dir_path : String) -> FResult<bool> {
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
    async fn create_dir(self, dir_path : String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        fs::create_dir(path).await?;
        Ok(true)
    }
    async fn rm_dir(self, dir_path : String) -> FResult<bool> {
        let path = Path::new(&dir_path);
        fs::remove_dir(path).await?;
        Ok(true)
    }

    async fn download_file(self, url : url::Url, dest_path : String) -> FResult<bool> {
        Ok(true)
    }

    async fn create_file(self, file_path : String) -> FResult<bool> {
        let path = Path::new(&file_path);
        if !path.exists().await {
            let file = fs::File::create(path).await?;
            file.sync_all().await?;
            return Ok(true);
        }
        Ok(false)
    }

    async fn rm_file(self, file_path : String) -> FResult<bool> {
        let path = Path::new(&file_path);
        fs::remove_file(path).await?;
        Ok(true)
    }

    async fn store_file(self, content : Vec<u8>, file_path : String) -> FResult<bool> {
        Ok(true)
    }

    async fn read_file(self, file_path : String) -> FResult<Vec<u8>> {
        let path = Path::new(&file_path);
        let mut file = fs::File::open(path).await?;
        let mut content : Vec<u8> = Vec::new();
        file.read_to_end(&mut content).await?;
        Ok(content)
    }
    async fn file_exists(self, file_path : String) -> FResult<bool> {
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

    async fn execute_command(self, cmd : String) -> FResult<String> {
        Ok("".to_string())
    }
    async fn send_signal(self, signal : u8, pid : u32) -> FResult<bool> {
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
    async fn check_if_pid_exists(self, pid : u32) -> FResult<bool> {
        let mut system = sysinfo::System::new_all();
        system.refresh_all();
        let process = system.get_process(pid.try_into()?);
        match process {
            Some(_) => Ok(true),
            None => Ok(false),
        }
    }

    async fn get_interface_type(self, iface : String) -> FResult<InterfaceKind> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn set_interface_unavailable(self, iface : String) -> FResult<bool> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn set_interface_available(self, iface : String) -> FResult<bool> {
        Err(FError::UnknownError("Not yet...".to_string()))
    }

    async fn get_local_mgmt_address(self) -> FResult<IPAddress> {
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
    };

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    agent.start().await;
    ctrlc.race(agent.run()).await;

    //Here we send the stop signal to the agent object and waits that it ends

    info!("Bye!")





}