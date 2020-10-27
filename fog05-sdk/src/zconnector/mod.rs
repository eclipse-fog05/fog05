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

use std::convert::TryInto;
use std::convert::TryFrom;
use super::im::data::*;
use async_std::sync::{Mutex,Arc};
use zenoh::*;
use futures::prelude::*;
use thiserror::Error;
use std::fmt;
use log::{info, trace, warn, error, debug};
use serde::{Serialize,de::DeserializeOwned};
use uuid::Uuid;
use std::str::FromStr;
use crate::fresult::{FResult, FError};


static GLOBAL_ACTUAL_PREFIX: &str = "/fos/global/actual";
static GLOBAL_DESIRED_PREFIX:  &str = "/fos/global/desired";
static LOCAL_ACTUAL_PREFIX:  &str = "/fos/local/actual";
static LOCAL_DESIRED_PREFIX:  &str = "/fos/local/desired";
static LOCAL_CONSTRAINT_ACTUAL_PREFIX:  &str = "/fos/constrained/local/actual";
static LOCAL_CONSTRAINT_DESIRED_PREFIX:  &str = "/fos/constrained/local/desired";

/// Default systemid is 00000000-0000-0000-0000-000000000000
static DEFAULT_SYSTEM_ID : Uuid = Uuid::nil();
static DEFAULT_TENANT_ID : Uuid = Uuid::nil();



// Strings and prefix can be converted to int to reduce the amount of data in zenoh, eg /agfos = /0

macro_rules!  SYS_INFO_PATH { ($prefix:expr, $sysid:expr) => { format!("{}/{}/info", $prefix,$sysid) }; }
macro_rules!  SYS_CONF_PATH { ($prefix:expr, $sysid:expr) => { format!("{}/{}/configuration", $prefix,$sysid) }; }

macro_rules!  SYS_USER_SELECTOR { ($prefix:expr, $sysid:expr) => { format!("{}/{}/users/*", $prefix,$sysid) }; }
macro_rules!  SYS_USER_INFO { ($prefix:expr, $sysid:expr, $userid:expr) => { format!("{}/{}/users/{}/info", $prefix,$sysid,$userid) }; }

macro_rules!  TENANTS_SELECTOR { ($prefix:expr, $sysid:expr) => { format!("{}/{}/tenants/*", $prefix,$sysid) }; }
macro_rules!  TENANT_INFO_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr) => { format!("{}/{}/tenants/{}/info", $prefix,$sysid,$tenantid) }; }
macro_rules!  TENANT_CONF_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr) => { format!("{}/{}/tenants/{}/configuration", $prefix,$sysid,$tenantid) }; }

macro_rules!  NODES_SELECTOR { ($prefix:expr, $sysid:expr, $tenantid:expr) => { format!("{}/{}/tenants/{}/nodes/*/info", $prefix,$sysid,$tenantid) }; }
macro_rules!  NODE_INFO_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/info", $prefix,$sysid,$tenantid,$nodeid) }; }
macro_rules!  NODE_CONF_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/configuration", $prefix,$sysid,$tenantid,$nodeid) }; }
macro_rules!  NODE_STATUS_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/status", $prefix,$sysid,$tenantid,$nodeid) }; }

