use futures::prelude::*;
use std::convert::TryFrom;
use structopt::StructOpt;
use zenoh::net::queryable::EVAL;
use zenoh::net::*;
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
    let session = zenoh::net::open(zproperties.into()).await.unwrap();

    let path = &Path::try_from("/test/eval").unwrap();

    let mut queryable = session
        .declare_queryable(&path.clone().into(), EVAL)
        .await
        .unwrap();

    let data: Vec<u8> = vec![0; args.size as usize];
    let query_stream = queryable.stream();
    while let Some(query) = query_stream.next().await {
        query
            .reply(Sample {
                res_name: path.to_string().clone(),
                payload: data.clone().into(),
                data_info: None,
            })
            .await;
    }
}
