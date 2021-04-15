use tide::prelude::*;
use tide::Request;

use async_std::fs;
use async_std::path::Path;
use async_std::sync::Arc;

use git_version::git_version;
use serde::{de::DeserializeOwned, Serialize};
use structopt::StructOpt;

use zenoh::*;

use fog05_sdk::agent::AgentOrchestratorInterfaceClient;
// use fog05_sdk::fresult::FError;
// use fog05_sdk::im::entity::{EntityDescriptor, EntityRecord};
use fog05_sdk::im::fdu::{FDUDescriptor, FDURecord};
use fog05_sdk::zconnector::ZConnector;
use rand::seq::SliceRandom;

static REST_CONFIG_FILE: &str = "/etc/fos/rest.yaml";

const GIT_VERSION: &str = git_version!(prefix = "v", cargo_prefix = "v");

#[derive(StructOpt, Debug)]
struct FOSRestArgs {
    /// Config file
    #[structopt(short, long, default_value = REST_CONFIG_FILE)]
    config: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct FOSRestConfig {
    address: String,
    port: u32,
    locator: String,
}

#[derive(Clone)]
struct FOSRestState {
    zsession: Arc<zenoh::net::Session>,
    zenoh: Arc<zenoh::Zenoh>,
    zconnector: Arc<ZConnector>,
    config: FOSRestConfig,
}

#[derive(Clone, Serialize)]
struct FOSRestResponse<D: Serialize + DeserializeOwned + Clone> {
    result: Option<D>,
    error: Option<String>,
}

impl<D> FOSRestResponse<D>
where
    D: Serialize + DeserializeOwned + Clone,
{
    pub fn serialize_to_json(&self) -> String {
        serde_json::to_string(self).unwrap()
    }
}

async fn read_file(path: &Path) -> String {
    fs::read_to_string(path).await.unwrap()
}

#[async_std::main]
async fn main() -> tide::Result<()> {
    let args = FOSRestArgs::from_args();

    // Init logging
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    log::debug!("Eclipse fog05 REST Service {}", GIT_VERSION);

    let conf_file_path = Path::new(&args.config);
    let config =
        serde_yaml::from_str::<FOSRestConfig>(&(read_file(&conf_file_path).await)).unwrap();

    log::debug!("Configuration {:?}", config);

    let zenoh = Arc::new(
        Zenoh::new(Properties::from(format!("mode=client;peer={}", config.locator)).into())
            .await
            .unwrap(),
    );
    let zsession = Arc::new(
        zenoh::net::open(Properties::from(format!("mode=client;peer={}", config.locator)).into())
            .await
            .unwrap(),
    );
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let rest_state = FOSRestState {
        zsession,
        zenoh,
        zconnector,
        config,
    };

    let mut app = tide::with_state(rest_state.clone());
    app.at("/fdu/define").post(define_fdu);
    app.at("/fdu/instance/:fdu_uuid").post(instantiate_fdu);
    app.at("/fdu/instance/:instance_uuid").get(get_fdu_instance);
    app.at("/fdu/instance/:instance_uuid")
        .delete(delete_fdu_instance);
    app.at("/fdu/delete/:fdu_uuid").delete(delete_fdu);
    app.listen(format!(
        "{}:{}",
        rest_state.config.address, rest_state.config.port
    ))
    .await?;
    Ok(())
}

async fn define_fdu(mut req: Request<FOSRestState>) -> tide::Result {
    let mut fdu_descriptor: FDUDescriptor = req.body_json().await?;
    log::trace!("Received descriptor {:?}", fdu_descriptor);
    let state = req.state();
    let nodes = state.zconnector.global.get_all_nodes().await?;
    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
    log::trace!(
        "Selected node entry point: {}",
        entry_point.agent_service_uuid
    );
    let node_client = AgentOrchestratorInterfaceClient::new(
        state.zsession.clone(),
        entry_point.agent_service_uuid,
    );
    match node_client.onboard_fdu(fdu_descriptor.clone()).await? {
        Ok(fdu_uuid) => {
            log::trace!("Success {} was created!", fdu_uuid);
            fdu_descriptor.uuid = Some(fdu_uuid);
            let res = FOSRestResponse {
                result: Some(fdu_descriptor),
                error: None,
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
        Err(e) => {
            log::error!("Error occurred: {:?}", e);
            let res = FOSRestResponse::<FDUDescriptor> {
                result: None,
                error: Some(format!("{:?}", e)),
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
    }
}

async fn instantiate_fdu(req: Request<FOSRestState>) -> tide::Result {
    let fdu_uuid: uuid::Uuid = uuid::Uuid::parse_str(req.param("fdu_uuid")?)?;
    log::trace!("Received FDU UUID {:?}", fdu_uuid);
    let state = req.state();
    let nodes = state.zconnector.global.get_all_nodes().await?;
    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
    log::trace!(
        "Selected node entry point: {}",
        entry_point.agent_service_uuid
    );
    let node_client = AgentOrchestratorInterfaceClient::new(
        state.zsession.clone(),
        entry_point.agent_service_uuid,
    );

    match state.zconnector.global.get_fdu(fdu_uuid).await {
        Ok(_fdu) => {
            let instance = node_client.schedule_fdu(fdu_uuid).await??;
            node_client.configure_fdu(instance.uuid).await??;
            let instance = node_client.start_fdu(instance.uuid).await??;
            log::trace!("Created instance {:?}", instance);
            let res = FOSRestResponse {
                result: Some(instance),
                error: None,
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
        Err(e) => {
            log::error!("Error occurred: {:?}", e);
            let res = FOSRestResponse::<FDURecord> {
                result: None,
                error: Some(format!("{:?}", e)),
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
    }
}

async fn delete_fdu_instance(req: Request<FOSRestState>) -> tide::Result {
    let instance_uuid: uuid::Uuid = uuid::Uuid::parse_str(req.param("instance_uuid")?)?;
    log::trace!("Received Instance UUID {:?}", instance_uuid);
    let state = req.state();
    let nodes = state.zconnector.global.get_all_nodes().await?;
    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
    log::trace!(
        "Selected node entry point: {}",
        entry_point.agent_service_uuid
    );
    let node_client = AgentOrchestratorInterfaceClient::new(
        state.zsession.clone(),
        entry_point.agent_service_uuid,
    );

    match state.zconnector.global.get_instance(instance_uuid).await {
        Ok(_fdu) => {
            let instance = node_client.stop_fdu(instance_uuid).await??;
            node_client.clean_fdu(instance.uuid).await??;
            let instance = node_client.undefine_fdu(instance.uuid).await??;
            log::trace!("Removed instance {:?}", instance);
            let res = FOSRestResponse {
                result: Some(instance),
                error: None,
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
        Err(e) => {
            log::error!("Error occurred: {:?}", e);
            let res = FOSRestResponse::<FDURecord> {
                result: None,
                error: Some(format!("{:?}", e)),
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
    }
}

async fn get_fdu_instance(req: Request<FOSRestState>) -> tide::Result {
    let instance_uuid: uuid::Uuid = uuid::Uuid::parse_str(req.param("instance_uuid")?)?;
    log::trace!("Received Instance UUID {:?}", instance_uuid);
    let state = req.state();
    let nodes = state.zconnector.global.get_all_nodes().await?;
    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
    log::trace!(
        "Selected node entry point: {}",
        entry_point.agent_service_uuid
    );

    match state.zconnector.global.get_instance(instance_uuid).await {
        Ok(instance) => {
            log::trace!("Get instance {:?}", instance);
            let res = FOSRestResponse {
                result: Some(instance),
                error: None,
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
        Err(e) => {
            log::error!("Error occurred: {:?}", e);
            let res = FOSRestResponse::<FDURecord> {
                result: None,
                error: Some(format!("{:?}", e)),
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
    }
}

async fn delete_fdu(req: Request<FOSRestState>) -> tide::Result {
    let fdu_uuid: uuid::Uuid = uuid::Uuid::parse_str(req.param("fdu_uuid")?)?;
    log::trace!("Received FDU UUID {:?}", fdu_uuid);
    let state = req.state();
    let nodes = state.zconnector.global.get_all_nodes().await?;
    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
    log::trace!(
        "Selected node entry point: {}",
        entry_point.agent_service_uuid
    );
    let node_client = AgentOrchestratorInterfaceClient::new(
        state.zsession.clone(),
        entry_point.agent_service_uuid,
    );
    match state.zconnector.global.get_fdu(fdu_uuid).await {
        Ok(fdu) => match node_client.offload_fdu(fdu_uuid).await? {
            Ok(_fdu_uuid) => {
                log::trace!("Removed descriptor {:?}", fdu);
                let res = FOSRestResponse {
                    result: Some(fdu),
                    error: None,
                };
                let body_resp = res.serialize_to_json();
                Ok(body_resp.into())
            }
            Err(e) => {
                log::error!("Error occurred: {:?}", e);
                let res = FOSRestResponse::<FDUDescriptor> {
                    result: None,
                    error: Some(format!("{:?}", e)),
                };
                let body_resp = res.serialize_to_json();
                Ok(body_resp.into())
            }
        },
        Err(e) => {
            log::error!("Error occurred: {:?}", e);
            let res = FOSRestResponse::<FDUDescriptor> {
                result: None,
                error: Some(format!("{:?}", e)),
            };
            let body_resp = res.serialize_to_json();
            Ok(body_resp.into())
        }
    }
}
