#[macro_use]
extern crate std;

use async_std::task;
use async_std::sync::Arc;
use std::time::Duration;
use futures::prelude::*;
use fog05_sdk::services::{ZServe};
use zenoh::*;
use std::str;
use std::str::FromStr;
use std::convert::TryFrom;
use uuid::Uuid;


//importing the macros
use fog05_macros::{zservice, zserver};

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

    let zenoh = Zenoh::new(zenoh::config::client(Some(format!("tcp/127.0.0.1:7447").to_string()))).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();
    let service = HelloZService("test1".to_string());

    let sid = service.instance_uuid();
    println!("Service UUID is: {}", sid);

    task::spawn(async move {
        let locator = format!("tcp/127.0.0.1:7447").to_string();
        service.get_server().serve(locator);
    });




    // let instance_id = Uuid::from_str("00000000-0000-0000-0000-000000000000").unwrap();
    let mut client = HelloClient::new(Arc::new(ws), sid);
    task::sleep(Duration::from_secs(1)).await;
    let hello = client.hello("client".to_string()).await;

    println!("Res is: {:?}", hello);

}


