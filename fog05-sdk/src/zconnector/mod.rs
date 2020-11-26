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

extern crate bincode;
extern crate hex;
extern crate serde;

use super::im::data::*;
use crate::fresult::{FError, FResult};
use async_std::sync::{Arc, Mutex};
use futures::prelude::*;
use log::{debug, error, info, trace, warn};
use serde::{de::DeserializeOwned, Serialize};
use std::convert::TryFrom;
use std::convert::TryInto;
use std::fmt;
use std::str::FromStr;
use thiserror::Error;
use uuid::Uuid;
use zenoh::*;

static GLOBAL_ACTUAL_PREFIX: &str = "/fos/global/actual";
static GLOBAL_DESIRED_PREFIX: &str = "/fos/global/desired";
static LOCAL_ACTUAL_PREFIX: &str = "/fos/local/actual";
static LOCAL_DESIRED_PREFIX: &str = "/fos/local/desired";
static LOCAL_CONSTRAINT_ACTUAL_PREFIX: &str = "/fos/constrained/local/actual";
static LOCAL_CONSTRAINT_DESIRED_PREFIX: &str = "/fos/constrained/local/desired";

/// Default systemid is 00000000-0000-0000-0000-000000000000
static DEFAULT_SYSTEM_ID: Uuid = Uuid::nil();
static DEFAULT_TENANT_ID: Uuid = Uuid::nil();

// Strings and prefix can be converted to int to reduce the amount of data in zenoh, eg /agfos = /0

macro_rules! SYS_INFO_PATH {
    ($prefix:expr, $sysid:expr) => {
        format!("{}/{}/info", $prefix, $sysid)
    };
}
macro_rules! SYS_CONF_PATH {
    ($prefix:expr, $sysid:expr) => {
        format!("{}/{}/configuration", $prefix, $sysid)
    };
}

macro_rules! SYS_USER_SELECTOR {
    ($prefix:expr, $sysid:expr) => {
        format!("{}/{}/users/*", $prefix, $sysid)
    };
}
macro_rules! SYS_USER_INFO {
    ($prefix:expr, $sysid:expr, $userid:expr) => {
        format!("{}/{}/users/{}/info", $prefix, $sysid, $userid)
    };
}

macro_rules! TENANTS_SELECTOR {
    ($prefix:expr, $sysid:expr) => {
        format!("{}/{}/tenants/*", $prefix, $sysid)
    };
}
macro_rules! TENANT_INFO_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!("{}/{}/tenants/{}/info", $prefix, $sysid, $tenantid)
    };
}
macro_rules! TENANT_CONF_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!("{}/{}/tenants/{}/configuration", $prefix, $sysid, $tenantid)
    };
}

macro_rules! NODES_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!("{}/{}/tenants/{}/nodes/*/info", $prefix, $sysid, $tenantid)
    };
}
macro_rules! NODE_INFO_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/info",
            $prefix, $sysid, $tenantid, $nodeid
        )
    };
}
macro_rules! NODE_CONF_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/configuration",
            $prefix, $sysid, $tenantid, $nodeid
        )
    };
}
macro_rules! NODE_STATUS_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/status",
            $prefix, $sysid, $tenantid, $nodeid
        )
    };
}

macro_rules! NODE_NEIGHBORS_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/neighbors/*/iface/*",
            $prefix, $sysid, $tenantid, $nodeid
        )
    };
}
macro_rules! NODE_NEIGHBOR_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $neighborid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/neighbors/{}/iface/*",
            $prefix, $sysid, $tenantid, $nodeid, $neighborid
        )
    };
}

macro_rules! NODE_PLUGINS_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/plugins/*/info",
            $prefix, $sysid, $tenantid, $nodeid
        )
    };
}
macro_rules! NODE_PLUGIN_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $pluginid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/plugins/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $pluginid
        )
    };
}

