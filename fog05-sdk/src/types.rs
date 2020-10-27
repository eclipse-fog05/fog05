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

extern crate serde;
extern crate mac_address;

use derive_more::Display;
use uuid::Uuid;
use serde::{Deserialize,Serialize};



pub type IPAddress = std::net::IpAddr; //this is just address, to investigate if we want CIRD notation in address to have the netmask
// pub type MACAddress = mac_address::MacAddress;

// #[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
// pub struct MACAddress {
//     bytes: [u8; 6],
// }

//Types used in the VirtualInterfaceKind enum

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum PluginKind {
    NETWORKING,
    FDU,
    IO,
    ACCELERATOR,
    GPS,
}


#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VETHKind {
    pub pair : Uuid,
    pub internal : bool,
    pub dev : Interface,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VLANKind {
    pub tag : u16,
    pub dev : Interface,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VXLANKind {
    pub vni : u32, //actually should be u24
    pub mcast_addr : IPAddress,
    pub port : u16,
    pub dev : Interface,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct BridgeKind {
    pub childs : Vec<Uuid>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GREKind {
    pub local_addr : IPAddress,
    pub remote_addr : IPAddress,
    pub ttl : u8,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MACVLANKind {
    pub dev : Interface,
}


/// Link kind supported by netlink
/// https://github.com/little-dude/netlink/blob/master/netlink-packet-route/src/rtnl/link/nlas/link_infos.rs
#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum VirtualInterfaceKind{
    VETH(VETHKind),
    VLAN(VLANKind),
    BRIDGE(BridgeKind),
    VXLAN(VXLANKind),
    GRE(GREKind),
    GRETAP(GREKind),
    IP6GRE(GREKind),
    IP6GRETAP(GREKind),
    MACVLAN(VXLANKind), //we always use mode VEPA
}




/// A virtual interface managed by fog05
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualInterface {
    pub uuid : Uuid,
    pub if_name : String,
    pub net_ns : Option<NetworkNamespace>, //if none interface is in default namespace
    pub kind : VirtualInterfaceKind,
    pub parent : Option<Uuid>, //present if the interface is under a BRIDGE, ref to VirtualInterface

    pub addresses : Vec<IPAddress>,
    pub phy_address : mac_address::MacAddress,
}

/// A network namespace managed by fog05
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct NetworkNamespace {
    pub uuid : Uuid,
    pub ns_name : String,
    pub interfaces : Vec<Uuid>, //refs to VirtualInterface

}

/// A connection point is a bridge and a veth inside a namespace
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConnectionPoint {
    pub uuid : Uuid,
    pub net_ns : Uuid, //ref to NetworkNamespace
    pub bridge : Uuid, // FDUs veth external connects to this, ref to VirtualInterface
    pub internal_veth : Uuid, //this is always connected to the bridge, ref to VirtualInterface
    pub external_veth : Uuid, //this connectes to external virtual networks/bridges, ref to Virtual Interface
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConnectionPointConfig {
    pub uuid : Uuid,
}



///Interfaces not managed by fog05
#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum InterfaceKind{
    ETHERNET,
    WLAN,
    CAN,
    BRIDGE,
    TUNNEL,
    PTP,
    BLUETOOTH, //understand how to discover those interfaces...
}


/// Interfaces that are not managed by fog05
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Interface {
    pub if_name : String,
    pub kind : InterfaceKind,
    pub addresses : Vec<IPAddress>,
    pub phy_address : Option<mac_address::MacAddress>,

}



#[derive(Serialize, Deserialize, Debug, Clone, Display)]
pub enum IPVersion {
    IPV4,
    IPV6,
}

#[derive(Serialize, Deserialize, Debug, Clone, Display)]
pub enum LinkKind {
    L2,    //we do a Multicast VXLAN
    L3,    //we do a GRE (tree-based, one Node receives all GRE connections and bridges)
    ELINE, //we do a Point-to-Point VXLAN
    ELAN,  //we do a Multicast VXLAN
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct IPConfiguration {
    pub subnet: Option<(IPAddress,u8)>,     // AAA.AAA.AAA.AAA/S
    pub gateway: Option<IPAddress>,    // AAA.AAA.AAA.AAA
    pub dhcp_range: Option<(IPAddress,IPAddress)>, // AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA
    pub dns: Option<Vec<IPAddress>>,        // AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualNetwork {
    pub uuid : Uuid,
    pub id: String,
    pub name: Option<String>,
    pub is_mgmt: bool, //MGMT from a user point of view
    pub link_kind: LinkKind,
    pub ip_version: IPVersion,
    pub ip_configuration: Option<IPConfiguration>,
    pub connection_points : Vec<Uuid>,
}


#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualNetworkConfig {
    pub uuid : Option<Uuid>,
    pub id: String,
    pub name: Option<String>,
    pub is_mgmt: bool, //MGMT from a user point of view
    pub link_kind: LinkKind,
    pub ip_version: IPVersion,
    pub ip_configuration: Option<IPConfiguration>,
}