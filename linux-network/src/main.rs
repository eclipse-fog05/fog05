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
extern crate serde;
extern crate serde_json;
extern crate serde_yaml;

use std::process;

use async_std::prelude::*;
use async_std::sync::Arc;

use zenoh::*;

use fog05_sdk::zconnector::ZConnector;

use async_ctrlc::CtrlC;

use structopt::StructOpt;

mod networking;
mod types;

use types::LinuxNetwork;

#[derive(StructOpt, Debug)]
struct LinuxNetArgs {
    /// Config file
    #[structopt(short, long, default_value = "tcp/127.0.0.1:7447")]
    zenoh: String,
}

#[async_std::main]
async fn main() {
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    let args = LinuxNetArgs::from_args();
    log::info!("Dummy Network Plugin -- bootstrap");
    let my_pid = process::id();
    log::info!("PID is {}", my_pid);

    let properties = format!("mode=client;peer={}", args.zenoh.clone());
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let mut net = LinuxNetwork::new(zenoh.clone(), zconnector.clone(), my_pid).unwrap();

    let (s, h) = net.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);

    stream.next().await;
    log::trace!("Received Ctrl-C start teardown");

    //Here we send the stop signal to the agent object and waits that it ends
    net.stop(s).await.unwrap();

    //wait for the futures to ends
    h.await;

    //zconnector.close();
    //zenoh.close();

    log::info!("Bye!")
}
