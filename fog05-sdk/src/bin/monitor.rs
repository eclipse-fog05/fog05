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


extern crate serde;
extern crate serde_json;
#[macro_use] extern crate prettytable;

use async_std::future;
use std::env;
use zenoh::*;
use std::time::Duration;
use async_std::task;
use async_std::sync::{Mutex,Arc};
use log::{info, trace, warn, error, debug};
use std::convert::TryFrom;
use fog05_sdk::im::data::ComponentInformation;
use std::collections::HashMap;
use futures::prelude::*;
use futures::select;

use prettytable::{Table, Row, Cell};

use serde::{Serialize, Deserialize};

pub struct MonitorInfo {
    pub components : HashMap<String,ComponentInformation>
}

// pub struct MonitorState {
//     pub state : Mutex<MonitorInfo>
// }


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ZSessionInfo {
    peer : String,
    links : Vec<String>,
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ZPluginInfo {
    name : String,
    path : String,
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ZRouterInfo {
    pid : String,
    locators : Vec<String>,
    sessions : Vec<ZSessionInfo>,
    plugins : Vec<ZPluginInfo>,
    time : Option<String>,
}



pub struct Monitor<'a> {
    state : Arc<Mutex<MonitorInfo>>,
    ws : Arc<Workspace<'a>>,
    z : Arc<&'a zenoh::net::Session>
}

impl<'a> Monitor<'a> {
    pub async fn new(ws : Arc<Workspace<'a>>, session : Arc<&'a zenoh::net::Session>) -> Monitor<'a> {

        Monitor{
            state : Arc::new(Mutex::new(MonitorInfo{components: HashMap::new()})),
            z : session,
            ws : ws,
        }
    }

    pub async fn check_components(&self) {
        loop {
            let mut s = self.state.lock().await;
            let mut to_remove : Vec<String> = Vec::new();

            {
                for (k,v) in  &s.components {
                    let selector = Selector::try_from(format!("/@/router/{}", String::from(&v.routerid))).unwrap();
                    match self.ws.get(&selector).await {
                    Err(_) => error!("Error in getting info from router {}", String::from(&v.routerid)),
                    Ok(mut datastream) => {
                        while let Some(d) = datastream.next().await {
                            match d.value {
                                Value::Json(sv) => {
                                    let ri = serde_json::from_str::<ZRouterInfo>(&sv).unwrap();
                                    let mut it = ri.sessions.iter();
                                    let f = it.find( |&x| {
                                        x.peer == String::from(&v.peerid).to_uppercase()
                                    });
                                    match f {
                                        None => to_remove.push(String::from(k)),
                                        Some(_) => info!("Component still there {}",  String::from(&v.peerid)),
                                    }
                                },
                                _ => error!("Value is not in the correct format {} -> {:?}",d.path, &d.value),
                            }
                        }
                    }
                }
            }
            }
            for k in to_remove.iter() {
                info!("Component {} is dead!",  String::from(k));
                s.components.remove(k);
            }
            // task::sleep(Duration::from_secs(1)).await;
            task::sleep(Duration::from_millis(750)).await;
        }
    }

    pub async fn listen_comp(&self, r : Change) {
        let mut s = self.state.lock().await;
        match r.value {
            Some(zv) => {
                match zv {
                    zenoh::Value::Raw(_,rbuf) => {
                        let value = bincode::deserialize::<ComponentInformation>(&rbuf.to_vec()).unwrap();
                        info!("Component {} Status {:?}", value.uuid, &value);
                        s.components.insert(value.uuid.to_string(), value);
                    },
                    _ => error!("Data expected to be Raw!"),
                }
            },
            None => {
                let p = r.path.as_str();
                let tok : Vec<&str> = p.split("/").collect();
                let cid = tok[2];
                info!("Component {} removed!", cid);
                s.components.remove(cid);
            },
        }
    }
    pub async fn listen_all_component(&self) -> ChangeStream<'_> {
        let component_selector = Selector::try_from("/components/*/info").unwrap();
        // ws.subscribe_with_callback(&component_selector, comp_cb ).await.unwrap();

        self.ws.subscribe(&component_selector).await.unwrap()

    }


    pub async fn table_output(&self) {

        loop {
            //clear screen
            print!("{esc}[2J{esc}[1;1H", esc = 27 as char);
            let mut s = self.state.lock().await;
            let mut table = Table::new();

            table.add_row(row!["ID", "PeerID", "Status"]);
            for (_,v) in &s.components {
                table.add_row(row![v.uuid.to_string(), String::from(&v.peerid), format!("{:?}",&v.status)]);
            }
            table.printstd();
            task::sleep(Duration::from_millis(250)).await;
        }
    }
}


#[async_std::main]
async fn main() {

    env_logger::init();

    let args: Vec<String> = env::args().collect();
    info!("{:?}", args);

    let router = &args[1];

    let zenoh = Zenoh::new(zenoh::config::client(Some(router.to_string()))).await.unwrap();
    let ws = Arc::new(zenoh.workspace(None).await.unwrap());
    let zsession = Arc::new(zenoh.session());

    info!("Connecting to Zenoh Router {:?} ", router);

    let monitor : Arc<Monitor> = Arc::new(Monitor::new(ws, zsession).await);

    let mut comp_stream = monitor.listen_all_component().await;


    // Subscriber/Eval dispatcher
    //let handle = task::spawn(async {
            loop {
                select!(
                    next = comp_stream.next().fuse() => {
                        let next = next.unwrap();
                        monitor.listen_comp(next).await
                    },
                );
            }
            //});





    //handle.await;

}


