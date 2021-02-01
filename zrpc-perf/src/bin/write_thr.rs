use structopt::StructOpt;
use zenoh::net::*;
use zenoh::Properties;

static DEFAULT_MODE: &str = "peer";
static DEFAULT_SIZE: &str = "8";

#[derive(StructOpt, Debug)]
struct WriteArgs {
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
    let args = WriteArgs::from_args();

    //println!("Args {:?}", args);

    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);
    let session = zenoh::net::open(zproperties.into()).await.unwrap();

    let reskey = ResKey::RId(
        session
            .declare_resource(&ResKey::RName(format!("/test/thr")))
            .await
            .unwrap(),
    );
    let _publ = session.declare_publisher(&reskey).await.unwrap();

    let data: RBuf = (0usize..(args.size as usize))
        .map(|_| 0 as u8)
        .collect::<Vec<u8>>()
        .into();

    loop {
        session
            .write_ext(
                &reskey,
                data.clone(),
                encoding::DEFAULT,
                data_kind::DEFAULT,
                CongestionControl::Block, // Make sure to not drop messages because of congestion control
            )
            .await
            .unwrap();
    }
}
