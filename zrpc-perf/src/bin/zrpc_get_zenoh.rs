use async_std::sync::Arc;
use async_std::task;
use futures::prelude::*;
use std::convert::TryFrom;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};
use structopt::StructOpt;
use zenoh::*;

static DEFAULT_MODE: &str = "peer";
static DEFAULT_INT: &str = "5";
static DEFAULT_DURATION: &str = "60";

#[derive(StructOpt, Debug)]
struct GetArgs {
    /// Config file
    #[structopt(short, long, default_value = DEFAULT_MODE)]
    mode: String,
    #[structopt(short, long)]
    peer: Option<String>,
    #[structopt(short, long, default_value = DEFAULT_INT)]
    interveal: u64,
    #[structopt(short, long, default_value = DEFAULT_DURATION)]
    duration: u64,
}

#[async_std::main]
async fn main() {
    let args = GetArgs::from_args();

    let rtts = Arc::new(AtomicU64::new(0));
    let count: Arc<AtomicU64> = Arc::new(AtomicU64::new(0));

    println!("MSGS,SIZE,THR,INTERVEAL,RTT_US,KIND");
    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);
    let zenoh = Zenoh::new(zproperties.into()).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();

    let zsession = zenoh.session();
    let zinfo = zsession.info().await;
    let rid = zinfo
        .get(&zenoh::net::info::ZN_INFO_ROUTER_PID_KEY)
        .unwrap()
        .split(",")
        .collect::<Vec<_>>()[0]
        .to_uppercase();

    let selector = zenoh::Selector::try_from(format!("/@/router/{}", String::from(&rid))).unwrap();

    let c = count.clone();
    let s = 491;
    let i = args.interveal;
    let rt = rtts.clone();
    task::spawn(async move {
        loop {
            task::sleep(Duration::from_secs(i)).await;
            let n = c.swap(0, Ordering::AcqRel);
            let r = rt.swap(0, Ordering::AcqRel);
            let msgs = n / i;
            let thr = (n * s * 8) / i;
            let rtt = r / n;
            println!("{},{},{},{},{},{}", msgs, s, thr, i, rtt, "ZRPC-Z-ADMIN");
        }
    });

    let start = Instant::now();

    while start.elapsed() < Duration::from_secs(args.duration) {
        let now_q = Instant::now();
        let mut data_stream = ws.get(&selector).await.unwrap();
        while data_stream.next().await.is_some() {}
        count.fetch_add(1, Ordering::AcqRel);
        rtts.fetch_add(now_q.elapsed().as_micros() as u64, Ordering::AcqRel);
    }

    zenoh.close().await.unwrap();
}
