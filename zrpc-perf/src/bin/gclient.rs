use std::sync::Arc;
use tokio::task;

pub mod bench {
    tonic::include_proto!("bench");
}

use bench::bencher_client::BencherClient;
use bench::BenchRequest;

use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};
use structopt::StructOpt;

static DEFAULT_ADDRESS: &str = "127.0.0.1:50001";
static DEFAULT_INT: &str = "5";
static DEFAULT_SIZE: &str = "8";
static DEFAULT_DURATION: &str = "60";

#[derive(StructOpt, Debug)]
struct ClientArgs {

    #[structopt(short, long, default_value = DEFAULT_ADDRESS)]
    address: String,
    #[structopt(short, long, default_value = DEFAULT_SIZE)]
    size: u64,
    #[structopt(short, long, default_value = DEFAULT_INT)]
    interveal: u64,
    #[structopt(short, long, default_value = DEFAULT_DURATION)]
    duration: u64,
}

#[tokio::main(worker_threads=1)]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = ClientArgs::from_args();

    let rtts = Arc::new(AtomicU64::new(0));
    let count: Arc<AtomicU64> = Arc::new(AtomicU64::new(0));

    let kind = "GRPC-CLIENT";

    let mut client = BencherClient::connect(format!("http://{}", args.address)).await?;



    let c = count.clone();
    let s = args.size;
    let i = args.interveal;
    let rt = rtts.clone();

    println!("MSGS,SIZE,THR,INTERVEAL,RTT_US,KIND");
    task::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(i)).await;
            let n = c.swap(0, Ordering::AcqRel);
            let r = rt.swap(0, Ordering::AcqRel);
            let msgs = n / i;
            let thr = (n * s * 8) / i;
            let rtt = if n == 0 { 0 } else { r / n };
            println!("{},{},{},{},{},{}", msgs, s, thr, i, rtt, kind);
        }
    });

    let start = Instant::now();

    while start.elapsed() < Duration::from_secs(args.duration) {
        let now_q = Instant::now();
        let request = tonic::Request::new(BenchRequest{});
        let _r = client.bench(request).await.unwrap();
        count.fetch_add(1, Ordering::AcqRel);
        rtts.fetch_add(now_q.elapsed().as_micros() as u64, Ordering::AcqRel);
    }
    Ok(())
}
