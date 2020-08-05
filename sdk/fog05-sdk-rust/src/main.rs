#![feature(async_closure)]
pub mod im;

use zenoh::net::Config;
use zenoh::*;
use futures::prelude::*;
use std::convert::TryInto;
use std::convert::TryFrom;
use im::data::*;
use std::env;


use protobuf::parse_from_bytes;
use protobuf::Message;

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
    let mut myself = fos::InternalComponent::<MyState>::new(id, name).await.unwrap();


    //connecting to zenoh
    match myself.connect(router).await {
        Err(why) => panic!("Error when connecting component {:?}", why),
        Ok(_) => {
            println!("Component is connected to Zenoh");
            println!("Connected to Zenoh Router: {} Component Status: {:?}",  myself.get_routerid().await, myself.get_status().await);
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

    match myself.get_state().await.unwrap() {
        None => {
            println!("No state found in Zenoh, starting from new state");
            let m_state = MyState {
                one : String::from("This is a string"),
                two : 123_000_000_456,
                three : 123.456
            };

            myself.put_state(m_state.clone()).await.unwrap();
        },
        Some(current_state) =>
            println!("State found in Zenoh {:?}", current_state,
        ),
    }



    //registering
    match myself.register().await {
        Err(why) => panic!("Error when registering component {:?}", why),
        Ok(_) => {
            println!("Component is registered to Zenoh");
            println!("Component Status: {:?} Component State: {:?}", myself.get_status().await, myself.get_state().await.unwrap());
        },
    }







}


