/*********************************************************************************
* Copyright (c) 2018,2020 ADLINK Technology Inc.
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
* which is available at https://www.apache.org/licenses/LICENSE-2.0.
*
* SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
* Contributors:
*   ADLINK fog05 team, <fog05@adlink-labs.tech>
*********************************************************************************/
#![allow(unused)]

use uuid::Uuid;

use rand::seq::SliceRandom;

use async_std::sync::Arc;

use zenoh::net::Session;

use crate::agent::AgentOrchestratorInterfaceClient;
use crate::fresult::FResult;
use crate::im;
use crate::zconnector::ZConnector;

pub struct FDUApi {
    pub zenoh: Arc<zenoh::net::Session>,
    pub zconnector: Arc<ZConnector>,
}

impl FDUApi {
    pub fn new(zconnector: Arc<ZConnector>, zenoh: Arc<zenoh::net::Session>) -> Self {
        Self { zenoh, zconnector }
    }

    async fn onboard_fdu(&self, fdu: im::fdu::FDUDescriptor) -> FResult<Uuid> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.onboard_fdu(fdu).await? {
            Ok(fdu_uuid) => Ok(fdu_uuid),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }

    async fn define_fdu(
        &self,
        fdu_uuid: Uuid,
        node_uuid: Option<Uuid>,
    ) -> FResult<im::fdu::FDURecord> {
        let entry_point = match node_uuid {
            None => {
                let nodes = self.zconnector.global.get_all_nodes().await?;
                let ep = nodes.choose(&mut rand::thread_rng()).unwrap();
                (&*ep).clone()
            }
            Some(node_uuid) => {
                let ni = self.zconnector.global.get_node_info(node_uuid).await?;
                ni
            }
        };
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );

        match node_uuid {
            None => match node_client.schedule_fdu(fdu_uuid).await? {
                Ok(instance) => Ok(instance),
                Err(e) => {
                    log::error!("Error occured: {}", e);
                    Err(e)
                }
            },
            Some(_) => match node_client.define_fdu(fdu_uuid).await? {
                Ok(instance) => Ok(instance),
                Err(e) => {
                    log::error!("Error occured: {}", e);
                    Err(e)
                }
            },
        }
    }

    async fn configure_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.configure_fdu(instance_uuid).await? {
            Ok(instance) => Ok(instance),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }

    async fn start_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.start_fdu(instance_uuid).await? {
            Ok(instance) => Ok(instance),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }

    async fn stop_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.stop_fdu(instance_uuid).await? {
            Ok(instance) => Ok(instance),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }

    async fn clean_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.clean_fdu(instance_uuid).await? {
            Ok(instance) => Ok(instance),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }

    async fn undefine_fdu(&self, instance_uuid: Uuid) -> FResult<im::fdu::FDURecord> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.undefine_fdu(instance_uuid).await? {
            Ok(instance) => Ok(instance),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }

    async fn offload_fdu(&self, fdu_uuid: Uuid) -> FResult<Uuid> {
        let nodes = self.zconnector.global.get_all_nodes().await?;
        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
        log::trace!(
            "Selected node entry point: {}",
            entry_point.agent_service_uuid
        );
        let node_client = AgentOrchestratorInterfaceClient::new(
            self.zenoh.clone(),
            entry_point.agent_service_uuid,
        );
        match node_client.offload_fdu(fdu_uuid).await? {
            Ok(id) => Ok(id),
            Err(e) => {
                log::error!("Error occured: {}", e);
                Err(e)
            }
        }
    }
}

pub struct NodeApi {
    pub zenoh: Arc<zenoh::net::Session>,
    pub zconnector: Arc<ZConnector>,
}

impl NodeApi {
    pub fn new(zconnector: Arc<ZConnector>, zenoh: Arc<zenoh::net::Session>) -> Self {
        Self { zenoh, zconnector }
    }

    async fn list(&self) -> FResult<Vec<im::node::NodeInfo>> {
        self.zconnector.global.get_all_nodes().await
    }

    async fn info(&self, node_uuid: Uuid) -> FResult<im::node::NodeInfo> {
        self.zconnector.global.get_node_info(node_uuid).await
    }

    async fn status(&self, node_uuid: Uuid) -> FResult<im::node::NodeStatus> {
        self.zconnector.global.get_node_status(node_uuid).await
    }
}

pub struct NetworkApi {
    pub zenoh: Arc<zenoh::net::Session>,
    pub zconnector: Arc<ZConnector>,
}

pub struct FIMApi {
    pub zenoh: Arc<zenoh::net::Session>,
    pub zconnector: Arc<ZConnector>,
    pub fdu: FDUApi,
    pub node: NodeApi,
}

impl FIMApi {
    pub fn new(zconnector: Arc<ZConnector>, zenoh: Arc<zenoh::net::Session>) -> Self {
        Self {
            zenoh: zenoh.clone(),
            zconnector: zconnector.clone(),
            fdu: FDUApi::new(zconnector.clone(), zenoh.clone()),
            node: NodeApi::new(zconnector, zenoh),
        }
    }
}
