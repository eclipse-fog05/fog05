
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
use std::unimplemented;

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
                let ws = self.z.workspace(None).await.unwrap();
                let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/state", self.server.instance_uuid())).unwrap();
                ws.put(
                    &path.into(),
                    Value::Json(r#"{"state"="halted"}"#.to_string()),
                    ).await.unwrap();
            }
        )
    }

    fn authenticate(&self){
        unimplemented!("Not yet..");
    }

    fn register(&self){
        unimplemented!("Not yet..");
    }

    fn announce(&self){
        unimplemented!("Not yet..");
    }

    fn work(&self){
        self.serve()
    }


    fn serve(
        &self
     )
    {
        task::block_on(async {
            let ws = self.z.workspace(None).await.unwrap();
            let path = zenoh::Path::try_from(format!("/this/is/generated/instance/{}/eval", self.server.instance_uuid())).unwrap();
            let mut rcv = ws.register_eval(&path.clone().into()).await.unwrap();
            // println!("Register eval");
            loop {
                let get_request = rcv.next().await.unwrap();
                // println!("ZServe GetRequest: {:?}", get_request.selector);
                let base64_req = get_request.selector.properties.get("req").cloned().unwrap();
                let b64_bytes = base64::decode(base64_req).unwrap();
                let js_req = str::from_utf8(&b64_bytes).unwrap();
                let req = serde_json::from_str::<HelloRequest>(&js_req).unwrap();
                // println!("ZServe Request: {:?}", req);
                match req {
                    HelloRequest::Hello { name } => {
                        let resp = HelloResponse::Hello(Hello::hello(self.server.clone(), name));
                        let encoded = bincode::serialize(&resp).unwrap();
                        //let p = zenoh::Path::try_from(get_request.selector.path_expr.as_str()).unwrap();
                        // println!("ZServe Response: {:?}", encoded);
                        get_request.reply(path.clone().into(), encoded.into()).await;
                    }
                }
            }
        });
    }

    fn unwork(&self){
        unimplemented!("Not yet..");
    }

    fn unannounce(&self){
        unimplemented!("Not yet..");
    }

    fn unregister(&self){
        unimplemented!("Not yet..");
    }

    fn disconnect(self){
        unimplemented!("Not yet..");
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
        let new_client = fog05_zservice::ZClientChannel::new(ws, format!("/this/is/generated/instance/{}/eval", instance_id));
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
        &mut self,
        name: String,
    ) -> impl std::future::Future<Output = std::io::Result<String>> + '_{
        let request = HelloRequest::Hello { name };
        // Timeout is implemented here
        let resp = self.ch.call_fun(request);
        async move {
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

#[async_std::main]
async fn main() {
    println!("HelloWorld!");


    let zenoh = Arc::new(Zenoh::new(zenoh::config::client(Some(format!("tcp/127.0.0.1:7447").to_string()))).await.unwrap());
    let ws = Arc::new(zenoh.workspace(None).await.unwrap());

    let service = HelloZService("test service".to_string());


    let z = zenoh.clone();
    let server = service.get_server(z);
    server.connect();

    let handle = task::spawn(async move {
        server.serve();
    });

    let instance_id = Uuid::from_str("00000000-0000-0000-0000-000000000000").unwrap();
    let mut client = HelloClient::new(ws, instance_id);
    task::sleep(Duration::from_secs(1)).await;
    let hello = client.hello("client".to_string()).await;
    println!("Res is: {:?}", hello);

    let hello = client.hello("client_two".to_string()).await;
    println!("Res is: {:?}", hello);


    handle.await;


}

