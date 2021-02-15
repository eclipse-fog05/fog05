#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]

#[macro_use]
extern crate std;

use async_std::prelude::FutureExt;
use async_std::sync::{Arc, Mutex};
use async_std::task;
use futures::prelude::*;
use std::convert::TryFrom;
use std::str;
use std::time::Duration;
use uuid::Uuid;
use zenoh::*;

//importing the macros
use znrpc_macros::{znserver, znservice};
use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc::ZNServe;

#[znservice(timeout_s = 60, prefix = "/lfos")]
pub trait Hello {
    async fn hello(&self, name: String) -> String;
    async fn add(&mut self) -> u64;
}

#[derive(Clone)]
struct HelloZService {
    pub ser_name: String,
    pub counter: Arc<Mutex<u64>>,
}

#[znserver]
impl Hello for HelloZService {
    async fn hello(&self, name: String) -> String {
        format!("Hello {}!, you are connected to {}", name, self.ser_name)
    }

    async fn add(&mut self) -> u64 {
        let mut guard = self.counter.lock().await;
        *guard += 1;
        *guard
    }
}

#[async_std::main]
async fn main() {
    env_logger::init();
    let zproperties = Properties::from("mode=peer");
    let zsession = Arc::new(zenoh::net::open(zproperties.into()).await.unwrap());
    let service = HelloZService {
        ser_name: "test service".to_string(),
        counter: Arc::new(Mutex::new(0u64)),
    };

    let z = zsession.clone();

    let server = service.get_hello_server(z, None);
    let ser_uuid = server.instance_uuid();
    println!("Server instance UUID {}", ser_uuid);
    let client = HelloClient::new(zsession.clone(), ser_uuid);

    let (stopper, _h) = server.connect().await.unwrap();
    server.initialize().await.unwrap();
    server.register().await.unwrap();

    // let servers = HelloClient::find_servers(zsession.clone()).await;
    // println!("servers found: {:?}", servers);

    // this should return an error as the server is not ready
    // let hello = client.hello("client".to_string()).await;
    // println!("Res is: {:?}", hello);

    println!("Verify server: {:?}", client.verify_server().await);

    let (s, handle) = server.start().await.unwrap();

    let servers = HelloClient::find_servers(zsession.clone()).await;
    println!("servers found: {:?}", servers);

    let local_servers = HelloClient::find_local_servers(zsession.clone()).await;
    println!("local_servers found: {:?}", local_servers);

    println!("Verify server: {:?}", client.verify_server().await);

    task::sleep(Duration::from_secs(1)).await;

    println!("Verify server: {:?}", client.verify_server().await);

    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let res = client.add().await;
    println!("Res is: {:?}", res);

    let res = client.add().await;
    println!("Res is: {:?}", res);

    let res = client.add().await;
    println!("Res is: {:?}", res);

    server.stop(s).await.unwrap();

    // let servers = HelloClient::find_servers(zsession.clone()).await;
    // println!("servers found: {:?}", servers);

    server.unregister().await.unwrap();
    server.disconnect(stopper).await.unwrap();

    handle.await.unwrap();

    // this should return an error as the server is not there
    // let hello = client.hello("client".to_string()).await;
    // println!("Res is: {:?}", hello);
}
