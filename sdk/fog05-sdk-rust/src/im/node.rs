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
extern crate serde_json;
extern crate serde_yaml;

use serde::{Serialize, Deserialize};

// Node Information

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct CPUSpec {
    pub model : String,
    pub frequency : f64,
    pub arch : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct RAMSpec {
    pub size : f64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct DiskSpec {
    pub local_address : String,
    pub dimension : f64,
    pub mount_point : String,
    pub file_system : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct IOSpec {
    pub name : String,
    pub io_type : String,
    pub io_file : String,
    pub available : bool
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct VolatilitySpec {
    pub avg_availability_minutes : u64,
    pub quartile_availability_minutes : Vec<u64>
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct AcceleratorSpec {
    pub hw_address : String,
    pub name : String,
    pub supported_libraries : Vec<String>,
    pub available : bool
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct PositionSpec {
    pub lat : f64,
    pub lon : f64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct InterfaceConfiguration {
    pub ipv4_address : String,
    pub ipv4_netmask : String,
    pub ipv4_gateway : String,
    pub ipv6_address : String,
    pub ipv6_netmask : String,
    pub ipv6_gateway : Option<String>,
    pub bus_address : Option<String>
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct NodeInfo {
    pub uuid : String,
    pub name : String,
    pub os : String,
    pub cpu : Vec<CPUSpec>,
    pub ram : RAMSpec,
    pub disks : Vec<DiskSpec>,
    pub io : Vec<IOSpec>,
    pub accelerators : Vec<AcceleratorSpec>,
    pub position : Option<PositionSpec>,
    pub volatility : Option<VolatilitySpec>

}

// Node Monitoring

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct RAMStatus {
    pub total : f64,
    pub free : f64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct DiskStatus {
    pub mount_point : String,
    pub total : f64,
    pub free : f64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct NeighborPeerInfo {
    pub name : String,
    pub id : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct NeighborInfo {
    pub node : NeighborPeerInfo,
    pub port : NeighborPeerInfo
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct Neighbor {
    pub src : NeighborInfo,
    pub dst : NeighborInfo
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct PingInfo {
    pub peer : String,
    pub average : f64,
    pub ip : String,
    pub iface : String,
    pub packet_loss : f64,
    pub packet_sent : u64,
    pub packet_received : u64,
    pub bytes_sent : u64,
    pub bytes_received : u64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct HeartbeatInfo {
    pub nodeid : String
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct NodeStatus {
    pub uuid : String,
    pub ram : RAMStatus,
    pub disk : DiskStatus,
    pub neighbors : Vec<Neighbor>
}