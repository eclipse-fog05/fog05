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

#![allow(non_camel_case_types)]

extern crate derive_more;
extern crate serde;

use derive_more::Display;
use semver::Version;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

fn default_zero() -> u8 {
    0
}

fn default_zero_u64() -> u64 {
    0
}

fn default_one() -> u8 {
    1
}

// FDU Generic

// Descriptors
#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum MigrationKind {
    LIVE,
    COLD,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum ConfigurationKind {
    SCRIPT,
    ENV,
    CLOUD_INIT,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum InterfaceKind {
    VIRTUAL,
    WLAN,
    BLUETOOTH,
}

#[derive(Serialize, Deserialize, Debug, Clone, Display)]
#[serde(rename_all = "UPPERCASE")]
pub enum VirtualInterfaceKind {
    PARAVIRT,
    PCI_PASSTHROUGH,
    SR_IOV,
    VIRTIO, //default
    E1000,
    RTL8139,
    PCNET,
    BRIDGED,
    PHYSICAL,
}

#[derive(Serialize, Deserialize, Debug, Clone, Display)]
#[serde(rename_all = "UPPERCASE")]
pub enum StorageKind {
    BLOCK, //virtual disk
    //FILE, //NFS kind of, can be Zenoh+file backend
    OBJECT, //Zenoh as object storage
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "UPPERCASE")]
pub enum ScalingMetric {
    CPU,
    DISK,
    MEMORY,
    CUSTOM(String),
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ScalingPolicy {
    pub metric: ScalingMetric,
    pub scale_up_threshold: f32,
    pub scale_down_threshold: f32,
    pub threshold_sensibility: u8,
    pub probe_interval: f32,
    pub min_replicas: u8,
    pub max_replicas: u8,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Position {
    pub lat: String,
    pub lon: String,
    pub radius: f64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
//or Affinity/Antiaffinity
pub struct Proximity {
    pub neighbour: String,
    pub radius: f64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Configuration {
    pub conf_kind: ConfigurationKind,
    pub script: Option<String>,   //both for script and cloud_init
    pub env: Option<Vec<String>>, //VAR=VALUE,
    pub ssh_keys: Option<Vec<String>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Image {
    pub uuid: Option<Uuid>,
    pub name: Option<String>,
    pub uri: String,
    pub checksum: String, //SHA256 of image file
    pub format: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ComputationalRequirements {
    pub cpu_arch: String,
    #[serde(default = "default_zero_u64")]
    pub cpu_min_freq: u64, //default 0 in MHz
    #[serde(default = "default_one")]
    pub cpu_min_count: u8, //default 1
    #[serde(default = "default_zero")]
    pub gpu_min_count: u8, //default 0
    #[serde(default = "default_zero")]
    pub fpga_min_count: u8, //default 0
    pub operating_system: Option<String>,
    pub ram_size_mb: u32,
    pub storage_size_mb: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GeographicalRequirement {
    pub position: Option<Position>,
    pub proximity: Option<Vec<Proximity>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualInterface {
    pub vif_kind: VirtualInterfaceKind,
    pub parent: Option<String>, //PCI address, bridge name, interface name
    pub bandwidht: Option<u8>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConnectionPointDescriptor {
    pub uuid: Option<Uuid>,
    pub name: String,
    pub id: String,
    pub vld_ref: Option<String>, //reference to a virtual link descriptor
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Interface {
    pub name: String,
    pub kind: InterfaceKind,
    pub mac_address: Option<crate::types::MACAddress>,
    pub virtual_interface: VirtualInterface,
    pub cp_id: Option<String>, //internal to this descriptor
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct StorageDescriptor {
    pub id: String,
    pub storage_kind: StorageKind,
    pub size: u32, //depends on the kind, MB for BLOCK, items for OBJECT
}

//example pf hypervisor for BARE (Native)
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Command {
    pub binary: String, //can be relative, in that case it is expected to be part of the image of global path
    pub args: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FDUDescriptor {
    pub uuid: Option<Uuid>,
    pub id: String,
    pub name: String,
    pub version: Version,     //semantic version of the descriptor
    pub fdu_version: Version, //semantic version of the fdu
    pub description: Option<String>,
    pub hypervisor: String, //eg. KVM, LXD, DOCKER, ROS2, BARE, K8s, AWS...
    pub image: Option<Image>,
    pub hypervisor_specific: Option<String>,
    pub computation_requirements: ComputationalRequirements,
    pub geographical_requirements: Option<GeographicalRequirement>,
    pub interfaces: Vec<Interface>,
    pub storage: Vec<StorageDescriptor>,
    pub connection_points: Vec<ConnectionPointDescriptor>,
    pub configuration: Option<Configuration>,
    pub migration_kind: MigrationKind,
    pub replicas: Option<u8>,
    //pub scaling_policies : Option<Vec<ScalingPolicy>>,
    pub depends_on: Vec<String>,
}

// FDU Record

#[derive(Serialize, Deserialize, Debug, Clone, Display)]
#[serde(rename_all = "UPPERCASE")]
pub enum FDUState {
    DEFINED,
    CONFIGURED,
    RUNNING,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FDURecord {
    pub uuid: Uuid,
    pub fdu_uuid: Uuid,
    pub node: Uuid,
    pub interfaces: Vec<FDURecordInterface>,
    pub connection_points: Vec<FDURecordConnectionPoint>,
    pub status: FDUState,
    pub error: Option<crate::fresult::FError>,
    pub hypervisor_specific: Option<Vec<u8>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FDURecordInterface {
    pub name: String,
    pub kind: InterfaceKind,
    pub mac_address: Option<crate::types::MACAddress>,
    pub virtual_interface: FDURecordVirtualInterface,
    pub cp_uuid: Option<Uuid>, //internal to this descriptor
    pub intf_uuid: Uuid,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FDURecordVirtualInterface {
    pub vif_kind: VirtualInterfaceKind,
    pub bandwidht: Option<u8>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FDURecordConnectionPoint {
    pub uuid: Uuid,
    pub id: String,
}

// #[derive(Serialize,Deserialize,Debug, Clone)]
// pub struct FDUMigrationProperties {
//     pub destination : String,
//     pub source : String
// }

// #[derive(Serialize,Deserialize,Debug, Clone)]
// pub struct Record {
//     pub uuid : String,
//     pub fdu_id : String,
//     pub status : FDUState,
//     pub image : Option<Image>,
//     pub compute_requirements : ComputationalRequirements,
//     pub interfaces : Vec<FDURecordInterface>,
//     pub ssh_keys : Vec<String>,
//     pub hypervisor : String, //eg. Docker, KVM, LXD, ROS2, Native ...
//     pub migration_kind : MigrationKind,
//     pub geographic_requirement : Option<GeographicalRequirement>,
//     pub properties : Option<String>,
//     pub error_code : Option<u64>,
//     pub error_msg : Option<String>,
//     pub migration_properties : Option<FDUMigrationProperties>,
//     pub hypervisor_info : String,
// }
