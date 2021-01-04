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

use std::process;

use async_std::fs;
use async_std::path::Path;
use async_std::prelude::*;
use async_std::sync::Arc;

use zenoh::*;

use fog05_sdk::zconnector::ZConnector;

use async_ctrlc::CtrlC;

use structopt::StructOpt;

use linux_network::types::{deserialize_plugin_config, LinuxNetwork};

static CONFIG_FILE: &str = "/etc/fos/linux-network/config.yaml";

#[derive(StructOpt, Debug)]
struct LinuxNetArgs {
    /// Config file
    #[structopt(short, long, default_value = CONFIG_FILE)]
    config: String,
}

async fn read_file(path: &Path) -> String {
    fs::read_to_string(path).await.unwrap()
}

#[async_std::main]
async fn main() {
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    let args = LinuxNetArgs::from_args();
    log::info!("Linux Network Plugin -- bootstrap");
    let my_pid = process::id();
    log::info!("PID is {}", my_pid);

    let conf_file_path = Path::new(&args.config);
    let config =
        deserialize_plugin_config(&(read_file(&conf_file_path).await.into_bytes().as_slice()))
            .unwrap();

    let properties = format!("mode=client;peer={}", config.zlocator.clone());
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let mut net = LinuxNetwork::new(zenoh.clone(), zconnector.clone(), my_pid, config).unwrap();

    let (s, h) = net.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);

    stream.next().await;
    log::trace!("Received Ctrl-C start teardown");

    //Here we send the stop signal to the agent object and waits that it ends
    net.stop(s).await.unwrap();

    //wait for the futures to ends
    h.await.unwrap();

    //zconnector.close();
    //zenoh.close();

    log::info!("Bye!")
}