macro_rules! NODE_INSTANCE_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $fduid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/fdu/{}/instances/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $fduid, $instanceid
        )
    };
}
macro_rules! NODE_INSTANCE_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/*/fdu/*/instances/{}/info",
            $prefix, $sysid, $tenantid, $instanceid
        )
    };
}
macro_rules! NODE_INSTANCE_SELECTOR2 {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/fdu/*/instances/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $instanceid
        )
    };
}
macro_rules! NODE_VNET_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $vnetid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/network/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $vnetid
        )
    };
}
macro_rules! NODE_CP_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $cpid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/connection_point/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $cpid
        )
    };
}
macro_rules! NODE_VIFACE_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $vifaceid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/viface/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $vifaceid
        )
    };
}
macro_rules! NODE_NETNS_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $netnsid:expr) => {
        format!(
            "{}/{}/tenants/{}/nodes/{}/netns/{}/info",
            $prefix, $sysid, $tenantid, $nodeid, $netnsid
        )
    };
}

macro_rules! FDU_DESCRIPTOR_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $fduid:expr) => {
        format!(
            "{}/{}/tenants/{}/catalog/fdu/{}/info",
            $prefix, $sysid, $tenantid, $fduid
        )
    };
}
macro_rules! FDU_DESCRIPTOR_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!(
            "{}/{}/tenants/{}/catalog/fdu/*/info",
            $prefix, $sysid, $tenantid
        )
    };
}

macro_rules! FDU_INSTANCE_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/tenants/{}/records/fdu/*/instance/{}/info",
            $prefix, $sysid, $tenantid, $instanceid
        )
    };
}
macro_rules! FDU_INSTANCE_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $fduid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/tenants/{}/records/fdu/{}/instance/{}/info",
            $prefix, $sysid, $tenantid, $fduid, $instanceid
        )
    };
}
macro_rules! FDU_INSTANCES_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $fduid:expr) => {
        format!(
            "{}/{}/tenants/{}/records/fdu/{}/instance/*/info",
            $prefix, $sysid, $tenantid, $fduid
        )
    };
}
macro_rules! FDU_ALL_INSTANCES_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!(
            "{}/{}/tenants/{}/records/fdu/*/instance/*/info",
            $prefix, $sysid, $tenantid
        )
    };
}

macro_rules! VNET_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $vnetid:expr) => {
        format!(
            "{}/{}/tenants/{}/network/{}/info",
            $prefix, $sysid, $tenantid, $vnetid
        )
    };
}
macro_rules! CP_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $cpid:expr) => {
        format!(
            "{}/{}/tenants/{}/connection_point/{}/info",
            $prefix, $sysid, $tenantid, $cpid
        )
    };
}
macro_rules! VIFACE_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $vifaceid:expr) => {
        format!(
            "{}/{}/tenants/{}/viface/{}/info",
            $prefix, $sysid, $tenantid, $vifaceid
        )
    };
}
macro_rules! NETNS_PATH {
    ($prefix:expr, $sysid:expr, $tenantid:expr, $netnsid:expr) => {
        format!(
            "{}/{}/tenants/{}/netns/{}/info",
            $prefix, $sysid, $tenantid, $netnsid
        )
    };
}

macro_rules! VNET_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!(
            "{}/{}/tenants/{}/network/*/info",
            $prefix, $sysid, $tenantid
        )
    };
}
macro_rules! CP_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!(
            "{}/{}/tenants/{}/connection_point/*/info",
            $prefix, $sysid, $tenantid
        )
    };
}
macro_rules! VIFACE_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!("{}/{}/tenants/{}/viface/*/info", $prefix, $sysid, $tenantid)
    };
}
macro_rules! NETNS_SELECTOR {
    ($prefix:expr, $sysid:expr, $tenantid:expr) => {
        format!("{}/{}/tenants/{}/netns/*/info", $prefix, $sysid, $tenantid)
    };
}

pub struct Global {
    pub system_id: Uuid,
    pub tenant_id: Uuid,
    z: Arc<zenoh::Zenoh>,
}

impl Global {
    pub fn new(z: Arc<zenoh::Zenoh>, system_id: Option<Uuid>, tenant_id: Option<Uuid>) -> Self {
        let sys_id = if let Some(id) = system_id {
            id
        } else {
            DEFAULT_SYSTEM_ID
        };

        let ten_id = if let Some(id) = tenant_id {
            id
        } else {
            DEFAULT_TENANT_ID
        };

        Self {
            system_id: sys_id,
            tenant_id: ten_id,
            z,
        }
    }

    pub fn close(self) {
        drop(self);
    }

