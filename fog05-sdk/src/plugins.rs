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
use crate::im::fdu::{FDUDescriptor, FDURecord};
use crate::types::{VirtualInterface, VirtualNetwork, VirtualNetworkConfig,
    Interface, IPAddress, MACAddress, ConnectionPoint, ConnectionPointConfig,
    NetworkNamespace, VirtualInterfaceConfig};


#[zservice(timeout_s = 10, prefix = "/fos/local")]
pub trait NetworkingPlugin {

    async fn create_virtual_network(network : VirtualNetworkConfig) -> FResult<VirtualNetwork>;
    async fn get_virtual_network(vnet_uuid : Uuid) -> FResult<VirtualNetwork>;
    async fn delete_virtual_network(vnet_uuid : Uuid) -> FResult<VirtualNetwork>;

    async fn create_connection_point(cp : ConnectionPointConfig) -> FResult<ConnectionPoint>;
    async fn get_connection_point(cp_uuid : Uuid) -> FResult<ConnectionPoint>;
    async fn delete_connection_point(cp_uuid : Uuid) -> FResult<Uuid>;


    async fn create_virtual_interface(intf : VirtualInterfaceConfig) -> FResult<VirtualInterface>;
    async fn get_virtual_interface(intf_uuid : VirtualInterface) -> FResult<VirtualInterface>;
    async fn delete_virtual_interface(intf_uuid : Uuid) -> FResult<VirtualInterface>;

    async fn create_virtual_bridge(br : VirtualInterfaceConfig) -> FResult<VirtualInterface>;
    async fn get_virtual_bridge(br_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn delete_virtual_bridge(br_uuid : Uuid) -> FResult<VirtualInterface>;

    async fn create_network_namespace() -> FResult<NetworkNamespace>;
    async fn get_network_namespace(ns_uuid : Uuid) -> FResult<NetworkNamespace>;
    async fn delete_network_namespace(ns_uuid : Uuid) -> FResult<NetworkNamespace>;

    async fn connect_interface_to_connection_point(intf_uuid : Uuid, cp_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn disconnect_interface_from_connection_point(intf_uuid : Uuid, cp_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn connect_connection_point_to_virtual_network(cp_uuid : Uuid, vnet_uuid : Uuid) -> FResult<ConnectionPoint>;
    async fn disconnect_connection_point_from_virtual_network(cp_uuid : Uuid, vnet_uuid : Uuid) -> FResult<ConnectionPoint>;
    async fn get_connection_point_address(cp_uuid : Uuid) -> FResult<IPAddress>;

    async fn get_overlay_iface() -> FResult<String>;
    async fn get_vlan_face() -> FResult<String>;

    async fn create_macvlan_interface(master_intf : String) -> FResult<VirtualInterface>;
    async fn delete_macvan_interface(intf_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn move_interface_info_namespace(intf_uuid : Uuid, ns_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn move_interface_into_default_namespace(intf_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn rename_virtual_interface(intf_uuid : Uuid, intf_name : String) -> FResult<VirtualInterface>;

    async fn attach_interface_to_bridge(intf_uuid : Uuid, br_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn detach_interface_from_bridge(intf_uuid : Uuid, br_uuid : Uuid) -> FResult<VirtualInterface>;

    async fn create_virtual_interface_in_namespace(intf : VirtualInterface, ns_uuid : Uuid) -> FResult<VirtualInterface>;
    async fn delete_virtual_interface_in_namespace(intf_uuid : Uuid, ns_uuid : Uuid) -> FResult<VirtualInterface>;

    async fn assing_address_to_interface(intf_uuid : Uuid, address: IPAddress) -> FResult<VirtualInterface>;
    async fn remove_address_from_interface(intf_uuid : Uuid, address : IPAddress) -> FResult<VirtualInterface>;

    async fn set_macaddres_of_interface(intf_uuid : Uuid, address : MACAddress) -> FResult<VirtualInterface>;

}


#[zservice(timeout_s = 10, prefix = "/fos/local")]
pub trait HypervisorPlugin {
    async fn define_fdu(fdu : FDUDescriptor) -> FResult<FDURecord>;
    async fn undefine_fdu(instance_uuid : Uuid) -> FResult<Uuid>;
	async fn configure_fdu(instance_uuid : Uuid) -> FResult<Uuid>;
    async fn clean_fdu(instance_uuid : Uuid) -> FResult<Uuid>;
    async fn start_fdu(instance_uuid : Uuid) -> FResult<Uuid>;

    async fn run_fdu(instance_uuid : Uuid) -> FResult<Uuid>; //this should be somehow blocking...
    async fn log_fdu(instance_uuid : Uuid) -> FResult<String>;
    async fn ls_fdu(instance_uuid : Uuid) -> FResult<Vec<String>>;
    async fn file_fdu(instance_uuid : Uuid, file_name : String) -> FResult<String>;


    async fn stop_fdu(instance_uuid : Uuid) -> FResult<Uuid>;
    async fn migrate_fdu(instance_uuid : Uuid, destination_uuid : Uuid) -> FResult<Uuid>;

    async fn get_fdu_status(instance_uuid : Uuid) -> FResult<FDURecord>;


}

