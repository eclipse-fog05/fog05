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

extern crate machine_uid;

use std::process;
use std::str;

use std::collections::HashMap;

use async_std::fs;
use async_std::path::Path;
use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};

use log::{debug, error, info, trace};

use zenoh::*;

use fog05_sdk::zconnector::ZConnector;

use async_ctrlc::CtrlC;
use uuid::Uuid;

use structopt::StructOpt;

pub mod agent;

use agent::{Agent, AgentConfig, AgentInner};

use git_version::git_version;

//static AGENT_PID_FILE: &str = "/tmp/fos_agent.pid";
static AGENT_CONFIG_FILE: &str = "/etc/fos/agent.yaml";

const GIT_VERSION: &str = git_version!(prefix = "v", cargo_prefix = "v");

#[derive(StructOpt, Debug)]
struct AgentArgs {
    /// Config file
    #[structopt(short, long, default_value = AGENT_CONFIG_FILE)]
    config: String,
}

async fn read_file(path: &Path) -> String {
    fs::read_to_string(path).await.unwrap()
}

async fn write_file(path: &Path, content: Vec<u8>) {
    let mut file = fs::File::create(path).await.unwrap();
    file.write_all(&content).await.unwrap();
    file.sync_all().await.unwrap();
}

#[async_std::main]
async fn main() {
    // Init logging
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    debug!("Eclipse fog05 Agent {}", GIT_VERSION);

    let args = AgentArgs::from_args();
    let conf_file_path = Path::new(&args.config);
    let config = serde_yaml::from_str::<AgentConfig>(&(read_file(&conf_file_path).await)).unwrap();

    info!("Eclipse fog05 Agent -- bootstrap");

    //Getting PID
    let my_pid = process::id();

    info!("PID is {}", my_pid);

    let pid_file_path = Path::new(&config.pid_file);

    //Read Agent PID file
    let old_pid: Option<u32> = if pid_file_path.exists().await {
        Some(read_file(pid_file_path).await.parse::<u32>().unwrap())
    } else {
        None
    };

    if let Some(pid) = old_pid {
        // There is a PID for an old agent
        // we check if it is still running
        trace!(
            "There is an old PID file existing, checking if the process {} is still running",
            pid
        );

        match psutil::process::Process::new(pid) {
            Ok(old_proc) => {
                if old_proc.is_running() {
                    error!("There is an agent already running, panic!");
                    // We panic if there is already an agent running on this machine
                    panic!("A fog05 Agent is already running in this machine!!!")
                }
            }
            _ => trace!("Old agent is not running, removing the PID file..."),
        }

        // If the process is not running we remove the file
        fs::remove_file(pid_file_path).await.unwrap();
    }

    //We create a file with the new PID

    write_file(pid_file_path, my_pid.to_string().into_bytes()).await;

    // Getting Node UUID
    let node_id_raw = machine_uid::get().unwrap();
    let node_str: &str = &node_id_raw;
    let node_uuid = Uuid::parse_str(node_str).unwrap();
    info!("Node UUID is {}", node_uuid);

    //Creating the Zenoh and ZConnector
    let zproperties = format!("mode=client;peer={}", config.zlocator.clone());
    let z = Arc::new(Zenoh::new(zproperties.clone().into()).await.unwrap());
    let zenoh = Arc::new(zenoh::net::open(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(z.clone(), Some(config.system), None));

    // Creating Agent
    let agent = Agent {
        z: zenoh.clone(),
        connector: zconnector.clone(),
        node_uuid,
        agent: Arc::new(RwLock::new(AgentInner {
            pid: my_pid,
            networking: None,
            hypervisors: HashMap::new(),
            config,
            instance_uuid: None,
        })),
    };

    //Starting the agent
    let (s, h) = agent.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);
    stream.next().await;
    trace!("Received Ctrl-C start teardown");

    //Here we send the stop signal to the agent object and waits that it ends
    agent.stop(s).await;

    //wait for the futures to ends
    h.await.unwrap();

    //zconnector.close();
    //zenoh.close();

    info!("Bye!")
}