    pub async fn get_system_info(&self) -> FResult<crate::im::types::SystemInfo> {
        let selector =
            zenoh::Selector::try_from(SYS_INFO_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let si =
                            bincode::deserialize::<crate::im::types::SystemInfo>(&buf.to_vec())?;
                        Ok(si)
                    }
                    _ => Err(FError::ZConnectorError),
                }
            }
            _ => Err(FError::ZConnectorError),
        }
    }

    pub async fn get_system_config(&self) -> FResult<crate::im::types::SystemConfig> {
        let selector =
            zenoh::Selector::try_from(SYS_CONF_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let sc =
                            bincode::deserialize::<crate::im::types::SystemConfig>(&buf.to_vec())?;
                        Ok(sc)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn get_all_nodes(&self) -> FResult<Vec<crate::im::node::NodeInfo>> {
        let selector = zenoh::Selector::try_from(NODES_SELECTOR!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            match &d.value {
                zenoh::Value::Raw(_, buf) => {
                    let ni = bincode::deserialize::<crate::im::node::NodeInfo>(&buf.to_vec())?;
                    data.push(ni);
                }
                _ => return Err(FError::EncodingError),
            }
        }
        Ok(data)
    }

    pub async fn get_node_info(&self, node_uuid: Uuid) -> FResult<crate::im::node::NodeInfo> {
        let selector = zenoh::Selector::try_from(NODE_INFO_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let ni = bincode::deserialize::<crate::im::node::NodeInfo>(&buf.to_vec())?;
                        Ok(ni)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn remove_node_info(&self, node_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INFO_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn add_node_info(&self, node_info: crate::im::node::NodeInfo) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INFO_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&node_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn get_node_status(&self, node_uuid: Uuid) -> FResult<crate::im::node::NodeStatus> {
        let selector = zenoh::Selector::try_from(NODE_STATUS_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let ni =
                            bincode::deserialize::<crate::im::node::NodeStatus>(&buf.to_vec())?;
                        Ok(ni)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_status(&self, node_status: crate::im::node::NodeStatus) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_STATUS_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_status.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_status = bincode::serialize(&node_status)?;
        Ok(ws.put(&path, encoded_status.into()).await?)
    }

    pub async fn remove_node_status(&self, node_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_STATUS_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_plugin(
        &self,
        nodeid: Uuid,
        plugin_uuid: Uuid,
    ) -> FResult<crate::types::PluginInfo> {
        let selector = zenoh::Selector::try_from(NODE_PLUGIN_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            nodeid,
            plugin_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info = bincode::deserialize::<crate::types::PluginInfo>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_plugin(
        &self,
        nodeid: Uuid,
        plugin_info: crate::types::PluginInfo,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_PLUGIN_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            nodeid,
            plugin_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&plugin_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_plugin(&self, nodeid: Uuid, plugin_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_PLUGIN_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            nodeid,
            plugin_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_virtual_network(
        &self,
        net_uuid: Uuid,
    ) -> FResult<crate::types::VirtualNetwork> {
        let selector = zenoh::Selector::try_from(VNET_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            net_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::VirtualNetwork>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_virutal_network(
        &self,
        vnet_info: crate::types::VirtualNetwork,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(VNET_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            vnet_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&vnet_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_virtual_network(&self, net_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(VNET_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            net_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_connection_point(
        &self,
        cp_uuid: Uuid,
    ) -> FResult<crate::types::ConnectionPoint> {
        let selector = zenoh::Selector::try_from(CP_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            cp_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::ConnectionPoint>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_connection_point(
        &self,
        cp_info: crate::types::ConnectionPoint,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(CP_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            cp_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&cp_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_connection_point(&self, cp_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(CP_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            cp_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_interface(&self, iface_uuid: Uuid) -> FResult<crate::types::VirtualInterface> {
        let selector = zenoh::Selector::try_from(VIFACE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            iface_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::VirtualInterface>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_interface(&self, iface_info: crate::types::VirtualInterface) -> FResult<()> {
        let path = zenoh::Path::try_from(VIFACE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            iface_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&iface_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_interface(&self, iface_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(VIFACE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            iface_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_fdu(&self, fdu_uuid: Uuid) -> FResult<crate::im::fdu::FDUDescriptor> {
        let selector = zenoh::Selector::try_from(FDU_DESCRIPTOR_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            fdu_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::im::fdu::FDUDescriptor>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_fdu(&self, fdu_info: crate::im::fdu::FDUDescriptor) -> FResult<()> {
        let fdu_uuid = fdu_info.uuid.ok_or(FError::MalformedDescriptor)?;
        let path = zenoh::Path::try_from(FDU_DESCRIPTOR_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            fdu_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&fdu_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_fdu(&self, fdu_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(FDU_DESCRIPTOR_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            fdu_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_instance(&self, instance_uuid: Uuid) -> FResult<crate::im::fdu::FDURecord> {
        let selector = zenoh::Selector::try_from(FDU_INSTANCE_SELECTOR!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            instance_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::im::fdu::FDURecord>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_instance(&self, instance_info: crate::im::fdu::FDURecord) -> FResult<()> {
        let path = zenoh::Path::try_from(FDU_INSTANCE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            instance_info.fdu_uuid,
            instance_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&instance_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_instance(&self, instance_uuid: Uuid) -> FResult<()> {
        let instance_info = self.get_instance(instance_uuid).await?;
        let path = zenoh::Path::try_from(FDU_INSTANCE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            instance_info.fdu_uuid,
            instance_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_node_instance(
        &self,
        node_uuid: Uuid,
        instance_uuid: Uuid,
    ) -> FResult<crate::im::fdu::FDURecord> {
        let selector = zenoh::Selector::try_from(NODE_INSTANCE_SELECTOR2!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            instance_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::im::fdu::FDURecord>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_instance(
        &self,
        node_uuid: Uuid,
        instance_info: crate::im::fdu::FDURecord,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INSTANCE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            instance_info.fdu_uuid,
            instance_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&instance_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_node_instance(&self, node_uuid: Uuid, instance_uuid: Uuid) -> FResult<()> {
        let instance_info = self.get_instance(instance_uuid).await?;
        let path = zenoh::Path::try_from(NODE_INSTANCE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            instance_info.fdu_uuid,
            instance_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_node_virtual_network(
        &self,
        node_uuid: Uuid,
        net_uuid: Uuid,
    ) -> FResult<crate::types::VirtualNetwork> {
        let selector = zenoh::Selector::try_from(NODE_VNET_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            net_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::VirtualNetwork>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_virutal_network(
        &self,
        node_uuid: Uuid,
        vnet_info: crate::types::VirtualNetwork,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VNET_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            vnet_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&vnet_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_node_virtual_network(
        &self,
        node_uuid: Uuid,
        net_uuid: Uuid,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VNET_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            net_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_node_connection_point(
        &self,
        node_uuid: Uuid,
        cp_uuid: Uuid,
    ) -> FResult<crate::types::ConnectionPoint> {
        let selector = zenoh::Selector::try_from(NODE_CP_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            cp_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::ConnectionPoint>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_connection_point(
        &self,
        node_uuid: Uuid,
        cp_info: crate::types::ConnectionPoint,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_CP_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            cp_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&cp_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_node_connection_point(
        &self,
        node_uuid: Uuid,
        cp_uuid: Uuid,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_CP_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            cp_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_node_interface(
        &self,
        node_uuid: Uuid,
        iface_uuid: Uuid,
    ) -> FResult<crate::types::VirtualInterface> {
        let selector = zenoh::Selector::try_from(NODE_VIFACE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            iface_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::VirtualInterface>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_interface(
        &self,
        node_uuid: Uuid,
        iface_info: crate::types::VirtualInterface,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VIFACE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            iface_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&iface_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_node_interface(&self, node_uuid: Uuid, iface_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VIFACE_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            iface_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_node_network_namespace(
        &self,
        node_uuid: Uuid,
        ns_uuid: Uuid,
    ) -> FResult<crate::types::NetworkNamespace> {
        let selector = zenoh::Selector::try_from(NODE_NETNS_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            ns_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        match data.len() {
            0 => Err(FError::NotFound),
            1 => {
                let kv = &data[0];
                match &kv.value {
                    zenoh::Value::Raw(_, buf) => {
                        let info =
                            bincode::deserialize::<crate::types::NetworkNamespace>(&buf.to_vec())?;
                        Ok(info)
                    }
                    _ => Err(FError::EncodingError),
                }
            }
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_network_namespace(
        &self,
        node_uuid: Uuid,
        ns_info: crate::types::NetworkNamespace,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_NETNS_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            ns_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&ns_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_node_network_namespace(
        &self,
        node_uuid: Uuid,
        ns_uuid: Uuid,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_NETNS_PATH!(
            GLOBAL_ACTUAL_PREFIX,
            self.system_id,
            self.tenant_id,
            node_uuid,
            ns_uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }
}

pub struct ZConnector {
    pub global: Global,
}

impl ZConnector {
    pub fn new(z: Arc<zenoh::Zenoh>, sys_id: Option<Uuid>, ten_id: Option<Uuid>) -> Self {
        Self {
            global: Global::new(z, sys_id, ten_id),
        }
    }

    pub fn close(self) {
        drop(self);
    }
}
