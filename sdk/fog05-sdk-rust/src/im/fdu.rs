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

// FDU Generic

#[derive(Serialize,Deserialize,Debug, Clone)]
pub enum FDUState {
    DEFINE,
    CONFIGURE,
    CLEAN,
    RUN,
    STARTING,
    STOP,
    RESUME,
    PAUSE,
    SCALE,
    TAKE_OFF,
    LAND,
    MIGRATE,
    UNDEFINE,
    ERROR
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub enum MigrationKind {
    LIVE,
    COLD
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub enum VirtualInterfaceKind {
    PARAVIRT,
    FOS_MGMT,
    PCI_PASSTHROUGH,
    SR_IOV,
    VIRTIO,
    E1000,
    RTL8139,
    PCNET,
    PHYSICAL,
    BRIDGED
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub enum InterfaceKind {
    INTERNAL,
    EXTERNAL,
    WLAN,
    BLUETOOTH
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub enum StorageKind {
    BLOCK,
    FILE,
    OBJECT
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct Image {
    pub uuid : Option<String>,
    pub name : Option<String>,
    pub uri :  String,
    pub checksum : String, //SHA256SUM
    pub format : String
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct Position {
    pub lat : String,
    pub lon : String,
    pub radius : f64
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct Proximity {
    pub neighbor : String,
    pub radius : f64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct GeographicalRequirements {
    position : Option<Position>,
    proximity : Option<Vec<Proximity>>
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ComputationalRequirements {
    pub uuid : Option<String>,
    pub name : Option<String>,
    pub cpu_arch : String,
    pub cpu_min_freq : u64,
    pub cpu_min_count : u64,
    pub gpu_min_count : Option<u64>,
    pub fpga_min_count : Option<u64>,
    pub ram_size_mb : f64,
    pub storage_size_gb : f64,
    pub duty_cycle : Option<f64>
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct VirtualInterface {
    pub intf_type : VirtualInterfaceKind,
    pub vpci : String
    pub bandwidth : Option<u64>
}

// User FDU - Descriptor



#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct FDUDescriptorInterface {
    pub name : String,
    pub is_mgmt : bool,
    pub if_type : InterfaceKind,
    pub mac_address : Option<String>,
    pub virtual_interface : VirtualInterface,
    pub cp_id : Option<String>,
    pub ext_cp_id : Option<String>

}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct Descriptor {
    pub id : String,
    pub name : String,
    pub uuid : Option<String>,
    pub description : Option<String>,
    pub image : Option<Image>,
    pub compute_requirements : ComputationalRequirements,
    pub interfaces : Vec<FDUDescriptorInterface>,
    pub ssh_keys : Vec<String>,
    pub hypervisor : String, //eg. Docker, KVM, LXD, ROS2, Native ...
    pub migration_kind : MigrationKind,
    pub geographic_requirement : Option<GeographicalRequirements>,
    pub properties : Option<String>,
}

// FDU Record


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct FDURecordInterface {
    pub is_mgmt : bool,
    pub if_type : InterfaceKind,
    pub mac_address : Option<String>,
    pub virtual_interface : VirtualInterface,
    pub cp_id : Option<String>,
    pub ext_cp_id : Option<String>

    pub vintf_name : String,
    pub status : String,
    pub phy_iface : Option<String>,
    pub veth_iface_name : Option<String>,
    pub properties : String,
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct FDUMigrationProperties {
    pub destination : String,
    pub source : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct Record {
    pub uuid : String,
    pub fdu_id : String,
    pub status : FDUState,
    pub image : Option<Image>,
    pub compute_requirements : ComputationalRequirements,
    pub interfaces : Vec<FDURecordInterface>,
    pub ssh_keys : Vec<String>,
    pub hypervisor : String, //eg. Docker, KVM, LXD, ROS2, Native ...
    pub migration_kind : MigrationKind,
    pub geographic_requirement : Option<GeographicalRequirements>,
    pub properties : Option<String>,
    pub error_code : Option<u64>,
    pub error_msg : Option<String>,
    pub migration_properties : Option<FDUMigrationProperties>,
    pub hypervisor_info : String,
}