#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]
#![feature(libstd_sys_internals)]
#![feature(print_internals)]
#![feature(fmt_internals)]
#![feature(prelude_import)]
#![feature(async_closure)]
#[prelude_import]
#[macro_use]
extern crate std;
extern crate base64;
extern crate bincode;
extern crate hex;
extern crate serde;
extern crate serde_json;

use async_std::prelude::FutureExt;
use async_std::sync::{Arc, Mutex};
use async_std::task;
use futures::prelude::*;
use serde::{Deserialize, Serialize};
use std::convert::TryFrom;
use std::str;
use std::time::Duration;
use uuid::Uuid;
use zenoh::*;
use zrpc::ZServe;

pub trait Hello: Clone {
    fn hello(&self, name: String) -> String;
    fn get_hello_server(self, z: Arc<zenoh::Zenoh>) -> ServeHello<Self> {
        ServeHello::new(z, self)
    }
    fn add(&mut self) -> u64;
}

#[derive(Clone)]
pub struct ServeHello<S> {
    z: Arc<zenoh::Zenoh>,
    server: S,
    instance_id: Uuid,
}

impl<S> ServeHello<S> {
    pub fn new(z: Arc<zenoh::Zenoh>, server: S) -> Self {
        Self {
            z,
            server,
            instance_id: Uuid::new_v4(),
        }
    }
}

