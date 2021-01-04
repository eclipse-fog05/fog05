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
#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]

extern crate serde;
extern crate serde_json;

use serde::{Deserialize, Serialize};

use async_std::prelude::FutureExt;
use async_std::sync::{Arc, RwLock};

use futures::prelude::*;
use std::collections::HashMap;
use std::convert::TryFrom;
use std::str;

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::types::IPAddress;

use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc_macros::zservice;

use uuid::Uuid;

use ipnetwork::IpNetwork;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct LinuxNetworkConfig {
    pub pid_file: Box<std::path::Path>,
    pub zlocator: String,
    pub zfilelocator: String,
    pub path: Box<std::path::Path>,
    pub run_path: Box<std::path::Path>,
    pub monitoring_interveal: u64,
    pub overlay_iface: Option<String>,
    pub dataplane_iface: Option<String>,
}

pub struct LinuxNetworkState {
    pub uuid: Option<Uuid>,
    pub tokio_rt: tokio::runtime::Runtime,
    pub ns_managers: HashMap<Uuid, (u32, NamespaceManagerClient)>,
}

#[derive(Clone)]
pub struct LinuxNetwork {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid: u32,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub config: LinuxNetworkConfig,
    pub state: Arc<RwLock<LinuxNetworkState>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VNetDHCP {
    pub leases_file: String,
    pub pid_file: String,
    pub conf: String,
    pub log_file: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VNetNetns {
    pub ns_name: String,
    pub ns_uuid: Uuid,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualNetworkInternals {
    pub dhcp: Option<VNetDHCP>,
    pub associated_netns: Option<VNetNetns>,
    pub associated_tables: Vec<String>,
}

pub fn serialize_network_internals(data: &VirtualNetworkInternals) -> FResult<Vec<u8>> {
    Ok(serde_json::to_string(data)
        .map_err(|e| FError::NetworkingError(format!("{}", e)))?
        .into_bytes())
}

pub fn deserialize_network_internals(raw_data: &[u8]) -> FResult<VirtualNetworkInternals> {
    Ok(serde_json::from_str::<VirtualNetworkInternals>(
        std::str::from_utf8(raw_data).map_err(|e| FError::NetworkingError(format!("{}", e)))?,
    )
    .map_err(|e| FError::NetworkingError(format!("{}", e)))?)
}

pub fn serialize_plugin_config(data: &LinuxNetworkConfig) -> FResult<Vec<u8>> {
    Ok(serde_yaml::to_string(data)
        .map_err(|e| FError::NetworkingError(format!("{}", e)))?
        .into_bytes())
}

pub fn deserialize_plugin_config(raw_data: &[u8]) -> FResult<LinuxNetworkConfig> {
    Ok(serde_yaml::from_str::<LinuxNetworkConfig>(
        std::str::from_utf8(raw_data).map_err(|e| FError::NetworkingError(format!("{}", e)))?,
    )
    .map_err(|e| FError::NetworkingError(format!("{}", e)))?)
}

#[zservice(timeout_s = 60, prefix = "/fos/local")]
pub trait NamespaceManager {
    async fn set_virtual_interface_up(&self, iface: String) -> FResult<()>;
    async fn set_virtual_interface_down(&self, iface: String) -> FResult<()>;
    async fn check_virtual_interface_exists(&self, iface: String) -> FResult<bool>;
    async fn move_virtual_interface_into_default_ns(&self, iface: String) -> FResult<()>;
    async fn set_virtual_interface_mac(&self, iface: String, address: Vec<u8>) -> FResult<()>;
    async fn set_virtual_interface_name(&self, iface: String, name: String) -> FResult<()>;
    async fn del_virtual_interface_address(&self, iface: String, addr: IPAddress) -> FResult<()>;
    async fn get_virtual_interface_addresses(&self, iface: String) -> FResult<Vec<IPAddress>>;
    async fn add_virtual_interface_address(
        &self,
        iface: String,
        addr: Option<IpNetwork>,
    ) -> FResult<Vec<IPAddress>>;
    async fn set_virtual_interface_master(&self, iface: String, master: String) -> FResult<()>;
    async fn set_virtual_interface_nomaster(&self, iface: String) -> FResult<()>;
    async fn del_virtual_interface(&self, iface: String) -> FResult<()>;
    async fn add_virtual_interface_ptp_vxlan(
        &self,
        iface: String,
        dev: String,
        vni: u32,
        local_addr: IPAddress,
        remote_addr: IPAddress,
        port: u16,
    ) -> FResult<()>;
    async fn add_virtual_interface_mcast_vxlan(
        &self,
        iface: String,
        dev: String,
        vni: u32,
        mcast_addr: IPAddress,
        port: u16,
    ) -> FResult<()>;
    async fn add_virtual_interface_vlan(&self, iface: String, dev: String, tag: u16)
        -> FResult<()>;
    async fn add_virtual_interface_veth(&self, iface_i: String, iface_e: String) -> FResult<()>;
    async fn add_virtual_interface_bridge(&self, br_name: String) -> FResult<()>;
    async fn list_interfaces(&self) -> FResult<Vec<String>>;
}
