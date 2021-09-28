use async_std::sync::Arc;

use fog05_sdk::agent::os::OSClient;
use zenoh::*;

use url::Url;

#[async_std::main]
async fn main() {
    env_logger::init();

    let zenoh = Arc::new(
        zenoh::net::open(Properties::from("mode=client;peer=tcp/127.0.0.1:61189").into())
            .await
            .unwrap(),
    );
    let local_servers = OSClient::find_servers(zenoh.clone()).await.unwrap();
    println!("local_servers: {:?}", local_servers);
    match local_servers.len() {
        0 => panic!("No Agent to test with"),
        1 => {
            let service_uuid = local_servers[0];
            let client = OSClient::new(zenoh.clone(), service_uuid);
            println!(
                "Res is: {:?}",
                client.dir_exists(String::from("/tmp")).await
            );
            let remote = Url::parse("https://gist.githubusercontent.com/gabrik/24e664ff772837563acd59108bc724e5/raw/8eb18fdaef00a2bc2df3af8e4f50b3db514cfaa0/node-prepare.sh").unwrap();
            println!(
                "Res is: {:?}",
                client
                    .download_file(remote, String::from("/tmp/dest.pl"))
                    .await
            );
        }
        _ => panic!("Found more that one local agent!!"),
    }
}
