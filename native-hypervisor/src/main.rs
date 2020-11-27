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
#![allow(unused_variables)]

use std::collections::HashMap;
use std::process;

use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};

use zenoh::*;

use fog05_sdk::zconnector::ZConnector;

use async_ctrlc::CtrlC;

use structopt::StructOpt;

pub mod native;
pub mod types;

use types::{NativeHVState, NativeHypervisor};

#[derive(StructOpt, Debug)]
struct DummyArgs {
    /// Config file
    #[structopt(short, long, default_value = "tcp/127.0.0.1:7447")]
    zenoh: String,
}

#[async_std::main]
async fn main() {
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    let args = DummyArgs::from_args();
    log::info!("Native Hypervisor Plugin -- bootstrap");
    let my_pid = process::id();
    log::info!("PID is {}", my_pid);

    let properties = format!("mode=client;peer={}", args.zenoh.clone());
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let mut native = NativeHypervisor {
        z: zenoh.clone(),
        connector: zconnector.clone(),
        pid: my_pid,
        agent: None,
        os: None,
        net: None,
        fdus: Arc::new(RwLock::new(NativeHVState {
            uuid: None,
            fdus: HashMap::new(),
            childs: HashMap::new(),
        })),
    };

    let (s, h) = native.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);
    stream.next().await;
    log::trace!("Received Ctrl-C start teardown");

    //Here we send the stop signal to the agent object and waits that it ends
    native.stop(s).await;

    //wait for the futures to ends
    h.await.unwrap();

    //zconnector.close();
    //zenoh.close();

    log::info!("Bye!")
}
