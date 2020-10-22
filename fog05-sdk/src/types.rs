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

use uuid::Uuid;
use serde::{Deserialize,Serialize};



pub type IPAddress = std::net::IpAddr; //this is just address, to investigate if we want CIRD notation in address to have the netmask
// pub type MACAddress = mac_address::MacAddress;

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct MACAddress {
    bytes: [u8; 6],
}

/// Link kind supported by netlink
/// https://github.com/little-dude/netlink/blob/master/netlink-packet-route/src/rtnl/link/nlas/link_infos.rs
#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum VirtualInterfaceKind{
    VETH,
    VLAN,
    BRIDGE,
    VXLAN,
    GRE,
    GRETAP,
    IP6GRE,
    IP6GRETAP,
    MACVLAN, //we always use mode VEPA
}


/// A virtual interface managed by fog05
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualInterface {
    pub uuid : Uuid,
    pub if_name : String,
    pub net_ns : Option<NetworkNamespace>, //if none interface is in default namespace
    pub kind : VirtualInterfaceKind,
    pub pair : Option<Uuid>, // in case of VETH pairs, ref to VirtualInterface
    pub internal : Option<bool>, // in case of VETH to identify the one that goes to FDU
    pub childs : Option<Vec<Uuid>>, //in case of BRIDGE, refs to VirtualInterface
    pub vni : Option<u32>, //in case of VXLAN, we have to bound it to u24...
    pub mcast_addr : Option<IPAddress>, //in case of VXLAN, verify it is multicast
    pub port : Option<u32>, //in case of VXLAN
    pub tag : Option<u16>, //in case of VLAN
    pub parent : Option<Uuid>, //present if the interface is under a BRIDGE, ref to VirtualInterface
    pub dev : Option<Interface>, //physical interface used by the VXLAN/MACVLAN/VLAN can be present also for GREs but they will just use addresses, maybe just String
    pub local_addr : Option<IPAddress>, // for GRE, IP6GRE, GRETAP, IP6GRETAP
    pub remote_addr : Option<IPAddress>, // for GRE, IP6GRE, GRETAP, IP6GRETAP
    pub ttl : Option<u8>, //for GRE, IP6GRE, GRETAP, IP6GRETAP

    pub addresses : Vec<IPAddress>,
    pub phy_address : MACAddress,
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
    pub phy_address : Option<MACAddress>,

}
