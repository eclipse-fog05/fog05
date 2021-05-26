#![feature(prelude_import)]
#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]
#[prelude_import]
extern crate serde;
extern crate std;

use std::prelude::v1::*;

use async_std::prelude::FutureExt;
use async_std::sync::{Arc, Mutex};
use async_std::task;
use futures::prelude::*;
use std::convert::TryFrom;
use std::str;
use std::time::Duration;
use uuid::Uuid;
use zenoh::*;

use serde::{Deserialize, Serialize};
use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc::ZNServe;

pub trait Hello: Clone {
    fn hello(
        &self,
        name: String,
    ) -> ::core::pin::Pin<Box<dyn ::core::future::Future<Output = String> + core::marker::Send + '_>>;
    fn add(
        &mut self,
    ) -> ::core::pin::Pin<Box<dyn ::core::future::Future<Output = u64> + core::marker::Send + '_>>;
    /// Returns the server object
    fn get_hello_server(
        self,
        z: async_std::sync::Arc<zenoh::net::Session>,
        id: Option<uuid::Uuid>,
    ) -> ServeHello<Self> {
        let id = id.unwrap_or(Uuid::new_v4());
        ServeHello::new(z, self, id)
    }
}

#[derive(Clone, Debug)]
pub struct ServeHello<S> {
    z: async_std::sync::Arc<zenoh::net::Session>,
    server: S,
    instance_id: uuid::Uuid,
    state: async_std::sync::Arc<async_std::sync::RwLock<zrpc::ComponentState>>,
}

