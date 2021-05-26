#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]
#![feature(libstd_sys_internals)]
#![feature(print_internals)]
#![feature(fmt_internals)]
#![feature(prelude_import)]
#![feature(async_closure)]
#![feature(associated_type_bounds)]
#[prelude_import]
#[macro_use]
extern crate std;
extern crate base64;
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
use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
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

    fn connect(
        &'_ self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        log::trace!("server connect");
        async fn __connect<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let zsession = _self.z.session();
            let zinfo = zsession.info().await;
            let pid = zinfo
                .get(&zenoh::net::info::ZN_INFO_PID_KEY)
                .ok_or(ZRPCError::MissingValue)?
                .to_uppercase();
            let rid = zinfo
                .get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY)
                .ok_or(ZRPCError::MissingValue)?
                .split(',')
                .collect::<Vec<_>>()[0]
                .to_uppercase();
            let ws = _self.z.workspace(None).await?;

            let component_info = zrpc::ComponentState {
                uuid: _self.instance_uuid(),
                name: "Hello".to_string(),
                routerid: rid.clone().to_uppercase(),
                peerid: pid.clone().to_uppercase(),
                status: zrpc::ComponentStatus::HALTED,
            };
            let encoded_ci = zrpc::serialize::serialize_state(&component_info)?;
            let path = zenoh::Path::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            Ok(ws.put(&path, encoded_ci.into()).await?)
        }
        Box::pin(__connect(self))
    }

    fn initialize(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        log::trace!("server initialize");
        async fn __initialize<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let selector = zenoh::Selector::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            let ws = _self.z.workspace(None).await?;
            let ds = ws.get(&selector).await?;
            let data: Vec<zenoh::Data> = ds.collect().await;
            match data.len() {
                0 => Err(ZRPCError::NotFound),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                                &buf.to_vec(),
                            )?;
                            match ci.status {
                                    zrpc::ComponentStatus::HALTED => {
                                        ci.status = zrpc::ComponentStatus::INITIALIZING;
                                        let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                        let path = zenoh::Path::try_from(format!("/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                                        _self.instance_uuid()))?;
                                        Ok(ws.put(&path,encoded_ci.into()).await?)
                                    },
                                    _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot authenticate a component in a state different than HALTED".to_string())),
                                }
                        }
                        _ => Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        )),
                    }
                }
                _ => Err(ZRPCError::Unreachable),
            }
        }
        Box::pin(__initialize(self))
    }

    fn register(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        log::trace!("server register");
        async fn __register<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let selector = zenoh::Selector::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            let ws = _self.z.workspace(None).await?;
            let ds = ws.get(&selector).await?;
            let data: Vec<zenoh::Data> = ds.collect().await;
            match data.len() {
                0 => Err(ZRPCError::NotFound),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                                &buf.to_vec(),
                            )?;
                            match ci.status {
                                    zrpc::ComponentStatus::INITIALIZING => {
                                        ci.status = zrpc::ComponentStatus::REGISTERED;
                                        let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                        let path = zenoh::Path::try_from(format!("/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                                        _self.instance_uuid()))?;
                                        Ok(ws.put(&path,encoded_ci.into()).await?)
                                    },
                                    _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot authenticate a component in a state different than BUILDING".to_string())),
                                }
                        }
                        _ => Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        )),
                    }
                }
                _ => Err(ZRPCError::Unreachable),
            }
        }
        Box::pin(__register(self))
    }

    fn start(
        &self,
    ) -> ::core::pin::Pin<
        Box<
            dyn std::future::Future<
                    Output = ZRPCResult<(
                        async_std::channel::Sender<()>,
                        async_std::task::JoinHandle<ZRPCResult<()>>,
                    )>,
                > + '_,
        >,
    > {
        log::trace!("server start");
        async fn __start<S>(
            _self: &ServeHello<S>,
        ) -> ZRPCResult<(
            async_std::channel::Sender<()>,
            async_std::task::JoinHandle<ZRPCResult<()>>,
        )>
        where
            S: Hello + Send + 'static,
        {
            let (s, r) = async_std::channel::bounded::<()>(1);
            let selector = zenoh::Selector::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            let ws = _self.z.workspace(None).await?;
            let ds = ws.get(&selector).await?;
            let data: Vec<zenoh::Data> = ds.collect().await;
            match data.len() {
                0 => Err(ZRPCError::NotFound),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                                &buf.to_vec(),
                            )?;
                            match ci.status {
                                zrpc::ComponentStatus::REGISTERED => {
                                    ci.status = zrpc::ComponentStatus::SERVING;
                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                    let path = zenoh::Path::try_from(format!(
                                        "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                                        _self.instance_uuid()
                                    ))?;
                                    ws.put(&path, encoded_ci.into()).await?;
                                    let server = _self.clone();
                                    let h = async_std::task::spawn_blocking(move || {
                                        async_std::task::block_on(async {
                                            server.serve(r).await
                                        })
                                    });
                                    Ok((s, h))
                                }
                                _ =>
                                Err(ZRPCError::StateTransitionNotAllowed("Cannot authenticate a component in a state different than REGISTERED".to_string())),
                            }
                        }
                        _ => Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        )),
                    }
                }
                _ => Err(ZRPCError::Unreachable),
            }
        }
        Box::pin(__start(self))
    }

    fn serve(
        &self,
        stop: async_std::channel::Receiver<()>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        log::trace!("server serve");
        async fn __serve<S>(
            _self: &ServeHello<S>,
            _stop: async_std::channel::Receiver<()>,
        ) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let selector = zenoh::Selector::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            let ws = _self.z.workspace(None).await?;
            let ds = ws.get(&selector).await?;
            let data: Vec<zenoh::Data> = ds.collect().await;
            match data.len() {
                0 => Err(ZRPCError::NotFound),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                                &buf.to_vec(),
                            )?;
                            match ci.status {
                                zrpc::ComponentStatus::SERVING => {
                                    let path = zenoh::Path::try_from(format!(
                                        "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/eval",
                                        _self.instance_uuid()
                                    ))?;
                                    log::trace!("eval registering");
                                    let mut rcv = ws.register_eval(&path.clone().into()).await?;
                                    log::trace!("eval registered");

                                    let rcv_loop = async {
                                        loop {
                                            let get_request = rcv
                                                .next()
                                                .await
                                                .ok_or_else(|| async_std::channel::RecvError)?;
                                            let base64_req = get_request
                                                .selector
                                                .properties
                                                .get("req")
                                                .cloned()
                                                .ok_or_else(|| async_std::channel::RecvError)?;
                                            let b64_bytes = base64::decode(base64_req)
                                                .map_err(|_| async_std::channel::RecvError)?;
                                            let req = zrpc::serialize::deserialize_request::<
                                                HelloRequest,
                                            >(
                                                &b64_bytes
                                            )
                                            .map_err(|_| async_std::channel::RecvError)?;

                                            let gr = get_request.clone();
                                            // let inner_ser = arc_ser.clone();
                                            let mut ser = _self.server.clone();
                                            let p = path.clone();

                                            match req {
                                                HelloRequest::Hello { name } => {
                                                    let resp =
                                                        HelloResponse::Hello(ser.hello(name));
                                                    let encoded =
                                                        zrpc::serialize::serialize_response(&resp)
                                                            .map_err(|_| {
                                                                async_std::channel::RecvError
                                                            })?;
                                                    gr.reply(p, encoded.into()).await;
                                                }
                                                HelloRequest::Add => {
                                                    let resp = HelloResponse::Add(ser.add());
                                                    let encoded =
                                                        zrpc::serialize::serialize_response(&resp)
                                                            .map_err(|_| {
                                                                async_std::channel::RecvError
                                                            })?;
                                                    gr.reply(p, encoded.into()).await;
                                                }
                                            }
                                        }
                                    };
                                    Ok(rcv_loop
                                        .race(_stop.recv())
                                        .await
                                        .map_err(|e| ZRPCError::Error(format!("{}", e)))?)
                                }
                                _ => Err(ZRPCError::StateTransitionNotAllowed(
                                    "State is not WORK, serve called directly?".to_string(),
                                )),
                            }
                        }
                        _ => Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        )),
                    }
                }
                _ => Err(ZRPCError::Unreachable),
            }
        }
        Box::pin(__serve(self, stop))
    }

    fn stop(
        &self,
        stop: async_std::channel::Sender<()>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        log::trace!("server stop");
        async fn __stop<S>(
            _self: &ServeHello<S>,
            _stop: async_std::channel::Sender<()>,
        ) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let selector = zenoh::Selector::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            let ws = _self.z.workspace(None).await?;
            let ds = ws.get(&selector).await?;
            let data: Vec<zenoh::Data> = ds.collect().await;
            match data.len() {
                0 => Err(ZRPCError::NotFound),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                                &buf.to_vec(),
                            )?;
                            match ci.status {
                                zrpc::ComponentStatus::SERVING => {
                                    ci.status = zrpc::ComponentStatus::REGISTERED;
                                    let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                    let path = zenoh::Path::try_from(format!(
                                        "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                                        _self.instance_uuid()
                                    ))?;
                                    ws.put(&path, encoded_ci.into()).await?;
                                    // Here we stop the serve
                                    Ok(_stop.send(()).await?)
                                }
                                _ => Err(ZRPCError::StateTransitionNotAllowed(
                                    "Cannot unwork a component in a state different than WORK"
                                        .to_string(),
                                )),
                            }
                        }
                        _ => Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        )),
                    }
                }
                _ => Err(ZRPCError::Unreachable),
            }
        }
        Box::pin(__stop(self, stop))
    }

    fn unregister(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        log::trace!("server unregister");
        async fn __unregister<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let selector = zenoh::Selector::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            let ws = _self.z.workspace(None).await?;
            let ds = ws.get(&selector).await?;
            let data: Vec<zenoh::Data> = ds.collect().await;
            match data.len() {
                0 => Err(ZRPCError::NotFound),
                1 => {
                    let kv = &data[0];
                    match &kv.value {
                        zenoh::Value::Raw(_, buf) => {
                            let mut ci = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                                &buf.to_vec(),
                            )?;
                            match ci.status {
                                    zrpc::ComponentStatus::REGISTERED => {
                                        ci.status = zrpc::ComponentStatus::HALTED;
                                        let encoded_ci = zrpc::serialize::serialize_state(&ci)?;
                                        let path = zenoh::Path::try_from(format!(
                                            "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                                            _self.instance_uuid()))?;
                                        Ok(ws.put(&path,encoded_ci.into()).await?)
                                        // Here we should stop the serve
                                    },
                                    _ => Err(ZRPCError::StateTransitionNotAllowed("Cannot unregister a component in a state different than UNANNOUNCED".to_string())),
                                }
                        }
                        _ => Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        )),
                    }
                }
                _ => Err(ZRPCError::Unreachable),
            }
        }
        Box::pin(__unregister(self))
    }

    fn disconnect(self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>>>> {
        async fn __disconnect<S>(_self: ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let ws = _self.z.workspace(None).await?;
            let path = zenoh::Path::try_from(format!(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/{}/state",
                _self.instance_uuid()
            ))?;
            Ok(ws.delete(&path).await?)
        }

        Box::pin(__disconnect(self))
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
            "/zservice/Hello/00000000-0000-0000-0000-000000000001".to_string(),
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
    ) -> impl std::future::Future<Output = ZRPCResult<Vec<Uuid>>> + 'static {
        async move {
            let ws = z.workspace(None).await?;
            let zsession = z.session();
            let zinfo = zsession.info().await;
            let rid = zinfo
                .get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY)
                .ok_or(ZRPCError::MissingValue)?
                .split(',')
                .collect::<Vec<_>>()[0]
                .to_uppercase();

            let selector = zenoh::Selector::try_from(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/*/state".to_string(),
            )?;
            let mut ds = ws.get(&selector).await?;
            let mut servers = Vec::new();

            while let Some(d) = ds.next().await {
                match d.value {
                    zenoh::Value::Raw(_, buf) => {
                        let ca = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                            &buf.to_vec(),
                        )?;
                        if ca.routerid == rid {
                            servers.push(ca.uuid);
                        }
                    }
                    _ => {
                        return Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        ))
                    }
                }
            }
            Ok(servers)
        }
    }

    pub fn find_servers(
        z: Arc<zenoh::Zenoh>,
    ) -> impl std::future::Future<Output = ZRPCResult<Vec<Uuid>>> + 'static {
        async move {
            let ws = z.workspace(None).await?;
            let selector = zenoh::Selector::try_from(
                "/zservice/Hello/00000000-0000-0000-0000-000000000001/*/state".to_string(),
            )?;
            let mut ds = ws.get(&selector).await?;
            let mut servers = Vec::new();

            while let Some(d) = ds.next().await {
                match d.value {
                    zenoh::Value::Raw(_, buf) => {
                        let ca = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(
                            &buf.to_vec(),
                        )?;
                        servers.push(ca.uuid);
                    }
                    _ => {
                        return Err(ZRPCError::ZenohError(
                            "Component state is expected to be RAW in Zenoh!!".to_string(),
                        ))
                    }
                }
            }
            Ok(servers)
        }
    }
}

