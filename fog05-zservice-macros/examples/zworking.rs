
#![feature(libstd_sys_internals)]
#![feature(print_internals)]
#![feature(fmt_internals)]
#![feature(prelude_import)]
#![feature(async_closure)]
#[prelude_import]
#[macro_use]

extern crate std;
extern crate serde;
extern crate bincode;
extern crate serde_json;
extern crate base64;
extern crate hex;

use async_std::task;
use async_std::sync::Arc;
use futures::prelude::*;
use fog05_zservice::ZServe;
use serde::{Serialize, Deserialize};
use zenoh::*;
use std::marker::PhantomData;
use std::str;
use std::convert::TryFrom;
use std::time::Duration;
use uuid::Uuid;
use std::str::FromStr;
use async_std::prelude::FutureExt;

pub trait Hello: Clone {

    fn hello(self, name: String) -> String;
    fn get_server(self, z : Arc<zenoh::Zenoh>) -> ServeHello<Self> {
        ServeHello {
            z : z,
            server: self,
        }
    }

    fn instance_uuid(&self) -> uuid::Uuid;
}

#[derive(Clone)]
pub struct ServeHello<S> {
    z : Arc<zenoh::Zenoh>,
    server: S,
}




impl<S> fog05_zservice::ZServe<HelloRequest> for ServeHello<S>
where
    S: Hello + Send +'static,
{
    type Resp = HelloResponse;


    fn connect(&self){
        task::block_on(
            async {
                let zsession = self.z.session();
                let zinfo = zsession.info().await;
                let rid = hex::encode(&(zinfo.iter().find(|x| x.0 == zenoh::net::info::ZN_INFO_ROUTER_PID_KEY ).unwrap().1));
                let pid = hex::encode(&(zinfo.iter().find(|x| x.0 == zenoh::net::info::ZN_INFO_PID_KEY).unwrap().1));
                let ws = self.z.workspace(None).await.unwrap();
                let component_advertisement = fog05_zservice::ComponentAdvertisement{
                    uuid : self.server.instance_uuid(),
                    name : "Test Component".to_string(),
                    routerid : rid.clone(),
                    peerid : pid.clone(),
                };
                let encoded_ca = bincode::serialize(&component_advertisement).unwrap();
                let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/info", self.server.instance_uuid())).unwrap();
                ws.put(&path.into(),encoded_ca.into()).await.unwrap();

                let component_info = fog05_zservice::ComponentInformation{
                    uuid : self.server.instance_uuid(),
                    name : "Test Component".to_string(),
                    routerid : rid.clone(),
                    peerid : pid.clone(),
                    status : fog05_zservice::ComponentStatus::HALTED,
                };
                let encoded_ci = bincode::serialize(&component_info).unwrap();
                let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                ws.put(&path.into(),encoded_ci.into()).await.unwrap();
            }
        )
    }

    fn authenticate(&self){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::HALTED => {
                                        ci.status = fog05_zservice::ComponentStatus::BUILDING;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                    },
                                    _ => panic!("Cannot authenticate a component in a state different than HALTED"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }

    fn register(&self){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::BUILDING => {
                                        ci.status = fog05_zservice::ComponentStatus::REGISTERED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                    },
                                    _ => panic!("Cannot register a component in a state different than BUILDING"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }

    fn announce(&self){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::REGISTERED => {
                                        ci.status = fog05_zservice::ComponentStatus::ANNOUNCED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                    },
                                    _ => panic!("Cannot announce a component in a state different than REGISTERED"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }

    fn work(&self) ->  (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {
        task::block_on(
            async {
                let (s, r) = async_std::sync::channel::<()>(1);
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::ANNOUNCED => {
                                        ci.status = fog05_zservice::ComponentStatus::WORK;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                        let server = self.clone();
                                        let h = async_std::task::spawn( async move {
                                            server.serve(r);
                                        });
                                        (s,h)
                                    },
                                    _ => panic!("Cannot work a component in a state different than ANNOUNCED"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }


    fn serve(&self, stop : async_std::sync::Receiver<()>)
    {
        task::block_on(async {
            let ws = self.z.workspace(None).await.unwrap();
            let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/eval", self.server.instance_uuid())).unwrap();
            let mut rcv = ws.register_eval(&path.clone().into()).await.unwrap();

            let rcv_loop = async {
                loop {
                    let get_request = rcv.next().await.unwrap();
                    let base64_req = get_request.selector.properties.get("req").cloned().unwrap();
                    let b64_bytes = base64::decode(base64_req).unwrap();
                    let js_req = str::from_utf8(&b64_bytes).unwrap();
                    let req = serde_json::from_str::<HelloRequest>(&js_req).unwrap();

                    match req {
                        HelloRequest::Hello { name } => {
                            let resp = HelloResponse::Hello(Hello::hello(self.server.clone(), name));
                            let encoded = bincode::serialize(&resp).unwrap();

                            get_request.reply(path.clone().into(), encoded.into()).await;
                        }
                    }
                }
            };
            rcv_loop.race(stop.recv()).await;
        });
    }

    fn unwork(&self, stop : async_std::sync::Sender<()>){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::WORK => {
                                        ci.status = fog05_zservice::ComponentStatus::UNWORK;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                        // Here we stop the serve
                                        stop.send(()).await;
                                    },
                                    _ => panic!("Cannot unwork a component in a state different than WORK"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }

    fn unannounce(&self){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::UNWORK => {
                                        ci.status = fog05_zservice::ComponentStatus::UNANNOUNCED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                        // Here we should stop the serve
                                    },
                                    _ => panic!("Cannot unannounce a component in a state different than UNWORK"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }

    fn unregister(&self){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::UNANNOUNCED => {
                                        ci.status = fog05_zservice::ComponentStatus::UNREGISTERED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                        // Here we should stop the serve
                                    },
                                    _ => panic!("Cannot unregister a component in a state different than UNANNOUNCED"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }

    fn disconnect(self){
        task::block_on(
            async {
                let selector = zenoh::Selector::try_from(format!("/this/is/generated/instance/{}/state",self.server.instance_uuid())).unwrap();
                let ws = self.z.workspace(None).await.unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut data = Vec::new();
                while let Some(d) = ds.next().await {
                    data.push(d)
                }
                match data.len() {
                    0 => panic!("This component state is not present in Zenoh!!"),
                    1 => {
                        let kv = &data[0];
                        match &kv.value {
                            zenoh::Value::Raw(_,buf) => {
                                let mut ci = bincode::deserialize::<fog05_zservice::ComponentInformation>(&buf.to_vec()).unwrap();
                                match ci.status {
                                    fog05_zservice::ComponentStatus::UNREGISTERED => {
                                        ci.status = fog05_zservice::ComponentStatus::DISCONNECTED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                                        ws.put(&path.into(),encoded_ci.into()).await.unwrap();
                                        // Here we should stop the serve
                                    },
                                    _ => panic!("Cannot disconnect a component in a state different than UNREGISTERED"),
                                }
                            },
                            _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                        }
                    },
                    _ => unreachable!(),
                }
            }
        )
    }
}


/// The request sent over the wire from the client to the server.
#[derive(Debug, Serialize, Deserialize)]
pub enum HelloRequest {
    Hello { name: String },
}

/// The response sent over the wire from the server to the client.
#[derive(Debug, Serialize, Deserialize)]
pub enum HelloResponse{
    Hello(String),
}




#[derive(Clone)]
struct HelloZService(String);


impl Hello for HelloZService {
    fn hello(
        self,
        name: String,
    ) -> String
    {
        let res = format!("Hello {}!, you are connected to {}", name, self.0);
        res
    }

    fn instance_uuid(&self) -> uuid::Uuid {
        Uuid::from_str("00000000-0000-0000-0000-000000000000").unwrap()
    }

}

#[allow(unused)]
/// The client stub that makes RPC calls to the server. Exposes a Future interface.
#[derive(Clone,Debug)]
pub struct HelloClient<'a, C = fog05_zservice::ZClientChannel<'a, HelloRequest, HelloResponse>>{
    ch : C,
    phantom : PhantomData<&'a ()>
}

impl HelloClient<'_> {
    pub fn new(
        ws : Arc<zenoh::Workspace>,
        instance_id : Uuid,
    ) -> HelloClient {
        let new_client = fog05_zservice::ZClientChannel::new(ws, "/this/is/generated/instance".to_string(), Some(instance_id));
        HelloClient{
            ch : new_client,
            phantom : PhantomData,
        }
    }
}

impl HelloClient<'_>
{
    #[allow(unused)]
    pub fn hello(
        &self,
        name: String,
    ) -> impl std::future::Future<Output = std::io::Result<String>> + '_{
        let request = HelloRequest::Hello { name };
        // Timeout is implemented here
        async move {
            match self.is_server_available().await {
                false => Err(std::io::Error::new(std::io::ErrorKind::PermissionDenied, "Server is not available".to_string())),
                true => {
                    let resp = self.ch.call_fun(request);
                    let dur = Duration::from_secs(10);
                    match async_std::future::timeout(dur, resp).await {
                        Ok(r) => match r {
                            Ok(zr) =>
                                match zr {
                                    HelloResponse::Hello(msg) => std::result::Result::Ok(msg),
                                    _ => ::std::rt::begin_panic("internal error: entered unreachable code"),
                                },
                            Err(e) => Err(e),
                        },
                        Err(e) => Err(std::io::Error::new(std::io::ErrorKind::TimedOut, format!("{}", e))),
                    }
                }
            }
        }
    }

    #[allow(unused)]
    pub fn is_server_available(&self) -> impl std::future::Future<Output = bool> + '_ {
        async move {
            self.ch.verify_server().await
        }
    }
}

#[async_std::main]
async fn main() {
    println!("HelloWorld!");


    let zenoh = Arc::new(Zenoh::new(zenoh::config::client(Some(format!("tcp/127.0.0.1:7447").to_string()))).await.unwrap());
    let ws = Arc::new(zenoh.workspace(None).await.unwrap());

    let service = HelloZService("test service".to_string());

    let z = zenoh.clone();
    let server = service.get_server(z);

    let instance_id = Uuid::from_str("00000000-0000-0000-0000-000000000000").unwrap();
    let mut client = HelloClient::new(ws, instance_id);

    server.connect();


    // this should return an error as the server is not ready
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    server.authenticate();
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

    handle.await;

}