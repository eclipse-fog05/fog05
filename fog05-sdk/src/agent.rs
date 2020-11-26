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

use thiserror::Error;
use zenoh::*;
use std::fmt;


use async_std::task;
use async_std::sync::Arc;
use async_std::prelude::FutureExt;
use std::time::Duration;
use futures::prelude::*;
use zenoh::*;
use std::str;
use std::str::FromStr;
use std::convert::TryFrom;
use uuid::Uuid;

use log::{trace};

//importing the macros
use zrpc_macros::{zservice, zserver};

use crate::fresult::FResult;
use crate::types::{IPAddress, InterfaceKind};
use crate::im;
use crate::types;




#[zservice(timeout_s = 10, prefix = "/fos/local")]
pub trait OS {

    // ex-OS plugin evals, used in agent<->plugin communication
    // std::path::Path doesn't have a size known at compile-time, cannot be serialized, using String instead

    async fn dir_exists(&self, dir_path : String) -> FResult<bool>;
    async fn create_dir(&self, dir_path : String) -> FResult<bool>;
    async fn rm_dir(&self, dir_path : String) -> FResult<bool>;

    async fn download_file(&self, url : url::Url, dest_path : String) -> FResult<bool>;

    async fn create_file(&self, file_path : String) -> FResult<bool>;
    async fn rm_file(&self, file_path : String) -> FResult<bool>;
    async fn store_file(&self, content : Vec<u8>, file_path : String) -> FResult<bool>;
    async fn read_file(&self, file_path : String) -> FResult<Vec<u8>>;
    async fn file_exists(&self, file_path : String) -> FResult<bool>;

    async fn execute_command(&self, cmd : String) -> FResult<String>;
    async fn send_signal(&self, signal : u8, pid : u32) -> FResult<bool>;
    async fn check_if_pid_exists(&self, pid : u32) -> FResult<bool>;

    async fn get_interface_type(&self, iface : String) -> FResult<InterfaceKind>;
    async fn set_interface_unavailable(&self, iface : String) -> FResult<bool>;
    async fn set_interface_available(&self, iface : String) -> FResult<bool>;
    async fn get_local_mgmt_address(&self) -> FResult<IPAddress>;

}


#[zservice(timeout_s = 10, prefix = "/fos/local")]
pub trait AgentPluginInterface {

    async fn fdu_info(&self, fdu_uuid : Uuid) -> FResult<im::fdu::FDUDescriptor>;
    async fn image_info(&self, image_uuid : Uuid) -> FResult<im::fdu::Image>;
    async fn node_fdu_info(&self, fdu_uuid : Uuid, node_uuid : Uuid, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn network_info(&self, network_uuid : Uuid) -> FResult<types::VirtualNetwork>;
    async fn connection_point_info(&self, cp_uuid : Uuid) -> FResult<types::ConnectionPoint>;
    async fn node_management_address(&self, node_uuid : Uuid) -> FResult<IPAddress>;

    async fn create_virtual_network(&self, vnet : types::VirtualNetworkConfig) -> FResult<types::VirtualNetwork>;
    async fn remove_virtual_network(&self, vnet_uuid : Uuid) -> FResult<Uuid>;

    async fn create_connection_point(&self, cp : types::ConnectionPointConfig) -> FResult<types::ConnectionPoint>;
    async fn remove_connection_point(&self, cp_uuid : Uuid) -> FResult<Uuid>;

    async fn bind_cp_to_fdu_face(&self, cp_uuid : Uuid, instance_uuid : Uuid, interface : String) -> FResult<Uuid>;
    async fn unbind_co_from_fdu_face(&self, cp_uuid : Uuid, instance_uuid : Uuid, interface : String) -> FResult<Uuid>;

    async fn bind_cp_to_network(&self, cp_uuid : Uuid, vnet_uuid : Uuid) -> FResult<Uuid>;
    async fn unbind_cp_from_network(&self, cp_uuid : Uuid, vnet_uuid : Uuid) -> FResult<Uuid>;

    async fn register_plugin(&mut self, plugin_uuid : Uuid, kind : types::PluginKind) -> FResult<Uuid>;
    async fn unregister_plugin(&mut self, plugin_uuid : Uuid) -> FResult<Uuid>;

}


#[zservice(timeout_s = 10, prefix = "/fos/local")]
pub trait AgentOrchestratorInterface {

    async fn check_fdu_compatibility(&self, fdu_uuid : Uuid) -> FResult<bool>;

    async fn schedule_fdu(&self, fdu_uuid : Uuid) -> FResult<im::fdu::FDURecord>;

    async fn onboard_fdu(&self, fdu : im::fdu::FDUDescriptor) -> FResult<Uuid>;

    async fn define_fdu(&self, fdu_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn configure_fdu(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn start_fdu(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;

    async fn run_fdu(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn log_fdu(&self, instance_uuid : Uuid) -> FResult<String>;
    async fn ls_fdu(&self, instance_uuid : Uuid) -> FResult<Vec<String>>;
    async fn file_fdu(&self, instance_uuid : Uuid, file_name : String) -> FResult<String>;

    async fn stop_fdu(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn clean_fdu(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn undefine_fdu(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;
    async fn offload_fdu(&self, fdu_uuid : Uuid) -> FResult<Uuid>;

    async fn fdu_status(&self, instance_uuid : Uuid) -> FResult<im::fdu::FDURecord>;

    async fn create_floating_ip(&self) -> FResult<Uuid>;
    async fn delete_floating_ip(&self, ip_uuid : Uuid) -> FResult<Uuid>;
    async fn assing_floating_ip(&self, ip_uuid : Uuid, cp_uuid : Uuid) -> FResult<Uuid>;
    async fn retain_floating_ip(&self, ip_uuid : Uuid, cp_uuid : Uuid) -> FResult<Uuid>;
}