impl HelloClient {
    #[allow(unused)]
    pub fn hello(
        &self,
        name: String,
    ) -> impl std::future::Future<Output = ZRPCResult<String>> + '_ {
        let request = HelloRequest::Hello { name };
        // Timeout is implemented here
        async move {
            match self.ch.verify_server().await {
                Ok(b) => match b {
                    false => Err(ZRPCError::Unavailable),
                    true => {
                        let resp = self.ch.call_fun(request);
                        let dur = Duration::from_secs(10);
                        match async_std::future::timeout(dur, resp).await {
                            Ok(r) => match r {
                                Ok(zr) => match zr {
                                    HelloResponse::Hello(msg) => Ok(msg),
                                    _ => ::std::rt::begin_panic(
                                        "internal error: entered unreachable code",
                                    ),
                                },
                                Err(e) => Err(e),
                            },
                            Err(e) => Err(ZRPCError::TimedOut),
                        }
                    }
                },
                Err(e) => Err(e),
            }
        }
    }

    #[allow(unused)]
    pub fn add(&self) -> impl std::future::Future<Output = ZRPCResult<u64>> + '_ {
        let request = HelloRequest::Add;
        // Timeout is implemented here
        async move {
            match self.ch.verify_server().await {
                Ok(b) => match b {
                    false => Err(ZRPCError::Unavailable),
                    true => {
                        let resp = self.ch.call_fun(request);
                        let dur = Duration::from_secs(10);
                        match async_std::future::timeout(dur, resp).await {
                            Ok(r) => match r {
                                Ok(zr) => match zr {
                                    HelloResponse::Add(msg) => Ok(msg),
                                    _ => ::std::rt::begin_panic(
                                        "internal error: entered unreachable code",
                                    ),
                                },
                                Err(e) => Err(e),
                            },
                            Err(e) => Err(ZRPCError::TimedOut),
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
    env_logger::init();

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
    let server = service.get_hello_server(z);
    let instance_id = server.instance_uuid();
    let client = HelloClient::new(zenoh.clone(), instance_id);

    server.connect().await.unwrap(); //instance UUID is generated at this point

    server.initialize().await.unwrap();
    server.register().await.unwrap();

    let local_servers = HelloClient::find_local_servers(zenoh.clone()).await;
    println!("local_servers: {:?}", local_servers);

    let servers = HelloClient::find_servers(zenoh.clone()).await;
    println!("servers found: {:?}", servers);

    // this returns an error as the server is not ready
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

    let hello = client.hello("client_two".to_string()).await;
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

    // this returns an error as the server is not there
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);
}
