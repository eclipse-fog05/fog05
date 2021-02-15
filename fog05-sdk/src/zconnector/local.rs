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
extern crate serde;

use crate::fresult::{FError, FResult};
use crate::im::data::*;
use async_std::pin::Pin;
use async_std::stream::Stream;
use async_std::sync::{Arc, Mutex};
use async_std::task::{Context, Poll};
use futures::future;
use futures::prelude::*;
use log::{debug, error, info, trace, warn};
use pin_project_lite::pin_project;
use serde::{de::DeserializeOwned, Serialize};
use std::convert::TryFrom;
use std::convert::TryInto;
use std::fmt;
use std::str::FromStr;
use thiserror::Error;
use uuid::Uuid;
use zenoh::*;

static GLOBAL_PREFIX: &str = "/fos/global";
static LOCAL_PREFIX: &str = "/fos/local";

// Strings and prefix can be converted to int to reduce the amount of data in zenoh, eg /fos = /0

macro_rules! NODE_INFO_PATH {
    ($prefix:expr, $nodeid:expr) => {
        format!("{}/{}/info", $prefix, $nodeid)
    };
}
macro_rules! NODE_CONF_PATH {
    ($prefix:expr, $nodeid:expr) => {
        format!("{}/{}/configuration", $prefix, $nodeid)
    };
}
macro_rules! NODE_STATUS_PATH {
    ($prefix:expr, $nodeid:expr) => {
        format!("{}/{}/status", $prefix, $nodeid)
    };
}

macro_rules! NODE_NEIGHBORS_SELECTOR {
    ($prefix:expr, $nodeid:expr) => {
        format!("{}/{}/neighbors/*/iface/*", $prefix, $nodeid)
    };
}
macro_rules! NODE_NEIGHBOR_SELECTOR {
    ($prefix:expr, $nodeid:expr, $neighborid:expr) => {
        format!("{}/{}/neighbors/{}/iface/*", $prefix, $nodeid, $neighborid)
    };
}

macro_rules! NODE_PLUGINS_SELECTOR {
    ($prefix:expr, $nodeid:expr) => {
        format!("{}/{}/plugins/*/info", $prefix, $nodeid)
    };
}
macro_rules! NODE_PLUGIN_PATH {
    ($prefix:expr, $nodeid:expr, $pluginid:expr) => {
        format!("{}/{}/plugins/{}/info", $prefix, $nodeid, $pluginid)
    };
}

macro_rules! NODE_INSTANCE_PATH {
    ($prefix:expr, $nodeid:expr, $fduid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/fdu/{}/instances/{}/info",
            $prefix, $nodeid, $fduid, $instanceid
        )
    };
}
macro_rules! NODE_INSTANCE_SELECTOR {
    ($prefix:expr, $nodeid:expr, $instanceid:expr) => {
        format!(
            "{}/{}/fdu/*/instances/{}/info",
            $prefix, $nodeid, $instanceid
        )
    };
}
macro_rules! NODE_INSTANCE_SELECTOR2 {
    ($prefix:expr, $nodeid:expr, $fduid:expr) => {
        format!("{}/{}/fdu/{}/instances/*/info", $prefix, $nodeid, $fduid)
    };
}

macro_rules! NODE_INSTANCE_SELECTOR3 {
    ($prefix:expr, $nodeid:expr) => {
        format!("{}/{}/fdu/*/instances/*/info", $prefix, $nodeid)
    };
}

macro_rules! NODE_VNET_PATH {
    ($prefix:expr, $nodeid:expr, $vnetid:expr) => {
        format!("{}/{}/network/{}/info", $prefix, $nodeid, $vnetid)
    };
}
macro_rules! NODE_CP_PATH {
    ($prefix:expr, $nodeid:expr, $cpid:expr) => {
        format!("{}/{}/connection_point/{}/info", $prefix, $nodeid, $cpid)
    };
}
macro_rules! NODE_VIFACE_PATH {
    ($prefix:expr, $nodeid:expr, $vifaceid:expr) => {
        format!("{}/{}/viface/{}/info", $prefix, $nodeid, $vifaceid)
    };
}
macro_rules! NODE_NETNS_PATH {
    ($prefix:expr, $nodeid:expr, $netnsid:expr) => {
        format!("{}/{}/netns/{}/info", $prefix, $nodeid, $netnsid)
    };
}

pub struct Local {
    pub node_uuid: Uuid,
    z: Arc<zenoh::Zenoh>,
}

impl Local {
    pub fn new(z: Arc<zenoh::Zenoh>, node_uuid: Uuid) -> Self {
        Self { node_uuid, z }
    }

    pub fn close(self) {
        drop(self);
    }

