#[macro_use]
extern crate std;

use async_std::task;
use async_std::sync::Arc;
use async_std::prelude::FutureExt;
use std::time::Duration;
use futures::prelude::*;
use fog05_zservice::ZServe;
use zenoh::*;
use std::str;
use std::str::FromStr;
use std::convert::TryFrom;
use uuid::Uuid;
//importing the macros
use fog05_zservice_macros::{zservice, zserver};

#[zservice(timeout_s = 10, prefix = "/lfos")]
pub trait Hello {
    async fn hello(name: String) -> String;
}


#[derive(Clone)]
struct HelloZService(String);

#[zserver(uuid = "10000000-0000-0000-0000-000000000001")]
impl Hello for HelloZService{
    async fn hello(self, name: String) -> String{
        format!("Hello {}!, you are connected to {}", name, self.0)
    }
}

#[async_std::main]
async fn main() {

    let zenoh = Arc::new(Zenoh::new(zenoh::config::client(Some(format!("tcp/127.0.0.1:7447").to_string()))).await.unwrap());
    let ws = Arc::new(zenoh.workspace(None).await.unwrap());

    let service = HelloZService("test service".to_string());


    let z = zenoh.clone();
    let ser_uuid = service.instance_uuid();
    let server = service.get_server(z);
    let client = HelloClient::new(ws.clone(), ser_uuid);


    server.connect();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    server.authenticate();

    // this should return an error as the server is not ready
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    server.register();
    server.announce();

    let (s, handle) = server.work();



    task::sleep(Duration::from_secs(1)).await;
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let hello = client.hello("client_two".to_string()).await;
    println!("Res is: {:?}", hello);


    server.unwork(s);
    server.unannounce();
    server.unregister();
    server.disconnect();
    server.stop();

    handle.await;

    // this should return an error as the server is not there
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);


}


