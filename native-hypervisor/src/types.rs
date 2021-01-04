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
extern crate serde_json;
extern crate serde_yaml;

use std::collections::HashMap;
use std::process::Child;

use async_std::sync::{Arc, Mutex, RwLock};

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::im::fdu::*;
use fog05_sdk::plugins::NetworkingPluginClient;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct NativeHVConfig {
    pub pid_file: Box<std::path::Path>,
    pub zlocator: String,
    pub path: Box<std::path::Path>,
    pub run_path: Box<std::path::Path>,
    pub monitoring_interveal: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NativeHVSpecificInfo {
    //pub netns: Uuid,
    pub pid: u32,
    pub env: HashMap<String, String>,
    pub instance_path: String,
    pub instance_files: Vec<String>,
    pub netns: Option<Uuid>,
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
    pub config: NativeHVConfig,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub net: Option<NetworkingPluginClient>,
    pub fdus: Arc<RwLock<NativeHVState>>,
}

pub fn serialize_native_specific_info(data: &NativeHVSpecificInfo) -> FResult<Vec<u8>> {
    Ok(serde_json::to_string(data)
        .map_err(|e| FError::HypervisorError(format!("{}", e)))?
        .into_bytes())
}

pub fn deserialize_native_specific_info(raw_data: &[u8]) -> FResult<NativeHVSpecificInfo> {
    Ok(serde_json::from_str::<NativeHVSpecificInfo>(
        std::str::from_utf8(raw_data).map_err(|e| FError::HypervisorError(format!("{}", e)))?,
    )
    .map_err(|e| FError::HypervisorError(format!("{}", e)))?)
}

pub fn serialize_native_specific_descriptor(data: &NativeHVSpecificDescriptor) -> FResult<Vec<u8>> {
    Ok(serde_json::to_string(data)
        .map_err(|e| FError::HypervisorError(format!("{}", e)))?
        .into_bytes())
}

pub fn deserialize_native_specific_descriptor(
    raw_data: &[u8],
) -> FResult<NativeHVSpecificDescriptor> {
    Ok(serde_json::from_str::<NativeHVSpecificDescriptor>(
        std::str::from_utf8(raw_data).map_err(|e| FError::HypervisorError(format!("{}", e)))?,
    )
    .map_err(|e| FError::HypervisorError(format!("{}", e)))?)
}

pub fn serialize_plugin_config(data: &NativeHVConfig) -> FResult<Vec<u8>> {
    Ok(serde_yaml::to_string(data)
        .map_err(|e| FError::HypervisorError(format!("{}", e)))?
        .into_bytes())
}

pub fn deserialize_plugin_config(raw_data: &[u8]) -> FResult<NativeHVConfig> {
    Ok(serde_yaml::from_str::<NativeHVConfig>(
        std::str::from_utf8(raw_data).map_err(|e| FError::HypervisorError(format!("{}", e)))?,
    )
    .map_err(|e| FError::HypervisorError(format!("{}", e)))?)
}