impl<S> zrpc::ZServe<HelloRequest> for ServeHello<S>
where
    S: Hello + Send + 'static,
{
    type Resp = HelloResponse;

    fn instance_uuid(&self) -> uuid::Uuid {
        self.instance_id
    }

    fn connect(&mut self) {
        task::block_on(async {
            let zsession = self.z.session();
            let zinfo = zsession.info().await;
            let pid = zinfo
                .get(&zenoh::net::info::ZN_INFO_PID_KEY)
                .unwrap()
                .to_uppercase();
            let rid = zinfo
                .get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY)
                .unwrap()
                .split(',')
                .collect::<Vec<_>>()[0]
                .to_uppercase();
            let ws = self.z.workspace(None).await.unwrap();

            let component_info = zrpc::ComponentState {
                uuid: self.instance_uuid(),
                name: "Hello".to_string(),
                routerid: rid.clone().to_uppercase(),
                peerid: pid.clone().to_uppercase(),
                status: zrpc::ComponentStatus::HALTED,
            };
            let encoded_ci = bincode::serialize(&component_info).unwrap();
            let path = zenoh::Path::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
            ws.put(&path, encoded_ci.into()).await.unwrap();
        })
    }

    fn initialize(&self) {
        task::block_on(async {
            let selector = zenoh::Selector::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
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
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci =
                                bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec())
                                    .unwrap();
                            match ci.status {
                                    zrpc::ComponentStatus::HALTED => {
                                        ci.status = zrpc::ComponentStatus::INITIALIZING;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/Hello/instance/{}/state",
                                        self.instance_uuid())).unwrap();
                                        ws.put(&path,encoded_ci.into()).await.unwrap();
                                    },
                                    _ => panic!("Cannot authenticate a component in a state different than HALTED"),
                                }
                        }
                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                    }
                }
                _ => unreachable!(),
            }
        })
    }

    fn register(&self) {
        task::block_on(async {
            let selector = zenoh::Selector::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
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
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci =
                                bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec())
                                    .unwrap();
                            match ci.status {
                                    zrpc::ComponentStatus::INITIALIZING => {
                                        ci.status = zrpc::ComponentStatus::REGISTERED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!("/this/is/generated/Hello/instance/{}/state",
                                        self.instance_uuid())).unwrap();
                                        ws.put(&path,encoded_ci.into()).await.unwrap();
                                    },
                                    _ => panic!("Cannot register a component in a state different than BUILDING"),
                                }
                        }
                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                    }
                }
                _ => unreachable!(),
            }
        })
    }

    fn start(&self) -> (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {
        task::block_on(async {
            let (s, r) = async_std::sync::channel::<()>(1);
            let selector = zenoh::Selector::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
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
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci =
                                bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec())
                                    .unwrap();
                            match ci.status {
                                zrpc::ComponentStatus::REGISTERED => {
                                    ci.status = zrpc::ComponentStatus::SERVING;
                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                    let path = zenoh::Path::try_from(format!(
                                        "/this/is/generated/Hello/instance/{}/state",
                                        self.instance_uuid()
                                    ))
                                    .unwrap();
                                    ws.put(&path, encoded_ci.into()).await.unwrap();
                                    let server = self.clone();
                                    let h = async_std::task::spawn(async move {
                                        server.serve(r);
                                    });
                                    (s, h)
                                }
                                _ => panic!(
                                    "Cannot work a component in a state different than ANNOUNCED"
                                ),
                            }
                        }
                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                    }
                }
                _ => unreachable!(),
            }
        })
    }

    fn serve(&self, stop: async_std::sync::Receiver<()>) {
        task::block_on(async {
            let selector = zenoh::Selector::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
            let ws = self.z.workspace(None).await.unwrap();
            let mut ds = ws.get(&selector).await.unwrap();
            let mut data = Vec::new();
            // let mut ser = &self.server;
            // let arc_ser = Arc::new(ser);
            while let Some(d) = ds.next().await {
                data.push(d)
            }
            match data.len() {
                0 => panic!("This component state is not present in Zenoh!!"),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let ci = bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec())
                                .unwrap();
                            match ci.status {
                                zrpc::ComponentStatus::SERVING => {
                                    let path = zenoh::Path::try_from(format!(
                                        "/this/is/generated/Hello/instance/{}/eval",
                                        self.instance_uuid()
                                    ))
                                    .unwrap();
                                    let mut rcv =
                                        ws.register_eval(&path.clone().into()).await.unwrap();
                                    let rcv_loop = async {
                                        loop {
                                            let get_request = rcv.next().await.unwrap();
                                            let base64_req = get_request
                                                .selector
                                                .properties
                                                .get("req")
                                                .cloned()
                                                .unwrap();
                                            let b64_bytes = base64::decode(base64_req).unwrap();
                                            let js_req = str::from_utf8(&b64_bytes).unwrap();
                                            let req = serde_json::from_str::<HelloRequest>(&js_req)
                                                .unwrap();

                                            let gr = get_request.clone();
                                            // let inner_ser = arc_ser.clone();
                                            let mut ser = self.server.clone();
                                            let p = path.clone();

                                            task::spawn(async move {
                                                match req {
                                                    HelloRequest::Hello { name } => {
                                                        //let ser = self.server.clone();
                                                        let resp =
                                                            HelloResponse::Hello(ser.hello(name));
                                                        let encoded =
                                                            bincode::serialize(&resp).unwrap();
                                                        gr.reply(p, encoded.into()).await;
                                                    }
                                                    HelloRequest::Add => {
                                                        let resp = HelloResponse::Add(ser.add());
                                                        let encoded =
                                                            bincode::serialize(&resp).unwrap();
                                                        gr.reply(p, encoded.into()).await;
                                                    }
                                                }
                                            });
                                        }
                                    };
                                    rcv_loop.race(stop.recv()).await.unwrap();
                                }
                                _ => panic!("State is not WORK, serve called directly?"),
                            }
                        }
                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                    }
                }
                _ => unreachable!(),
            }
        });
    }

    fn stop(&self, stop: async_std::sync::Sender<()>) {
        task::block_on(async {
            let selector = zenoh::Selector::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
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
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci =
                                bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec())
                                    .unwrap();
                            match ci.status {
                                zrpc::ComponentStatus::SERVING => {
                                    ci.status = zrpc::ComponentStatus::REGISTERED;
                                    let encoded_ci = bincode::serialize(&ci).unwrap();
                                    let path = zenoh::Path::try_from(format!(
                                        "/this/is/generated/Hello/instance/{}/state",
                                        self.instance_uuid()
                                    ))
                                    .unwrap();
                                    ws.put(&path, encoded_ci.into()).await.unwrap();
                                    // Here we stop the serve
                                    stop.send(()).await;
                                }
                                _ => panic!(
                                    "Cannot unwork a component in a state different than WORK"
                                ),
                            }
                        }
                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                    }
                }
                _ => unreachable!(),
            }
        })
    }

    fn unregister(&self) {
        task::block_on(async {
            let selector = zenoh::Selector::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
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
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci =
                                bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec())
                                    .unwrap();
                            match ci.status {
                                    zrpc::ComponentStatus::REGISTERED => {
                                        ci.status = zrpc::ComponentStatus::HALTED;
                                        let encoded_ci = bincode::serialize(&ci).unwrap();
                                        let path = zenoh::Path::try_from(format!(
                                            "/this/is/generated/Hello/instance/{}/state",
                                            self.instance_uuid())).unwrap();
                                        ws.put(&path,encoded_ci.into()).await.unwrap();
                                        // Here we should stop the serve
                                    },
                                    _ => panic!("Cannot unregister a component in a state different than UNANNOUNCED"),
                                }
                        }
                        _ => panic!("Component state is expected to be RAW in Zenoh!!"),
                    }
                }
                _ => unreachable!(),
            }
        })
    }

    fn disconnect(self) {
        task::block_on(async {
            let ws = self.z.workspace(None).await.unwrap();
            let path = zenoh::Path::try_from(format!(
                "/this/is/generated/Hello/instance/{}/state",
                self.instance_uuid()
            ))
            .unwrap();
            ws.delete(&path).await.unwrap();
        })
    }
}

