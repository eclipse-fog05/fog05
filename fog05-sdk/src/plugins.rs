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
#![allow(clippy::manual_async_fn)]
#![allow(clippy::large_enum_variant)]

use std::convert::TryFrom;
use std::fmt;
use std::str;
use std::str::FromStr;
use std::time::Duration;

use thiserror::Error;

use async_std::prelude::FutureExt;
use async_std::sync::Arc;
use async_std::task;
use futures::prelude::*;

use uuid::Uuid;
use zenoh::*;

use log::trace;

use ipnetwork::IpNetwork;

use zrpc::zrpcresult::{ZRPCError, ZRPCResult};
use zrpc_macros::{zserver, zservice};

use crate::fresult::FResult;
use crate::im::fdu::{FDUDescriptor, FDURecord};
use crate::types::{
    ConnectionPoint, ConnectionPointConfig, IPAddress, Interface, MACAddress, NetworkNamespace,
    VirtualInterface, VirtualInterfaceConfig, VirtualNetwork, VirtualNetworkConfig,
};

#[zservice(
    timeout_s = 60,
    prefix = "/fos/local",
    service_uuid = "00000000-0000-0000-0000-000000000004"
)]
pub trait NetworkingPlugin {
    /// Creates the default fosbr0 virtual network
    /// it's UUID is 00000000-0000-0000-0000-000000000000
    /// it is a VXLAN kind of virtual network
    /// VNI: 3845
    /// MCast Addr: 239.15.5.0
    /// Port 3845
    /// Net: 10.240.0.0/16
    /// Gateway: 10.240.0.1
    /// Agents checks if there is already a default network in the system
    /// if so it calls with the DHCP set to false
    /// otherwise it is set to true an a DHCP for the default network
    /// is started in the node
    async fn create_default_virtual_network(&self, dhcp: bool) -> FResult<VirtualNetwork>;

    /// Creates a virtual network with the given VirtualNetworkConfig in the node
    /// if the network does not globally exists returns an error
    /// if the network already exists iun the node does nothing
    async fn create_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork>;

    /// Gets the virtual network with the specified UUID
    /// if the network is not present in the node returns
    /// an error
    async fn get_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork>;

    /// Removes the virtual network from the node
    /// if this was the last node in the network
    /// the network is removed from the global catalog
    async fn delete_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork>;

    /// Creates a connection point in the node
    async fn create_connection_point(&self) -> FResult<ConnectionPoint>;

    /// Gets the connection point with the specified UUID
    async fn get_connection_point(&self, cp_uuid: Uuid) -> FResult<ConnectionPoint>;

    /// Removes the connection point from the node
    async fn delete_connection_point(&self, cp_uuid: Uuid) -> FResult<Uuid>;

    /// Creates a virtual interface in the nodes
    /// following the given VirtualInterfaceConfig
    /// if an interface with same UUID already exists
    /// it does nothing
    async fn create_virtual_interface(
        &self,
        intf: VirtualInterfaceConfig,
    ) -> FResult<VirtualInterface>;

    /// Gets the virtual interface matching the UUID
    async fn get_virtual_interface(&self, intf_uuid: Uuid) -> FResult<VirtualInterface>;

    /// Removes the virtual interface from the node
    async fn delete_virtual_interface(&self, intf_uuid: Uuid) -> FResult<VirtualInterface>;

    /// Creates a virtual bridge, this is a shortcut for
    /// create_virtual_interface with Kind Bridge
    /// if an interface with same name already exists
    /// otherwise do nothing
    async fn create_virtual_bridge(&self, br_name: String) -> FResult<VirtualInterface>;

    /// Gets the virtual bridge matching the UUID
    /// if the interface matching the UUID is not
    /// a virtual bridge returns an error
    async fn get_virtual_bridge(&self, br_uuid: Uuid) -> FResult<VirtualInterface>;

    /// Removes the virtual bridge matching the UUID
    /// if the interface matching the UUID is not
    /// a virtual bridge returns an error
    async fn delete_virtual_bridge(&self, br_uuid: Uuid) -> FResult<VirtualInterface>;

    /// Creates a new network namespace in the node
    async fn create_network_namespace(&self) -> FResult<NetworkNamespace>;

    /// Gets the network namespace matching the given UUID
    async fn get_network_namespace(&self, ns_uuid: Uuid) -> FResult<NetworkNamespace>;

    /// Removes the network namespace matching the given UUID
    async fn delete_network_namespace(&self, ns_uuid: Uuid) -> FResult<NetworkNamespace>;