macro_rules!  NODE_NEIGHBORS_SELECTOR { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/neighbors/*/iface/*", $prefix,$sysid,$tenantid,$nodeid) }; }
macro_rules!  NODE_NEIGHBOR_SELECTOR { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $neighborid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/neighbors/{}/iface/*", $prefix,$sysid,$tenantid,$nodeid, $neighborid) }; }

macro_rules!  NODE_PLUGINS_SELECTOR { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/plugins/*/info", $prefix,$sysid,$tenantid,$nodeid) }; }
macro_rules!  NODE_PLUGIN_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $pluginid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/plugins/{}/info", $prefix,$sysid,$tenantid,$nodeid, $pluginid) }; }

macro_rules!  NODE_FDU_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr, $fduid:expr, $instanceid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/fdu/{}/instances/{}/info", $prefix,$sysid,$tenantid,$nodeid, $fduid, $instanceid) }; }


pub struct Global {
    pub system_id : Uuid,
    pub tenant_id : Uuid,
    z : Arc<zenoh::Zenoh>,
}

impl Global {
    pub fn new(z : Arc<zenoh::Zenoh>, system_id : Option<Uuid>, tenant_id : Option<Uuid>) -> Self {
        let sys_id = if let Some(id) = system_id {
            id
        } else {
            DEFAULT_SYSTEM_ID
        };

        let ten_id = if let Some(id) =  tenant_id {
            id
        } else {
            DEFAULT_TENANT_ID
        };

        Self{
            system_id : sys_id,
            tenant_id : ten_id,
            z,
        }
    }

    pub fn close(self) {
        drop(self);
    }

    pub async fn get_system_info(&self) -> FResult<crate::im::types::SystemInfo> {
        let selector = zenoh::Selector::try_from(SYS_INFO_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id))?;
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
                    zenoh::Value::Raw(_,buf) => {
                        let si = bincode::deserialize::<crate::im::types::SystemInfo>(&buf.to_vec())?;
                        Ok(si)
                    },
                    _ => Err(FError::ZConnectorError),
                }
            },
            _ => Err(FError::ZConnectorError),
        }
    }

    pub async fn get_system_config(&self) -> FResult<crate::im::types::SystemConfig> {
        let selector = zenoh::Selector::try_from(SYS_CONF_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id))?;
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
                    zenoh::Value::Raw(_,buf) => {
                        let sc = bincode::deserialize::<crate::im::types::SystemConfig>(&buf.to_vec())?;
                        Ok(sc)
                    },
                    _ => Err(FError::EncodingError),
                }
            },
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn get_all_nodes(&self) -> FResult<Vec<crate::im::node::NodeInfo>> {
        let selector = zenoh::Selector::try_from(NODES_SELECTOR!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            match &d.value {
                zenoh::Value::Raw(_,buf) => {
                    let ni = bincode::deserialize::<crate::im::node::NodeInfo>(&buf.to_vec())?;
                    data.push(ni);
                },
                _ => return Err(FError::EncodingError),
            }
        }
        Ok(data)
    }

    pub async fn get_node_info(&self, node_uuid : Uuid) -> FResult<crate::im::node::NodeInfo> {
        let selector = zenoh::Selector::try_from(NODE_INFO_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id, node_uuid))?;
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
                    zenoh::Value::Raw(_,buf) => {
                        let ni = bincode::deserialize::<crate::im::node::NodeInfo>(&buf.to_vec())?;
                        Ok(ni)
                    },
                    _ => Err(FError::EncodingError),
                }
            },
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn remove_node_info(&self, node_uuid : Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INFO_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id, node_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)

    }

    pub async fn add_node_info(&self, node_info : crate::im::node::NodeInfo) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INFO_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id, node_info.uuid))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&node_info)?;
        Ok(ws.put(&path,encoded_info.into()).await?)
    }

    pub async fn get_node_status(&self, node_uuid : Uuid) -> FResult<crate::im::node::NodeStatus> {
        let selector = zenoh::Selector::try_from(NODE_STATUS_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id, node_uuid))?;
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
                    zenoh::Value::Raw(_,buf) => {
                        let ni = bincode::deserialize::<crate::im::node::NodeStatus>(&buf.to_vec())?;
                        Ok(ni)
                    },
                    _ => Err(FError::EncodingError),
                }
            },
            _ => Err(FError::TooMuchError),
        }
    }

    pub async fn add_node_status(&self, node_status : crate::im::node::NodeStatus) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_STATUS_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id, node_status.uuid))?;
        let ws = self.z.workspace(None).await?;
        let encoded_status = bincode::serialize(&node_status)?;
        Ok(ws.put(&path,encoded_status.into()).await?)
    }

    pub async fn remove_node_status(&self, node_uuid : Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_STATUS_PATH!(GLOBAL_ACTUAL_PREFIX, self.system_id, self.tenant_id, node_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }
}


pub struct ZConnector {
    pub global : Global
}


impl ZConnector {
    pub fn new(z : Arc<zenoh::Zenoh>, sys_id : Option<Uuid>, ten_id : Option<Uuid>) -> Self {
        Self{
            global : Global::new(z, sys_id, ten_id),
        }
    }
}