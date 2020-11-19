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

use async_std::sync::{Arc, RwLock};

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};

use uuid::Uuid;

pub struct LinuxNetworkState {
    pub uuid: Option<Uuid>,
    pub tokio_rt: tokio::runtime::Runtime,
}

#[derive(Clone)]
pub struct LinuxNetwork {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid: u32,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub state: Arc<RwLock<LinuxNetworkState>>,
}