    pub async fn get_node_info(&self) -> FResult<crate::im::node::NodeInfo> {
        let selector = zenoh::Selector::try_from(NODE_INFO_PATH!(LOCAL_PREFIX, self.node_uuid))?;
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

    pub async fn remove_node_info(&self) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INFO_PATH!(LOCAL_PREFIX, self.node_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn add_node_info(&self, node_info: &crate::im::node::NodeInfo) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INFO_PATH!(LOCAL_PREFIX, self.node_uuid))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&node_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn get_node_status(&self) -> FResult<crate::im::node::NodeStatus> {
        let selector = zenoh::Selector::try_from(NODE_STATUS_PATH!(LOCAL_PREFIX, self.node_uuid))?;
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

    pub async fn add_node_status(&self, node_status: &crate::im::node::NodeStatus) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_STATUS_PATH!(LOCAL_PREFIX, self.node_uuid))?;
        let ws = self.z.workspace(None).await?;
        let encoded_status = bincode::serialize(&node_status)?;
        Ok(ws.put(&path, encoded_status.into()).await?)
    }

    pub async fn remove_node_status(&self) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_STATUS_PATH!(LOCAL_PREFIX, self.node_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_plugin(&self, plugin_uuid: Uuid) -> FResult<crate::types::PluginInfo> {
        let selector = zenoh::Selector::try_from(NODE_PLUGIN_PATH!(
            LOCAL_PREFIX,
            self.node_uuid,
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

    pub async fn add_plugin(&self, plugin_info: &crate::types::PluginInfo) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_PLUGIN_PATH!(
            LOCAL_PREFIX,
            self.node_uuid,
            plugin_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&plugin_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_plugin(&self, plugin_uuid: Uuid) -> FResult<()> {
        let path =
            zenoh::Path::try_from(NODE_PLUGIN_PATH!(LOCAL_PREFIX, self.node_uuid, plugin_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_virtual_network(
        &self,
        net_uuid: Uuid,
    ) -> FResult<crate::types::VirtualNetwork> {
        let selector =
            zenoh::Selector::try_from(NODE_VNET_PATH!(LOCAL_PREFIX, self.node_uuid, net_uuid))?;
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
        vnet_info: &crate::types::VirtualNetwork,
    ) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VNET_PATH!(
            LOCAL_PREFIX,
            self.node_uuid,
            vnet_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&vnet_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_virtual_network(&self, net_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VNET_PATH!(LOCAL_PREFIX, self.node_uuid, net_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_connection_point(
        &self,
        cp_uuid: Uuid,
    ) -> FResult<crate::types::ConnectionPoint> {
        let selector =
            zenoh::Selector::try_from(NODE_CP_PATH!(LOCAL_PREFIX, self.node_uuid, cp_uuid))?;
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
        cp_info: &crate::types::ConnectionPoint,
    ) -> FResult<()> {
        let path =
            zenoh::Path::try_from(NODE_CP_PATH!(LOCAL_PREFIX, self.node_uuid, cp_info.uuid))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(cp_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_connection_point(&self, cp_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_CP_PATH!(LOCAL_PREFIX, self.node_uuid, cp_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_interface(&self, iface_uuid: Uuid) -> FResult<crate::types::VirtualInterface> {
        let selector =
            zenoh::Selector::try_from(NODE_VIFACE_PATH!(LOCAL_PREFIX, self.node_uuid, iface_uuid))?;
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

    pub async fn get_all_interfaces(&self) -> FResult<Vec<crate::types::VirtualInterface>> {
        let selector =
            zenoh::Selector::try_from(NODE_VIFACE_PATH!(LOCAL_PREFIX, self.node_uuid, "*"))?;
        let ws = self.z.workspace(None).await?;
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        let mut ifaces = Vec::new();

        for kv in data {
            match &kv.value {
                zenoh::Value::Raw(_, buf) => {
                    let info =
                        bincode::deserialize::<crate::types::VirtualInterface>(&buf.to_vec())?;
                    ifaces.push(info);
                }
                _ => return Err(FError::EncodingError),
            }
        }
        Ok(ifaces)
    }

    pub async fn add_interface(&self, iface_info: &crate::types::VirtualInterface) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_VIFACE_PATH!(
            LOCAL_PREFIX,
            self.node_uuid,
            iface_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&iface_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_interface(&self, iface_uuid: Uuid) -> FResult<()> {
        let path =
            zenoh::Path::try_from(NODE_VIFACE_PATH!(LOCAL_PREFIX, self.node_uuid, iface_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn get_instance(&self, instance_uuid: Uuid) -> FResult<crate::im::fdu::FDURecord> {
        let selector = zenoh::Selector::try_from(NODE_INSTANCE_SELECTOR!(
            LOCAL_PREFIX,
            self.node_uuid,
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

    pub async fn get_all_instances(&self) -> FResult<Vec<crate::im::fdu::FDURecord>> {
        log::debug!("Get all FDU instances");
        let selector =
            zenoh::Selector::try_from(NODE_INSTANCE_SELECTOR3!(LOCAL_PREFIX, self.node_uuid))?;
        log::trace!("Creating workspace");
        let ws = self.z.workspace(None).await?;
        log::trace!("Calling get");
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        let mut fdus: Vec<crate::im::fdu::FDURecord> = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        log::trace!("Got {} values", data.len());

        for kv in data {
            match &kv.value {
                zenoh::Value::Raw(_, buf) => {
                    let info = bincode::deserialize::<crate::im::fdu::FDURecord>(&buf.to_vec())?;
                    fdus.push(info);
                }
                _ => return Err(FError::EncodingError),
            }
        }
        Ok(fdus)
    }

    pub async fn get_all_fdu_instances(
        &self,
        fdu_uuid: Uuid,
    ) -> FResult<Vec<crate::im::fdu::FDURecord>> {
        log::debug!("Get all FDU instance for {}", fdu_uuid);
        let selector = zenoh::Selector::try_from(NODE_INSTANCE_SELECTOR2!(
            LOCAL_PREFIX,
            self.node_uuid,
            fdu_uuid
        ))?;
        log::trace!("Creating workspace");
        let ws = self.z.workspace(None).await?;
        log::trace!("Calling get");
        let mut ds = ws.get(&selector).await?;
        let mut data = Vec::new();
        let mut fdus: Vec<crate::im::fdu::FDURecord> = Vec::new();
        while let Some(d) = ds.next().await {
            data.push(d)
        }
        log::trace!("Got {} values", data.len());

        for kv in data {
            match &kv.value {
                zenoh::Value::Raw(_, buf) => {
                    let info = bincode::deserialize::<crate::im::fdu::FDURecord>(&buf.to_vec())?;
                    fdus.push(info);
                }
                _ => return Err(FError::EncodingError),
            }
        }
        Ok(fdus)
    }

    pub async fn add_instance(&self, instance_info: &crate::im::fdu::FDURecord) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_INSTANCE_PATH!(
            LOCAL_PREFIX,
            self.node_uuid,
            instance_info.fdu_uuid,
            instance_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&instance_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_instance(&self, instance_uuid: Uuid) -> FResult<()> {
        let instance_info = self.get_instance(instance_uuid).await?;
        let path = zenoh::Path::try_from(NODE_INSTANCE_PATH!(
            LOCAL_PREFIX,
            self.node_uuid,
            instance_info.fdu_uuid,
            instance_info.uuid
        ))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }

    pub async fn subscribe_instances(
        &self,
    ) -> FResult<async_std::channel::Receiver<crate::im::fdu::FDURecord>> {
        let selector =
            zenoh::Selector::try_from(NODE_INSTANCE_SELECTOR3!(LOCAL_PREFIX, self.node_uuid))?;

        let (sender, receiver) = async_std::channel::unbounded::<crate::im::fdu::FDURecord>();
        let sub_z = self.z.clone();

        let _sub = async_std::task::spawn(async move {
            let ws = sub_z.workspace(None).await.ok().unwrap();
            let mut cs = ws.subscribe(&selector).await.ok().unwrap();
            while let Some(change) = cs.next().await {
                match change.kind {
                    zenoh::ChangeKind::Put | zenoh::ChangeKind::Patch => match change.value {
                        Some(value) => {
                            if let zenoh::Value::Raw(_, buf) = value {
                                if let Ok(info) =
                                    bincode::deserialize::<crate::im::fdu::FDURecord>(&buf.to_vec())
                                {
                                    sender.send(info).await.ok().unwrap();
                                }
                            }
                        }
                        None => log::warn!("Received empty change drop it"),
                    },
                    zenoh::ChangeKind::Delete => (),
                }
            }
        });

        Ok(receiver)

        // If Zenoh was allowing this, this would be the preferred solution.
        // let ws = self.z.workspace(None).await?;
        // Ok(ws
        //     .subscribe(&selector)
        //     .await
        //     .map(|change_stream| FDURecordStream { change_stream })?)
    }

    pub async fn get_network_namespace(
        &self,
        ns_uuid: Uuid,
    ) -> FResult<crate::types::NetworkNamespace> {
        let selector =
            zenoh::Selector::try_from(NODE_NETNS_PATH!(LOCAL_PREFIX, self.node_uuid, ns_uuid))?;
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

    pub async fn add_network_namespace(
        &self,
        ns_info: &crate::types::NetworkNamespace,
    ) -> FResult<()> {
        let path =
            zenoh::Path::try_from(NODE_NETNS_PATH!(LOCAL_PREFIX, self.node_uuid, ns_info.uuid))?;
        let ws = self.z.workspace(None).await?;
        let encoded_info = bincode::serialize(&ns_info)?;
        Ok(ws.put(&path, encoded_info.into()).await?)
    }

    pub async fn remove_network_namespace(&self, ns_uuid: Uuid) -> FResult<()> {
        let path = zenoh::Path::try_from(NODE_NETNS_PATH!(LOCAL_PREFIX, self.node_uuid, ns_uuid))?;
        let ws = self.z.workspace(None).await?;
        Ok(ws.delete(&path).await?)
    }
}
