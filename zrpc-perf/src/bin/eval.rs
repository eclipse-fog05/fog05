use futures::prelude::*;
use std::convert::TryFrom;
use structopt::StructOpt;
use zenoh::*;

static DEFAULT_MODE: &str = "peer";
static DEFAULT_SIZE: &str = "8";

#[derive(StructOpt, Debug)]
struct GetArgs {
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
    let args = GetArgs::from_args();

    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);
    let zenoh = Zenoh::new(zproperties.into()).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();

    let path = &Path::try_from("/test/eval").unwrap();

    let data: Vec<u8> = vec![0; args.size as usize];
    let mut get_stream = ws.register_eval(&path.into()).await.unwrap();
    while let Some(get_request) = get_stream.next().await {
        get_request.reply(path.clone(), data.clone().into()).await;
    }
}
