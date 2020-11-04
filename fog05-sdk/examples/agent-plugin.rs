use async_std::sync::Arc;

use fog05_sdk::agent::AgentPluginInterfaceClient;
use zenoh::*;

#[async_std::main]
async fn main() {
    env_logger::init();

    let zenoh = Arc::new(
        Zenoh::new(Properties::from("mode=client;peer=tcp/127.0.0.1:7447").into())
            .await
            .unwrap(),
    );
    let local_servers = AgentPluginInterfaceClient::find_local_servers(zenoh.clone())
        .await
        .unwrap();
    println!("local_servers: {:?}", local_servers);
    match local_servers.len() {
        0 => panic!("No Agent to test with"),
        1 => {
            let service_uuid = local_servers[0];
            let client = AgentPluginInterfaceClient::new(zenoh.clone(), service_uuid);
            println!("Res is: {:?}", client.fdu_info(service_uuid).await);
        }
        _ => panic!("Found more that one local agent!!"),
    }
}