/// The request sent over the wire from the client to the server.
#[derive(Debug, Serialize, Deserialize)]
pub enum HelloRequest {
    Hello { name: String },
    Add,
}

/// The response sent over the wire from the server to the client.
#[derive(Debug, Serialize, Deserialize)]
pub enum HelloResponse {
    Hello(String),
    Add(u64),
}

#[derive(Clone)]
struct HelloZService {
    pub ser_name: String,
    pub counter: Arc<Mutex<u64>>,
}

impl Hello for HelloZService {
    fn hello(&self, name: String) -> String {
        task::block_on(async move {
            let res = format!("Hello {}!, you are connected to {}", name, self.ser_name);
            res
        })
    }

    fn add(&mut self) -> u64 {
        task::block_on(async move {
            let mut guard = self.counter.lock().await;
            *guard += 1;
            *guard
        })
    }
}

#[allow(unused)]
/// The client stub that makes RPC calls to the server. Exposes a Future interface.
#[derive(Clone, Debug)]
pub struct HelloClient<C = zrpc::ZClientChannel<HelloRequest, HelloResponse>> {
    ch: C,
    server_uuid: Uuid,
    // phantom : PhantomData<&'a ()>
}

impl HelloClient {
    pub fn new(z: Arc<zenoh::Zenoh>, instance_id: Uuid) -> HelloClient {
        let new_client = zrpc::ZClientChannel::new(
            z,
            "/this/is/generated/Hello/instance".to_string(),
            Some(instance_id),
        );
        HelloClient {
            ch: new_client,
            server_uuid: instance_id,
            // phantom : PhantomData,
        }
    }

    pub fn get_server_uuid(&self) -> Uuid {
        self.server_uuid
    }

    pub fn find_local_servers(
        z: Arc<zenoh::Zenoh>,
    ) -> impl std::future::Future<Output = std::io::Result<Vec<Uuid>>> + 'static {
        async move {
            let ws = z.workspace(None).await.unwrap();
            let zsession = z.session();
            let zinfo = zsession.info().await;
            let rid = zinfo
                .get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY)
                .unwrap()
                .split(',')
                .collect::<Vec<_>>()[0]
                .to_uppercase();

            let selector =
                zenoh::Selector::try_from("/this/is/generated/Hello/instance/*/state".to_string())
                    .unwrap();
            let mut ds = ws.get(&selector).await.unwrap();
            let mut servers = Vec::new();

