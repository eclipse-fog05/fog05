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

use async_std::prelude::FutureExt;
use async_std::sync::{Arc, RwLock};

use futures::prelude::*;
use std::convert::TryFrom;
use std::str;

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::fresult::FResult;
use fog05_sdk::types::IPAddress;

use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc_macros::zservice;

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

#[zservice(timeout_s = 10, prefix = "/fos/local")]
pub trait NamespaceManager {
    async fn set_virtual_interface_up(&self, iface: String) -> FResult<()>;
    async fn set_virtual_interface_down(&self, iface: String) -> FResult<()>;
    async fn check_virtual_interface_exists(&self, iface: String) -> FResult<bool>;
    async fn move_virtual_interface_into_default_ns(&self, iface: String) -> FResult<()>;
    async fn set_virtual_interface_mac(&self, iface: String, address: Vec<u8>) -> FResult<()>;
    async fn set_virtual_interface_name(&self, iface: String, name: String) -> FResult<()>;
    async fn del_virtual_interface_address(&self, iface: String, addr: IPAddress) -> FResult<()>;
    async fn add_virtual_interface_address(
        &self,
        iface: String,
        addr: IPAddress,
        prefix: u8,
    ) -> FResult<()>;
    async fn set_virtual_interface_master(&self, iface: String, master: String) -> FResult<()>;
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
}
