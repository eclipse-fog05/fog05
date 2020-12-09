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
use zrpc::ZServe;
//importing the macros
use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc_macros::{zserver, zservice};

#[zservice(timeout_s = 60, prefix = "/lfos")]
pub trait Hello {
    async fn hello(&self, name: String) -> String;
    async fn add(&mut self) -> u64;
}

#[derive(Clone)]
struct HelloZService {
    pub ser_name: String,
    pub counter: Arc<Mutex<u64>>,
}

#[zserver]
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
    let zenoh = Arc::new(
        Zenoh::new(Properties::from("mode=client;peer=tcp/127.0.0.1:7447").into())
            .await
            .unwrap(),
    );
    // let ws = Arc::new(zenoh.workspace(None).await.unwrap());

    let service = HelloZService {
        ser_name: "test service".to_string(),
        counter: Arc::new(Mutex::new(0u64)),
    };

    let z = zenoh.clone();

    let server = service.get_hello_server(z, None);
    let ser_uuid = server.instance_uuid();
    let client = HelloClient::new(zenoh.clone(), ser_uuid);

    server.connect().await.unwrap();
    server.initialize().await.unwrap();
    server.register().await.unwrap();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    // this should return an error as the server is not ready
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let (s, handle) = server.start().await.unwrap();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    task::sleep(Duration::from_secs(1)).await;
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let hello = client.add().await;
    println!("Res is: {:?}", hello);

    let hello = client.add().await;
    println!("Res is: {:?}", hello);

    let hello = client.add().await;
    println!("Res is: {:?}", hello);

    server.stop(s).await.unwrap();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    server.unregister().await.unwrap();
    server.disconnect().await.unwrap();

    handle.await.unwrap();

    // this should return an error as the server is not there
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);
}