impl<S> ServeHello<S> {
    pub fn new(z: async_std::sync::Arc<zenoh::net::Session>, server: S, id: uuid::Uuid) -> Self {
        let ci = zrpc::ComponentState {
            uuid: id,
            name: "HelloService".to_string(),
            routerid: "".to_string(),
            peerid: "".to_string(),
            status: zrpc::ComponentStatus::HALTED,
        };
        Self {
            z,
            server,
            instance_id: id,
            state: async_std::sync::Arc::new(async_std::sync::RwLock::new(ci)),
        }
    }
}
impl<S> zrpc::ZNServe<HelloRequest> for ServeHello<S>
where
    S: Hello + Send + 'static,
{
    type Resp = HelloResponse;
    fn instance_uuid(&self) -> uuid::Uuid {
        self.instance_id
    }

    #[allow(unused)]
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn connect(
        &'_ self,
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
        async fn __connect<S>(
            _self: &ServeHello<S>,
        ) -> ZRPCResult<(
            async_std::channel::Sender<()>,
            async_std::task::JoinHandle<ZRPCResult<()>>,
        )>
        where
            S: Hello + Send + 'static,
        {
            let zinfo = _self.z.info().await;
            let pid = zinfo
                .get(&zenoh::net::info::ZN_INFO_PID_KEY)
                .ok_or(ZRPCError::MissingValue)?
                .to_uppercase();
            let rid = match zinfo.get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY) {
                Some(r_info) => {
                    if r_info != "" {
                        r_info.split(",").collect::<Vec<_>>()[0].to_uppercase()
                    } else {
                        "".to_string()
                    }
                }
                None => "".to_string(),
            };
            let mut ci = _self.state.write().await;
            ci.peerid = pid.clone().to_uppercase();
            drop(ci);
            let (s, r) = async_std::channel::bounded::<()>(1);
            let zsession = _self.z.clone();
            let state = _self.state.clone();
            let path = zenoh::Path::try_from(format!(
                "/znservice/Hello/2967c40b-a9a4-4330-b5f6-e0315b2356a9/{}/state",
                _self.instance_uuid()
            ))?;

            let h = async_std::task::spawn(async move {
                let mut queryable = zsession
                    .declare_queryable(&path.clone().into(), zenoh::net::queryable::EVAL)
                    .await?;

                let rcv_loop = async {
                    loop {
                        let query = queryable
                            .stream()
                            .next()
                            .await
                            .ok_or_else(|| async_std::channel::RecvError)?;
                        let ci = state.read().await;
                        let data = zrpc::serialize::serialize_state(&*ci)
                            .map_err(|_| async_std::channel::RecvError)?;
                        drop(ci);
                        let sample = zenoh::net::Sample {
                            res_name: path.to_string().clone(),
                            payload: data.into(),
                            data_info: Some(zenoh::net::protocol::proto::DataInfo {
                                source_id: None,
                                source_sn: None,
                                first_router_id: None,
                                first_router_sn: None,
                                timestamp: Some(uhlc::Timestamp::new(
                                    Default::default(),
                                    uhlc::ID::new(16, [1u8; uhlc::ID::MAX_SIZE]),
                                )),
                                kind: None,
                                encoding: None,
                            }),
                        };

                        query.reply(sample).await;
                    }
                };

                rcv_loop
                    .race(r.recv())
                    .await
                    .map_err(|e| ZRPCError::Error(format!("{}", e)))
            });
            Ok((s, h))
        }
        Box::pin(__connect(self))
    }
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn initialize(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        async fn __initialize<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let mut ci = _self.state.write().await;
            match ci.status {
                zrpc::ComponentStatus::HALTED => {
                    ci.status = zrpc::ComponentStatus::INITIALIZING;
                    Ok(())
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "Cannot initialize a component in a state different than HALTED".to_string(),
                )),
            }
        }
        Box::pin(__initialize(self))
    }
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn register(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        async fn __register<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let mut ci = _self.state.write().await;
            match ci.status {
                zrpc::ComponentStatus::INITIALIZING => {
                    ci.status = zrpc::ComponentStatus::REGISTERED;
                    Ok(())
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "Cannot register a component in a state different than INITIALIZING"
                        .to_string(),
                )),
            }
        }
        Box::pin(__register(self))
    }
    #[allow(
        clippy::type_complexity,
        clippy::manual_async_fn,
        clippy::needless_question_mark
    )]
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
            let barrier = async_std::sync::Arc::new(async_std::sync::Barrier::new(2));
            let ci = _self.state.read().await;
            match ci.status {
                zrpc::ComponentStatus::REGISTERED => {
                    drop(ci);

                    let server = _self.clone();
                    let b = barrier.clone();
                    let h = async_std::task::spawn_blocking(move || {
                        async_std::task::block_on(async { server.serve(r, b).await })
                    });

                    barrier.wait().await;

                    let mut ci = _self.state.write().await;
                    ci.status = zrpc::ComponentStatus::SERVING;
                    drop(ci);

                    Ok((s, h))
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "Cannot start a component in a state different than REGISTERED".to_string(),
                )),
            }
        }
        Box::pin(__start(self))
    }
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn serve(
        &self,
        stop: async_std::channel::Receiver<()>,
        barrier: async_std::sync::Arc<async_std::sync::Barrier>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        async fn __serve<S>(
            _self: &ServeHello<S>,
            _stop: async_std::channel::Receiver<()>,
            _barrier: async_std::sync::Arc<async_std::sync::Barrier>,
        ) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let ci = _self.state.read().await;
            match ci.status {
                zrpc::ComponentStatus::REGISTERED => {
                    drop(ci);
                    let path = zenoh::Path::try_from(format!(
                        "/znservice/Hello/2967c40b-a9a4-4330-b5f6-e0315b2356a9/{}/eval",
                        _self.instance_uuid()
                    ))?;

                    let mut queryable = _self
                        .z
                        .declare_queryable(&path.clone().into(), zenoh::net::queryable::EVAL)
                        .await?;
                    _barrier.wait().await;
                    let rcv_loop = async {
                        loop {
                            let query = queryable
                                .stream()
                                .next()
                                .await
                                .ok_or_else(|| async_std::channel::RecvError)?;

                            let base64_req = query.predicate.clone();
                            let b64_bytes = base64::decode(base64_req)
                                .map_err(|_| async_std::channel::RecvError)?;
                            let req =
                                zrpc::serialize::deserialize_request::<HelloRequest>(&b64_bytes)
                                    .map_err(|_| async_std::channel::RecvError)?;

                            let mut ser = _self.server.clone();
                            let p = path.clone();
                            match req {
                                HelloRequest::Hello { name } => {
                                    let resp = HelloResponse::Hello(ser.hello(name).await);
                                    let encoded = zrpc::serialize::serialize_response(&resp)
                                        .map_err(|_| async_std::channel::RecvError)?;
                                    let sample = zenoh::net::Sample {
                                        res_name: p.to_string().clone(),
                                        payload: encoded.into(),
                                        data_info: Some(zenoh::net::protocol::proto::DataInfo {
                                            source_id: None,
                                            source_sn: None,
                                            first_router_id: None,
                                            first_router_sn: None,
                                            timestamp: Some(uhlc::Timestamp::new(
                                                Default::default(),
                                                uhlc::ID::new(16, [1u8; uhlc::ID::MAX_SIZE]),
                                            )),
                                            kind: None,
                                            encoding: None,
                                        }),
                                    };
                                    query.reply(sample).await;
                                }
                                HelloRequest::Add {} => {
                                    let resp = HelloResponse::Add(ser.add().await);
                                    let encoded = zrpc::serialize::serialize_response(&resp)
                                        .map_err(|_| async_std::channel::RecvError)?;
                                    let sample = zenoh::net::Sample {
                                        res_name: p.to_string().clone(),
                                        payload: encoded.into(),
                                        data_info: Some(zenoh::net::protocol::proto::DataInfo {
                                            source_id: None,
                                            source_sn: None,
                                            first_router_id: None,
                                            first_router_sn: None,
                                            timestamp: Some(uhlc::Timestamp::new(
                                                Default::default(),
                                                uhlc::ID::new(16, [1u8; uhlc::ID::MAX_SIZE]),
                                            )),
                                            kind: None,
                                            encoding: None,
                                        }),
                                    };
                                    query.reply(sample).await;
                                }
                            }
                        }
                    };

                    let res = rcv_loop
                        .race(_stop.recv())
                        .await
                        .map_err(|e| ZRPCError::Error(format!("{}", e)));
                    res
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "State is not WORK, serve called directly? serve is called by calling work!"
                        .to_string(),
                )),
            }
        }
        let res = __serve(self, stop, barrier);
        Box::pin(res)
    }
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn stop(
        &self,
        stop: async_std::channel::Sender<()>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        async fn __stop<S>(
            _self: &ServeHello<S>,
            _stop: async_std::channel::Sender<()>,
        ) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let mut ci = _self.state.write().await;
            match ci.status {
                zrpc::ComponentStatus::SERVING => {
                    ci.status = zrpc::ComponentStatus::REGISTERED;
                    drop(ci);
                    Ok(_stop.send(()).await?)
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "Cannot stop a component in a state different than WORK".to_string(),
                )),
            }
        }
        Box::pin(__stop(self, stop))
    }
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn unregister(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        async fn __unregister<S>(_self: &ServeHello<S>) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let mut ci = _self.state.write().await;
            match ci.status {
                zrpc::ComponentStatus::REGISTERED => {
                    ci.status = zrpc::ComponentStatus::HALTED;
                    Ok(())
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "Cannot unregister a component in a state different than REGISTERED"
                        .to_string(),
                )),
            }
        }
        Box::pin(__unregister(self))
    }
    #[allow(clippy::type_complexity, clippy::manual_async_fn)]
    fn disconnect(
        &self,
        stop: async_std::channel::Sender<()>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>> {
        async fn __disconnect<S>(
            _self: &ServeHello<S>,
            _stop: async_std::channel::Sender<()>,
        ) -> ZRPCResult<()>
        where
            S: Hello + Send + 'static,
        {
            let mut ci = _self.state.write().await;
            match ci.status {
                zrpc::ComponentStatus::HALTED => {
                    ci.status = zrpc::ComponentStatus::HALTED;
                    drop(ci);
                    Ok(_stop.send(()).await?)
                }
                _ => Err(ZRPCError::StateTransitionNotAllowed(
                    "Cannot disconnect a component in a state different than HALTED".to_string(),
                )),
            }
        }
        Box::pin(__disconnect(self, stop))
    }
}

