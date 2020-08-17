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

// use zenoh::net::Config;
// use zenoh::*;
// use futures::prelude::*;
// use std::convert::TryInto;
// use std::convert::TryFrom;
// use im::data::*;
use std::env;

use std::time::Duration;
use async_std::task;

// use protobuf::parse_from_bytes;
// use protobuf::Message;

extern crate serde;
extern crate hex;
use serde::{Serialize, Deserialize};



#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct MyState {
    pub one : String,
    pub two : u64,
    pub three : f64,
}

// fn cb( r : Change) {
//     println!("Subscriber received {:?} <= {:?}", r.path, r.value);
// }

#[async_std::main]
async fn main() {

    let args: Vec<String> = env::args().collect();
    println!("{:?}", args);

    let router = &args[1];
    let id = String::from(&args[2]);
    let name = String::from(&args[3]);

    //creating the decentralized component
    let mut myself = fos::Component::<MyState>::new(id, name).await;


    //connecting to zenoh
    match myself.connect(router).await {
        Err(why) => panic!("Error when connecting component {:?}", why),
        Ok(_) => {
            println!("Component is connected to Zenoh");
            println!("Connected to Zenoh Router: {} Zenoh PeerId: {} Component Status: {:?}",  myself.get_routerid().await, myself.get_peerid().await, myself.get_status().await);
        },

    }

    //authenticating
    match myself.authenticate().await {
        Err(why) => panic!("Error when authenticating component {:?}", why),
        Ok(_) => {
            println!("Component is authenticated to Zenoh");
            println!("Component Status: {:?}", myself.get_status().await);
        },
    }

    //reading state from zenoh
    myself.read().await.unwrap();

    match myself.get_state().await {
        None => {
            println!("No state found in Zenoh, starting from new state");
            let m_state = MyState {
                one : String::from("This is a string"),
                two : 0,
                three : 123.456
            };

            myself.put_state(m_state.clone()).await.unwrap();
        },
        Some(mut current_state) => {
            println!("State found in Zenoh!!");
            // // Updating the state just for testing
            // current_state.two += 1;
            // myself.put_state(current_state.clone()).await.unwrap();
        }
    }



    //registering
    match myself.register().await {
        Err(why) => panic!("Error when registering component {:?}", why),
        Ok(_) => {
            println!("Component is registered to Zenoh");
            println!("Component Status: {:?} Component State: {:?}", myself.get_status().await, myself.get_state().await.unwrap());
        },
    }


    myself.announce().await.unwrap();
    println!("Component is announced to Zenoh");

    myself.work().await.unwrap();
    println!("Component is Working");


    for _ in 0..10 {
        let mut s = myself.get_state().await.unwrap();
        s.two += 1;
        myself.put_state(s.clone()).await.unwrap();
        myself.sync_state().await.unwrap();
        task::sleep(Duration::from_millis(250)).await;
    }



    myself.unwork().await.unwrap();
    println!("Component is Unworking");

    myself.unannounce().await.unwrap();
    println!("Component is Unannounced on Zenoh");

    myself.unregister().await.unwrap();
    println!("Component is Unregistered on Zenoh");



    myself.disconnect().await.unwrap();
    println!("Component is disconnected from Zenoh");

    myself.stop().await.unwrap();
    println!("Component is Stopped");


}


