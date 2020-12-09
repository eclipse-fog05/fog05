use std::convert::TryInto;
use structopt::StructOpt;
use zenoh::*;

static DEFAULT_MODE: &str = "peer";

#[derive(StructOpt, Debug)]
struct PutArgs {
    /// Config file
    #[structopt(short, long, default_value = DEFAULT_MODE)]
    mode: String,
    #[structopt(short, long)]
    peer: Option<String>,
}

#[async_std::main]
async fn main() {
    let args = PutArgs::from_args();

    println!("Args {:?}", args);

    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);
    let zenoh = Zenoh::new(zproperties.into()).await.unwrap();
    let ws = zenoh.workspace(None).await.unwrap();

    let mut size: u32 = 60; //Size of the bench response in zenoh

    let path = format!("/test/{}", size);
    println!("Adding {} size on path {}", size, path);
    let data = vec![0; size as usize];
    ws.put(&path.try_into().unwrap(), data.into())
        .await
        .unwrap();

    size = 128; //size of the component state in zenoh

    let path = format!("/test/{}", size);
    println!("Adding {} size on path {}", size, path);
    let data = vec![0; size as usize];
    ws.put(&path.try_into().unwrap(), data.into())
        .await
        .unwrap();

    size = 491; //size of the zenoh router status (2 clients)
    let path = format!("/test/{}", size);
    println!("Adding {} size on path {}", size, path);
    let data = vec![0; size as usize];
    ws.put(&path.try_into().unwrap(), data.into())
        .await
        .unwrap();

    // Sum of previous sizes
    size = 679;
    let path = format!("/test/{}", size);
    println!("Adding {} size on path {}", size, path);
    let data = vec![0; size as usize];
    ws.put(&path.try_into().unwrap(), data.into())
        .await
        .unwrap();

    println!("Done filling storage")
}
