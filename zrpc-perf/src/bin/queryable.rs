use async_std::task;
use futures::prelude::*;
use futures::select;
use std::convert::TryFrom;
use structopt::StructOpt;
use zenoh::net::queryable::EVAL;
use zenoh::net::*;
use zenoh::*;
use zenoh::net::protocol::proto::DataInfo;

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

    let _h = task::spawn(async move {
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

        let sample = Sample {
            res_name: "/test/eval".into(),
            payload: data.into(),
            data_info: Some(DataInfo {
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
        loop {
            select!(
                query = queryable.stream().next().fuse() => {
                    let q = query.unwrap();
                    q
                    .reply(sample.clone())
                    .await;
                }
            );
        }
    });

    futures::future::pending::<()>().await;
}