/// The request sent over the wire from the client to the server.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum HelloRequest {
    Hello { name: String },
    Add {},
}

/// The response sent over the wire from the server to the client.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum HelloResponse {
    Hello(String),
    Add(u64),
}

#[allow(unused)]
#[derive(Clone, Debug)]
pub struct HelloClient<C = zrpc::ZNClientChannel<HelloRequest, HelloResponse>> {
    ch: C,
    server_uuid: Uuid,
}

impl HelloClient {
    pub fn new(
        z: async_std::sync::Arc<zenoh::net::Session>,
        instance_id: uuid::Uuid,
    ) -> HelloClient {
        let new_client = zrpc::ZNClientChannel::new(
            z,
            "/znservice/Hello/2967c40b-a9a4-4330-b5f6-e0315b2356a9/".to_string(),
            Some(instance_id),
        );
        HelloClient {
            ch: new_client,
            server_uuid: instance_id,
        }
    }
    pub fn get_server_uuid(&self) -> Uuid {
        self.server_uuid
    }
    pub fn find_servers(
        z: async_std::sync::Arc<zenoh::net::Session>,
    ) -> impl std::future::Future<Output = ZRPCResult<Vec<uuid::Uuid>>> + 'static {
        async move {
            let reskey = net::ResKey::RId(
                z.declare_resource(&net::ResKey::RName(
                    "/znservice/Hello/2967c40b-a9a4-4330-b5f6-e0315b2356a9/*/state".to_string(),
                ))
                .await?,
            );
            let mut servers = Vec::new();
            let mut replies = z
                .query(
                    &reskey,
                    "",
                    net::QueryTarget::default(),
                    net::QueryConsolidation::default(),
                )
                .await?;
            while let Some(d) = replies.next().await {
                let buf = d.data.payload;
                let ca = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                servers.push(ca.uuid);
            }
            Ok(servers)
        }
    }
    pub fn find_local_servers(
        z: async_std::sync::Arc<zenoh::net::Session>,
    ) -> impl std::future::Future<Output = ZRPCResult<Vec<uuid::Uuid>>> + 'static {
        async move {
            let reskey = net::ResKey::RId(
                z.declare_resource(&net::ResKey::RName(
                    "/znservice/Hello/2967c40b-a9a4-4330-b5f6-e0315b2356a9/*/state".to_string(),
                ))
                .await?,
            );
            let mut servers = Vec::new();
            let mut replies = z
                .query(
                    &reskey,
                    "",
                    net::QueryTarget::default(),
                    net::QueryConsolidation::default(),
                )
                .await?;
            while let Some(d) = replies.next().await {
                let buf = d.data.payload;
                let ca = zrpc::serialize::deserialize_state::<zrpc::ComponentState>(&buf.to_vec())?;
                servers.push(ca);
            }
            let zinfo = z.info().await;
            let rid = match zinfo.get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY) {
                Some(r_info) => {
                    if r_info != "" {
                        r_info.split(",").collect::<Vec<_>>()[0].to_uppercase()
                    } else {
                        return Err(ZRPCError::NoRouter);
                    }
                }
                None => return Err(ZRPCError::NoRouter),
            };

            let reskey = net::ResKey::RId(
                z.declare_resource(&net::ResKey::RName(format!("/@/router/{}", rid)))
                    .await?,
            );
            let rdata: Vec<zenoh::net::Reply> = z
                .query(
                    &reskey,
                    "",
                    net::QueryTarget::default(),
                    net::QueryConsolidation::default(),
                )
                .await?
                .collect()
                .await;
            if rdata.len() == 0 {
                return Err(ZRPCError::NotFound);
            }
            let router_data = &rdata[0].data;
            let reply_encoding = if let Some(info) = router_data.data_info.clone() {
                info.encoding
                    .unwrap_or(zenoh::net::protocol::proto::encoding::APP_OCTET_STREAM)
            } else {
                zenoh::net::protocol::proto::encoding::APP_OCTET_STREAM
            };
            let router_value = zenoh::Value::decode(reply_encoding, router_data.payload.clone())?;
            match router_value {
                zenoh::Value::Json(sv) => {
                    let ri = zrpc::serialize::deserialize_router_info(&sv.as_bytes())?;
                    let r: Vec<Uuid> = servers
                        .into_iter()
                        .filter_map(|ci| {
                            let pid = String::from(&ci.peerid).to_uppercase();
                            let mut it = ri.clone().sessions.into_iter();
                            let f = it.find(|x| x.peer == pid.clone());
                            if f.is_none() {
                                None
                            } else {
                                Some(ci.uuid)
                            }
                        })
                        .collect();

                    Ok(r)
                }
                _ => Err(ZRPCError::ZenohError(
                    "Router information is not encoded in JSON".to_string(),
                )),
            }
        }
    }
}
impl HelloClient {
    pub fn verify_server(&self) -> impl std::future::Future<Output = ZRPCResult<bool>> + '_ {
        async move { self.ch.verify_server().await }
    }
    #[allow(unused, clippy::manual_async_fn)]
    pub fn hello(
        &self,
        name: String,
    ) -> impl std::future::Future<Output = ZRPCResult<String>> + '_ {
        let request = HelloRequest::Hello { name };
        async move {
            let resp = self.ch.call_fun(request);
            let dur = std::time::Duration::from_secs(60u16 as u64);
            match async_std::future::timeout(dur, resp).await {
                Ok(r) => match r {
                    Ok(zr) => match zr {
                        HelloResponse::Hello(msg) => std::result::Result::Ok(msg),
                        _ => Err(ZRPCError::Unreachable),
                    },
                    Err(e) => Err(e),
                },
                Err(e) => Err(ZRPCError::TimedOut),
            }
        }
    }
    #[allow(unused, clippy::manual_async_fn)]
    pub fn add(&self) -> impl std::future::Future<Output = ZRPCResult<u64>> + '_ {
        let request = HelloRequest::Add {};
        async move {
            let resp = self.ch.call_fun(request);
            let dur = std::time::Duration::from_secs(60u16 as u64);
            match async_std::future::timeout(dur, resp).await {
                Ok(r) => match r {
                    Ok(zr) => match zr {
                        HelloResponse::Add(msg) => std::result::Result::Ok(msg),
                        _ => Err(ZRPCError::Unreachable),
                    },
                    Err(e) => Err(e),
                },
                Err(e) => Err(ZRPCError::TimedOut),
            }
        }
    }
}

#[derive(Clone, Debug)]
struct HelloZService {
    pub ser_name: String,
    pub counter: Arc<Mutex<u64>>,
}

impl Hello for HelloZService {
    #[allow(unused, clippy::manual_async_fn)]
    fn hello(
        &self,
        name: String,
    ) -> ::core::pin::Pin<Box<dyn ::core::future::Future<Output = String> + core::marker::Send + '_>>
    {
        async fn __hello(_self: &HelloZService, name: String) -> String {
            {
                format!("Hello {}!, you are connected to {}", name, _self.ser_name)
            }
        }
        Box::pin(__hello(self, name))
    }
    #[allow(unused, clippy::manual_async_fn)]
    fn add(
        &mut self,
    ) -> ::core::pin::Pin<Box<dyn ::core::future::Future<Output = u64> + core::marker::Send + '_>>
    {
        async fn __add(mut _self: &HelloZService) -> u64 {
            let mut guard = _self.counter.lock().await;
            *guard += 1;
            *guard
        }
        Box::pin(__add(self))
    }
}

#[async_std::main]
async fn main() {
    {
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
        server.unregister().await.unwrap();
        server.disconnect(stopper).await.unwrap();
        handle.await.unwrap();
    }
}
