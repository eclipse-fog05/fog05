use std::convert::TryFrom;
use structopt::StructOpt;
use zenoh::*;

static DEFAULT_MODE: &str = "peer";
static DEFAULT_SIZE: &str = "8";

#[derive(StructOpt, Debug)]
struct PutArgs {
    /// Config file
    #[structopt(short, long, default_value = DEFAULT_MODE)]
    mode: String,
    #[structopt(short, long)]
    peer: Option<String>,
    #[structopt(short, long, default_value = DEFAULT_SIZE)]
    size: u64,
}

#[async_std::main]
async fn main() {
    let args = PutArgs::from_args();

    //println!("Args {:?}", args);

    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);
    let zenoh = Zenoh::new(zproperties.into()).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();

    let path: Path = Path::try_from("/test/thr").unwrap();
    let data = vec![0; args.size as usize];
    let value = Value::from(data);

    loop {
        ws.put(&path, value.clone()).await.unwrap();
    }
}
