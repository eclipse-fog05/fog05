#![allow(unused_variables)]

extern crate machine_uid;
extern crate serde;
extern crate serde_json;
extern crate serde_yaml;



use std::process;
use std::str::FromStr;
use std::time::Duration;
use std::collections::HashMap;

use async_std::task;
use async_std::sync::Arc;
use async_std::prelude::*;



use log::{info, error, trace};

use zenoh::*;

use zrpc_macros::zserver;
use zrpc::ZServe;


use fog05_sdk::fresult::{FResult, FError};
use fog05_sdk::types::PluginKind;
use fog05_sdk::agent::{OSClient, AgentPluginInterfaceClient};
use fog05_sdk::zconnector::ZConnector;
use fog05_sdk::plugins::{HypervisorPlugin, NetworkingPluginClient};
use fog05_sdk::im::fdu::{FDUDescriptor, FDURecord};

use uuid::Uuid;
use async_ctrlc::CtrlC;

use structopt::StructOpt;


#[derive(StructOpt, Debug)]
struct DummyArgs {
    /// Config file
    #[structopt(short, long, default_value = "tcp/127.0.0.1:7447")]
    zenoh: String,
}


#[derive(Clone)]
pub struct DummyHypervisor {
    pub uuid : Uuid,
    pub z : Arc<zenoh::Zenoh>,
    pub connector : Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid : u32,
    pub agent : Option<AgentPluginInterfaceClient>,
    pub os : Option<OSClient>,
    pub net : Option<NetworkingPluginClient>,
    pub fdus : HashMap<Uuid, FDURecord>,
}


#[zserver(uuid = "00000000-0000-0000-0000-000000000003")]
impl HypervisorPlugin for DummyHypervisor {

    async fn define_fdu(&self, fdu : FDUDescriptor) -> FResult<FDURecord> {
        Err(FError::Unimplemented)
    }

    async fn undefine_fdu(&self, instance_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn configure_fdu(&self,instance_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn clean_fdu(&self,instance_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }


    async fn start_fdu(&self,instance_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }


    async fn run_fdu(&self,instance_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn log_fdu(&self,instance_uuid : Uuid) -> FResult<String> {
        Err(FError::Unimplemented)
    }
    async fn ls_fdu(&self,instance_uuid : Uuid) -> FResult<Vec<String>> {
        Err(FError::Unimplemented)
    }

    async fn file_fdu(&self,instance_uuid : Uuid, file_name : String) -> FResult<String> {
        Err(FError::Unimplemented)
    }


    async fn stop_fdu(&self,instance_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn migrate_fdu(&self,instance_uuid : Uuid, destination_uuid : Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
    }

    async fn get_fdu_status(&self,instance_uuid : Uuid) -> FResult<FDURecord> {
        Err(FError::Unimplemented)
    }

}


impl DummyHypervisor {
    async fn run(&self, stop : async_std::sync::Receiver<()>) {
        info!("DummyHypervisor main loop starting...");

        //starting the Agent-Plugin Server
        let hv_server = self.clone().get_hypervisor_plugin_server(self.z.clone());
        hv_server.connect();
        hv_server.initialize();


        self.agent.clone().unwrap().register_plugin(self.uuid, PluginKind::HYPERVISOR(String::from("dummy"))).await.unwrap().unwrap();

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
            Err(e) => trace!("Monitoring ending got error: {}",e),
        }

        self.agent.clone().unwrap().unregister_plugin(self.uuid).await.unwrap().unwrap();

        hv_server.stop(shv);
        hv_server.unregister();
        hv_server.disconnect();

        info!("DummyHypervisor main loop exiting")
    }

    pub async fn start(&mut self) -> (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {

        let local_os = OSClient::find_local_servers(self.z.clone()).await.unwrap();
        if local_os.is_empty() {
            error!("Unable to find a local OS interface");
            panic!("No OS Server");
        }

        let local_agent = AgentPluginInterfaceClient::find_local_servers(self.z.clone()).await.unwrap();
        if local_agent.is_empty() {
            error!("Unable to find a local Agent interface");
            panic!("No Agent Server");
        }

        let os = OSClient::new(self.z.clone(), local_os[0]);
        let agent = AgentPluginInterfaceClient::new(self.z.clone(), local_agent[0]);

        self.agent = Some(agent);
        self.os = Some(os);

        // Starting main loop in a task
        let (s, r) = async_std::sync::channel::<()>(1);
        let plugin = self.clone();
        let h = async_std::task::spawn(
            async move {
                plugin.run(r).await;
            }
        );
        (s,h)
    }

    pub async fn stop(&self, stop : async_std::sync::Sender<()>) {
        stop.send(()).await;
    }
}




#[async_std::main]
async fn main() {
    env_logger::init_from_env(env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"));

    let args = DummyArgs::from_args();
    info!("Dummy Hypervisor Plugin -- bootstrap");
    let my_pid = process::id();
    info!("PID is {}", my_pid);


    let properties = format!("mode=client;peer={}",args.zenoh.clone());
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let mut dummy = DummyHypervisor {
        uuid : Uuid::parse_str("00000000-0000-0000-0000-000000000003").unwrap(),
        z : zenoh.clone(),
        connector : zconnector.clone(),
        pid : my_pid,
        agent : None,
        os : None,
        net : None,
        fdus : HashMap::new(),
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