    /// Binds the interface to the given connection point
    async fn bind_interface_to_connection_point(
        &self,
        intf_uuid: Uuid,
        cp_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Unbinds the interfaces from the given connection point
    /// if they are not binded returns an error
    async fn unbind_interface_from_connection_point(
        &self,
        intf_uuid: Uuid,
        cp_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Binds the connection point to the given virtual network
    async fn bind_connection_point_to_virtual_network(
        &self,
        cp_uuid: Uuid,
        vnet_uuid: Uuid,
    ) -> FResult<ConnectionPoint>;

    /// Unbinds the connection point from the virtual networks
    /// if they are not connected returns an error
    async fn unbind_connection_point_from_virtual_network(
        &self,
        cp_uuid: Uuid,
        vnet_uuid: Uuid,
    ) -> FResult<ConnectionPoint>;

    /// Gets the addresses of the given interface
    async fn get_interface_addresses(&self, intf_uuid: Uuid) -> FResult<Vec<IPAddress>>;

    /// Gets the interface configured for Overlay networking
    async fn get_overlay_iface(&self) -> FResult<String>;

    /// Gets the interface configured for VLANs
    async fn get_vlan_face(&self) -> FResult<String>;

    /// Creates a MACVLAN interface, shortcut
    /// to create_virtual_interface with MACVLAN kind
    /// if an interface with same UUID already exists
    /// and it is not MACVLAN returns an error
    /// otherwise do nothing
    async fn create_macvlan_interface(&self, master_intf: String) -> FResult<VirtualInterface>;

    /// Removes the MACVLAN interface matching the UUID
    /// if the interface matching is not a MACVLAN
    /// returns an error
    async fn delete_macvan_interface(&self, intf_uuid: Uuid) -> FResult<VirtualInterface>;

    /// Moves the given interface into the given network namespace
    async fn move_interface_info_namespace(
        &self,
        intf_uuid: Uuid,
        ns_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Moves the given interface into the default namespace
    async fn move_interface_into_default_namespace(
        &self,
        intf_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Renames the given interface
    async fn rename_virtual_interface(
        &self,
        intf_uuid: Uuid,
        intf_name: String,
    ) -> FResult<VirtualInterface>;

    /// Attaches the given interface to the given bridge
    async fn attach_interface_to_bridge(
        &self,
        intf_uuid: Uuid,
        br_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Detaches the given interface from the given bridge
    async fn detach_interface_from_bridge(
        &self,
        intf_uuid: Uuid,
        br_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Creates a virtual interface in the given namespace
    async fn create_virtual_interface_in_namespace(
        &self,
        intf: VirtualInterfaceConfig,
        ns_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Deletes the given virtual interface from the given namespace
    async fn delete_virtual_interface_in_namespace(
        &self,
        intf_uuid: Uuid,
        ns_uuid: Uuid,
    ) -> FResult<VirtualInterface>;

    /// Assigns the given address to the given interface
    async fn assing_address_to_interface(
        &self,
        intf_uuid: Uuid,
        address: Option<IpNetwork>,
    ) -> FResult<VirtualInterface>;

    /// Retains the given address from the given interface
    async fn remove_address_from_interface(
        &self,
        intf_uuid: Uuid,
        address: IPAddress,
    ) -> FResult<VirtualInterface>;

    /// Sets the MACAddress for the given interface
    async fn set_macaddres_of_interface(
        &self,
        intf_uuid: Uuid,
        address: MACAddress,
    ) -> FResult<VirtualInterface>;
}

#[zservice(
    timeout_s = 60,
    prefix = "/fos/local",
    service_uuid = "00000000-0000-0000-0000-000000000005"
)]
pub trait HypervisorPlugin {
    /// Defines the given FDU in the node
    async fn define_fdu(&mut self, fdu: FDUDescriptor) -> FResult<FDURecord>;

    /// Undefines the given instance
    async fn undefine_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid>;

    /// Configures the given instance
    async fn configure_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid>;

    /// Cleans the given instance
    async fn clean_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid>;

    /// Starts the given instance
    async fn start_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid>;

    /// Runs the given instance in a BLOCKING mode
    async fn run_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid>; //this should be somehow blocking...

    /// Gets log of the given instance, what log means depend on the FDU
    /// may be left unimplemented
    async fn log_fdu(&mut self, instance_uuid: Uuid) -> FResult<String>;

    /// Lists files in the instance, may be left unimplemented, depends on the FDU
    async fn ls_fdu(&mut self, instance_uuid: Uuid) -> FResult<Vec<String>>;

    /// Gets the specified file from the instance, may be left unimplemented
    /// depends on th FDU
    async fn file_fdu(&mut self, instance_uuid: Uuid, file_name: String) -> FResult<String>;

    /// Stops the given instance
    async fn stop_fdu(&mut self, instance_uuid: Uuid) -> FResult<Uuid>;

    /// Migrates the instance to destination node
    async fn migrate_fdu(&mut self, instance_uuid: Uuid, destination_uuid: Uuid) -> FResult<Uuid>;

    /// Gets the status of the instance from the hypervisor
    async fn get_fdu_status(&self, instance_uuid: Uuid) -> FResult<FDURecord>;
}
