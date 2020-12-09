#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]
#[macro_use]
extern crate std;

use async_std::sync::Arc;
use async_std::task;
use futures::prelude::*;
use std::convert::TryFrom;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};
use structopt::StructOpt;
use zenoh::*;

use async_std::prelude::FutureExt;

use std::str;
use uuid::Uuid;
use zrpc::ZServe;
//importing the macros
use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc_macros::{zserver, zservice};

static DEFAULT_MODE: &str = "client";
static DEFAULT_ROUTER: &str = "tcp/127.0.0.1:7447";
static DEFAULT_INT: &str = "5";
static DEFAULT_DURATION: &str = "60";

#[derive(StructOpt, Debug)]
struct CallArgs {
    /// Config file
    #[structopt(short, long, default_value = DEFAULT_MODE)]
    mode: String,
    #[structopt(short, long, default_value = DEFAULT_ROUTER)]
    router: String,
    #[structopt(short, long, default_value = DEFAULT_INT)]
    interveal: u64,
    #[structopt(short, long, default_value = DEFAULT_DURATION)]
    duration: u64,
}

#[zservice(
    timeout_s = 60,
    prefix = "/lfos",
    service_uuid = "00000000-0000-0000-0000-000000000001"
)]
pub trait Bench {
    async fn bench(&self, name: String) -> String;
}

#[derive(Clone)]
struct BenchZService {
    pub ser_name: String,
}

#[zserver]
impl Bench for BenchZService {
    async fn bench(&self, name: String) -> String {
        format!("Hello {}!, you are connected to {}", name, self.ser_name)
    }
}

#[async_std::main]
async fn main() {
    // initiate logging
    env_logger::init();

    let args = CallArgs::from_args();

    if args.mode == "server" {
        server(args).await;
    } else if args.mode == "client" {
        client(args).await;
    } else {
        panic!("Mode can be only one of [client|server]")
    }
}

async fn client(args: CallArgs) {
    let rtts = Arc::new(AtomicU64::new(0));
    let count: Arc<AtomicU64> = Arc::new(AtomicU64::new(0));

    println!("MSGS,SIZE,THR,INTERVEAL,RTT_US,KIND");
    let properties = format!("mode=client;peer={}", args.router);

    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());

    //let ws = zenoh.workspace(None).await.unwrap();

    let local_servers = BenchClient::find_local_servers(zenoh.clone())
        .await
        .unwrap();
    //println!("local_servers: {:?}", local_servers);

    let client = BenchClient::new(zenoh.clone(), local_servers[0]);
    // let path = Selector::try_from(format!("/test/{}", args.size)).unwrap() ;

    let c = count.clone();
    let s = 128;
    let i = args.interveal;
    let rt = rtts.clone();
    task::spawn(async move {
        loop {
            task::sleep(Duration::from_secs(i)).await;
            let n = c.swap(0, Ordering::AcqRel);
            let r = rt.swap(0, Ordering::AcqRel);
            let msgs = n / i;
            let thr = (n * s * 8) / i;
            let rtt = if n > 0 { r / n } else { std::u64::MAX };
            println!("{},{},{},{},{},{}", msgs, s, thr, i, rtt, "ZRPC-STATE");
        }
    });

    let start = Instant::now();

    while start.elapsed() < Duration::from_secs(args.duration) {
        let now_q = Instant::now();
        client.verify_server().await.unwrap();
        count.fetch_add(1, Ordering::AcqRel);
        rtts.fetch_add(now_q.elapsed().as_micros() as u64, Ordering::AcqRel);
    }

    //zenoh.close().await.unwrap();
}

async fn server(args: CallArgs) {
    let properties = format!("mode=client;peer={}", args.router);
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());

    let service = BenchZService {
        ser_name: "bench service".to_string(),
    };

    let server = service.get_bench_server(zenoh.clone(), None);

    println!("Instance ID {}", server.instance_uuid());
    server.connect().await.unwrap();
    server.initialize().await.unwrap();
    server.register().await.unwrap();

    let (_s, handle) = server.start().await.unwrap();

    handle.await.unwrap();
}