            while let Some(d) = ds.next().await {
                match d.value {
                    zenoh::Value::Raw(_, buf) => {
                        let ca =
                            bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec()).unwrap();
                        if ca.routerid == rid {
                            servers.push(ca.uuid);
                        }
                    }
                    _ => {
                        return Err(std::io::Error::new(
                            std::io::ErrorKind::InvalidData,
                            "Component Advertisement is not encoded in RAW".to_string(),
                        ))
                    }
                }
            }
            std::result::Result::Ok(servers)
        }
    }

    pub fn find_servers(
        z: Arc<zenoh::Zenoh>,
    ) -> impl std::future::Future<Output = std::io::Result<Vec<Uuid>>> + 'static {
        async move {
            let ws = z.workspace(None).await.unwrap();
            let selector =
                zenoh::Selector::try_from("/this/is/generated/Hello/instance/*/state".to_string())
                    .unwrap();
            let mut ds = ws.get(&selector).await.unwrap();
            let mut servers = Vec::new();

            while let Some(d) = ds.next().await {
                match d.value {
                    zenoh::Value::Raw(_, buf) => {
                        let ca =
                            bincode::deserialize::<zrpc::ComponentState>(&buf.to_vec()).unwrap();
                        servers.push(ca.uuid);
                    }
                    _ => {
                        return Err(std::io::Error::new(
                            std::io::ErrorKind::InvalidData,
                            "Component Advertisement is not encoded in RAW".to_string(),
                        ))
                    }
                }
            }
            std::result::Result::Ok(servers)
        }
    }
}

impl HelloClient {
    #[allow(unused)]
    pub fn hello(
        &self,
        name: String,
    ) -> impl std::future::Future<Output = std::io::Result<String>> + '_ {
        let request = HelloRequest::Hello { name };
        // Timeout is implemented here
        async move {
            match self.ch.verify_server().await {
                Ok(b) => match b {
                    false => Err(std::io::Error::new(
                        std::io::ErrorKind::PermissionDenied,
                        "Server is not available".to_string(),
                    )),
                    true => {
                        let resp = self.ch.call_fun(request);
                        let dur = Duration::from_secs(10);
                        match async_std::future::timeout(dur, resp).await {
                            Ok(r) => match r {
                                Ok(zr) => match zr {
                                    HelloResponse::Hello(msg) => std::result::Result::Ok(msg),
                                    _ => ::std::rt::begin_panic(
                                        "internal error: entered unreachable code",
                                    ),
                                },
                                Err(e) => Err(e),
                            },
                            Err(e) => Err(std::io::Error::new(
                                std::io::ErrorKind::TimedOut,
                                format!("{}", e),
                            )),
                        }
                    }
                },
                Err(e) => Err(e),
            }
        }
    }

    #[allow(unused)]
    pub fn add(&self) -> impl std::future::Future<Output = std::io::Result<u64>> + '_ {
        let request = HelloRequest::Add;
        // Timeout is implemented here
        async move {
            match self.ch.verify_server().await {
                Ok(b) => match b {
                    false => Err(std::io::Error::new(
                        std::io::ErrorKind::PermissionDenied,
                        "Server is not available".to_string(),
                    )),
                    true => {
                        let resp = self.ch.call_fun(request);
                        let dur = Duration::from_secs(10);
                        match async_std::future::timeout(dur, resp).await {
                            Ok(r) => match r {
                                Ok(zr) => match zr {
                                    HelloResponse::Add(msg) => std::result::Result::Ok(msg),
                                    _ => ::std::rt::begin_panic(
                                        "internal error: entered unreachable code",
                                    ),
                                },
                                Err(e) => Err(e),
                            },
                            Err(e) => Err(std::io::Error::new(
                                std::io::ErrorKind::TimedOut,
                                format!("{}", e),
                            )),
                        }
                    }
                },
                Err(e) => Err(e),
            }
        }
    }
}

#[async_std::main]
async fn main() {
    println!("HelloWorld!");

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
    let mut server = service.get_hello_server(z);
    let instance_id = server.instance_uuid();
    let client = HelloClient::new(zenoh.clone(), instance_id);

    server.connect(); //instance UUID is generated at this point

    server.initialize();
    server.register();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    // this returns an error as the server is not ready
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let (s, handle) = server.start();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    task::sleep(Duration::from_secs(1)).await;
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let hello = client.hello("client_two".to_string()).await;
    println!("Res is: {:?}", hello);

    let hello = client.add().await;
    println!("Res is: {:?}", hello);

    let hello = client.add().await;
    println!("Res is: {:?}", hello);

    let hello = client.add().await;
    println!("Res is: {:?}", hello);

    server.stop(s);

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    server.unregister();
    server.disconnect();

    handle.await;

    // this returns an error as the server is not there
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);
}
