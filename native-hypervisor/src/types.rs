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

#![allow(unused_variables)]

extern crate serde;

use std::collections::HashMap;
use std::process::Child;

use async_std::sync::{Arc, Mutex, RwLock};

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::im::fdu::*;
use fog05_sdk::plugins::NetworkingPluginClient;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NativeHVSpecificInfo {
    //pub netns: Uuid,
    pub pid: u32,
    pub env: HashMap<String, String>,
    pub instance_path: String,
    pub instance_files: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NativeHVSpecificDescriptor {
    pub path: Option<String>,
    pub cmd: String,
    pub args: Vec<String>,
    pub env: HashMap<String, String>,
}

#[derive(Clone)]
pub struct NativeHVState {
    pub fdus: HashMap<Uuid, FDURecord>,
    pub childs: HashMap<Uuid, Arc<Mutex<Child>>>,
    pub uuid: Option<Uuid>,
}

#[derive(Clone)]
pub struct NativeHypervisor {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid: u32,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub net: Option<NetworkingPluginClient>,
    pub fdus: Arc<RwLock<NativeHVState>>,
}
