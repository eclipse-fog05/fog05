

use tonic::{transport::Server, Request, Response, Status};

pub mod bench {
    tonic::include_proto!("bench");
}


use structopt::StructOpt;
use bench::bencher_server::{Bencher, BencherServer};
use bench::{BenchReply, BenchRequest};



static DEFAULT_ADDRESS: &str = "127.0.0.1:50001";
static DEFAULT_SIZE: &str = "8";

#[derive(StructOpt, Debug)]
struct ServerArgs {
    /// Config file
    #[structopt(short, long, default_value = DEFAULT_ADDRESS)]
    address: String,
    #[structopt(short, long, default_value = DEFAULT_SIZE)]
    size: u64,
}


#[derive(Debug, Default)]
pub struct MyBench {
    data: Vec<u8>,
}

#[tonic::async_trait]
impl Bencher for MyBench {
    async fn bench(&self, _request: Request<BenchRequest>) -> Result<Response<BenchReply>, Status> {
        let reply = bench::BenchReply {
            data: self.data.clone(),
        };
        Ok(Response::new(reply))
    }
}



#[tokio::main(worker_threads=1)]
async fn main() -> Result<(), Box<dyn std::error::Error>> {

    let args = ServerArgs::from_args();

    let addr = args.address.parse()?;

    let data = vec![0; args.size as usize];

    let greeter = MyBench{data};

    Server::builder()
        .add_service(BencherServer::new(greeter))
        .serve(addr)
        .await?;

    Ok(())
}
