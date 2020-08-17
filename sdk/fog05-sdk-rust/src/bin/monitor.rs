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

#![feature(async_closure)]

use async_std::future;
use std::env;
use zenoh::*;
use std::time::Duration;
use async_std::task;
use log::{info, trace, warn, error, debug};
use std::convert::TryFrom;
use protobuf::parse_from_bytes;

fn cb_component( r : Change) {

    match r.value {
        Some(zv) => {
            match zv {
                zenoh::Value::Raw(_,rbuf) => {
                    let value = parse_from_bytes::<fos::im::data::ComponentInformation>(&rbuf.to_vec()).unwrap();
                    info!("Component {} Status {:?}", &value.uuid, value);
                },
                _ => error!("Data expected to be Raw!"),
            }
        },
        None => info!("Component removed!"),
    }



}

fn cb_advertisement(r : Change)  {
    info!("Advertisement Subscriber received {:?} <= {:?}", r.path, r.value);
}


#[async_std::main]
async fn main() {

    env_logger::init();

    let args: Vec<String> = env::args().collect();
    info!("{:?}", args);

    let router = &args[1];

    info!("Connecting to Zenoh Router {:?} ", router);

    let zconfig = net::Config::client().add_peer(&router);
    let zenoh = Zenoh::new(zconfig, None).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();

    let component_selector = Selector::try_from("/components/*/info").unwrap();
    ws.subscribe_with_callback(&component_selector, cb_component).await.unwrap();




    future::pending::<()>().await;

}


