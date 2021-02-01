use async_std::sync::Arc;
use async_std::task;
use std::convert::TryFrom;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;
use structopt::StructOpt;
use zenoh::*;

static DEFAULT_MODE: &str = "peer";
static DEFAULT_SIZE: &str = "8";
static DEFAULT_INT: &str = "5";
static DEFAULT_DURATION: &str = "60";

#[derive(StructOpt, Debug)]
struct GetArgs {
    /// Zenoh mode, client or peer
    #[structopt(short, long, default_value = DEFAULT_MODE)]
    mode: String,
    #[structopt(short, long)]
    peer: Option<String>,
    #[structopt(short, long, default_value = DEFAULT_SIZE)]
    size: u64,
    #[structopt(short, long, default_value = DEFAULT_INT)]
    interveal: u64,
    #[structopt(short, long, default_value = DEFAULT_DURATION)]
    duration: u64,
}

#[async_std::main]
async fn main() {
    let args = GetArgs::from_args();
    let count: Arc<AtomicU64> = Arc::new(AtomicU64::new(0));

    //Fields are the same for each test,
    // if they do not make sense they are set to 0
    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);
    let zenoh = Zenoh::new(zproperties.into()).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();

    let path = Selector::try_from(format!("/test/thr")).unwrap();

    let kind = if args.mode == "peer" {
        "PP-SUB"
    } else {
        "CRC-SUB"
    };
    println!("MSGS,SIZE,THR,INTERVEAL,RTT_US,KIND");
    let c = count.clone();
    let s = args.size;
    let i = args.interveal;
    task::spawn(async move {
        loop {
            task::sleep(Duration::from_secs(i)).await;
            let n = c.swap(0, Ordering::AcqRel);
            let msgs = n / i;
            let thr = (n * s * 8) / i;
            println!("{},{},{},{},{},{}", msgs, s, thr, i, 0, kind);
        }
    });

    let subscriber = ws
        .subscribe_with_callback(&path, move |_change| {
            count.fetch_add(1, Ordering::AcqRel);
        })
        .await
        .unwrap();

    task::sleep(Duration::from_secs(args.duration)).await;

    subscriber.close().await.unwrap();
    zenoh.close().await.unwrap();
}
