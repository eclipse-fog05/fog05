// /*********************************************************************************
// * Copyright (c) 2018,2020 ADLINK Technology Inc.
// *
// * This program and the accompanying materials are made available under the
// * terms of the Eclipse Public License 2.0 which is available at
// * http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
// * which is available at https://www.apache.org/licenses/LICENSE-2.0.
// *
// * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
// * Contributors:
// *   ADLINK fog05 team, <fog05@adlink-labs.tech>
// *********************************************************************************/
#![allow(non_camel_case_types)]

extern crate derive_more;
extern crate serde;
extern crate serde_aux;
extern crate serde_json;
extern crate serde_yaml;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use fog05_sdk::im::entity::{EntityDescriptor, EntityRecord};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Job {
    pub job_id: String,
    pub original_sender: String,
    pub kind: String,
    pub body: String,
    pub status: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RequestNewJobMessage {
    pub sender: String,
    pub job_kind: String,
    pub body: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ReplyNewJobMessage {
    pub original_sender: String,
    pub accepted: bool,
    pub job_id: String,
    pub body: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EntityActionBody {
    pub uuid: Uuid,
    pub fim_id: Option<Uuid>,
    pub cloud_id: Option<Uuid>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetInstanceResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub entity: Uuid,
    pub instance: EntityRecord,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetInstancesResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub entity: Uuid,
    pub instances: Vec<Uuid>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetEntityResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub entity: EntityDescriptor,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetEntitiesResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub entities: Vec<Uuid>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetCloudsResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub clouds: Vec<Uuid>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetFIMsResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub fims: Vec<Uuid>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetFIMResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub fim: FIMInfo,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GetCloudResponse {
    pub system: Uuid,
    pub tenant: Uuid,
    pub cloud: CloudInfo,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FIMInfo {
    pub uuid: Uuid,
    pub locator: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CloudInfo {
    pub uuid: Uuid,
    pub config: String, //K8s client config
    pub ca: String,     //base64 of CA data
    pub cert: String,   //base64 of Client Certificate
    pub key: String,    //base64 of Client Key
}

// // Descriptors
// #[derive(Serialize, Deserialize, Debug, Clone)]
// #[serde(rename_all = "UPPERCASE")]
// pub enum MigrationKind {
//     LIVE,
//     COLD,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// #[serde(rename_all = "UPPERCASE")]
// pub enum ConfigurationKind {
//     SCRIPT,
//     ENV,
//     CLOUD_INIT,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// #[serde(rename_all = "UPPERCASE")]
// pub enum InterfaceKind {
//     VIRTUAL,
//     WLAN,
//     BLUETOOTH,
// }

// #[derive(Serialize, Deserialize, Debug, Clone, Display)]
// #[serde(rename_all = "UPPERCASE")]
// pub enum VirtualInterfaceKind {
//     PARAVIRT,
//     PCI_PASSTHROUGH,
//     SR_IOV,
//     VIRTIO, //default
//     E1000,
//     RTL8139,
//     PCNET,
//     BRIDGED,
//     PHYSICAL,
// }

// #[derive(Serialize, Deserialize, Debug, Clone, Display)]
// #[serde(rename_all = "UPPERCASE")]
// pub enum StorageKind {
//     BLOCK, //virtual disk
//     //FILE, //NFS kind of, can be Zenoh+file backend
//     OBJECT, //Zenoh as object storage
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// #[serde(rename_all = "UPPERCASE")]
// pub enum ScalingMetric {
//     CPU,
//     DISK,
//     MEMORY,
//     CUSTOM(String),
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct ScalingPolicy {
//     pub metric: ScalingMetric,
//     pub scale_up_threshold: f32,
//     pub scale_down_threshold: f32,
//     pub threshold_sensibility: u8,
//     pub probe_interval: f32,
//     pub min_replicas: u8,
//     pub max_replicas: u8,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct Position {
//     pub lat: String,
//     pub lon: String,
//     pub radius: f64,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// //or Affinity/Antiaffinity
// pub struct Proximity {
//     pub neighbour: String,
//     pub radius: f64,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct Configuration {
//     pub conf_kind: ConfigurationKind,
//     pub script: Option<String>,   //both for script and cloud_init
//     pub env: Option<Vec<String>>, //VAR=VALUE,
//     pub ssh_keys: Option<Vec<String>>,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct Image {
//     pub uuid: Option<Uuid>,
//     pub name: Option<String>,
//     pub uri: String,
//     pub checksum: String, //SHA256 of image file
//     pub format: String,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct ComputationalRequirements {
//     pub cpu_arch: String,
//     #[serde(default = "default_zero")]
// 	pub cpu_min_freq: u8, //default 0
// 	#[serde(default = "default_one")]
//     pub cpu_min_count: u8, //default 1
//     #[serde(default = "default_zero")]
//     pub gpu_min_count: u8, //default 0
//     #[serde(default = "default_zero")]
//     pub fpga_min_count: u8, //default 0
//     pub ram_size_mb: u32,
//     pub storage_size_mb: u32,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct GeographicalRequirement {
//     pub position: Option<Position>,
//     pub proximity: Option<Vec<Proximity>>,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct VirtualInterface {
//     pub vif_kind: VirtualInterfaceKind,
//     pub parent: Option<String>, //PCI address, bridge name, interface name
//     pub bandwidht: Option<u8>,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct ConnectionPointDescriptor {
//     pub uuid: Option<Uuid>,
//     pub name: String,
//     pub id: String,
//     pub vld_ref: Option<String>, //reference to a virtual link descriptor
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct Interface {
//     pub name: String,
//     pub kind: InterfaceKind,
//     pub mac_address: Option<String>,
//     pub virtual_interface: VirtualInterface,
//     pub cp_id: Option<String>, //internal to this descriptor
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct StorageDescriptor {
//     pub id: String,
//     pub storage_kind: StorageKind,
//     pub size: u32, //depends on the kind, MB for BLOCK, items for OBJECT
// }

// //example pf hypervisor for BARE (Native)
// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct Command {
//     pub binary: String, //can be relative, in that case it is expected to be part of the image of global path
//     pub args: Vec<String>,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct FDUDescriptor {
//     pub uuid: Option<Uuid>,
//     pub id: String,
//     pub name: String,
//     pub version: Version,     //semantic version of the descriptor
//     pub fdu_version: Version, //semantic version of the fdu
//     pub description: Option<String>,
//     pub hypervisor: String, //eg. KVM, LXD, DOCKER, ROS2, BARE, K8s, AWS...
//     pub image: Option<Image>,
//     pub hypervisor_specific: Option<String>,
//     pub computation_requirements: ComputationalRequirements,
//     pub geographical_requirements: Option<GeographicalRequirement>,
//     pub interfaces: Vec<Interface>,
//     pub storage: Vec<StorageDescriptor>,
//     pub connection_points: Vec<ConnectionPointDescriptor>,
//     pub configuration: Option<Configuration>,
//     pub migration_kind: MigrationKind,
//     pub replicas: Option<u8>,
//     //pub scaling_policies : Option<Vec<ScalingPolicy>>,
//     pub depends_on: Vec<String>,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct FDURecord {
//     pub uuid: Uuid,
//     pub id: Uuid,
//     pub status: String,
// }

// // Entity

// #[derive(Serialize, Deserialize, Debug, Clone, Display)]
// pub enum IPVersion {
//     IPV4,
//     IPV6,
// }

// #[derive(Serialize, Deserialize, Debug, Clone, Display)]
// pub enum LinkKind {
//     L2,    //we do a Multicast VXLAN
//     L3,    //we do a GRE (tree-based, one Node receives all GRE connections and bridges)
//     ELINE, //we do a Point-to-Point VXLAN
//     ELAN,  //we do a Multicast VXLAN
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct IPConfiguration {
//     pub subnet: Option<String>,     // AAA.AAA.AAA.AAA/S
//     pub gateway: Option<String>,    // AAA.AAA.AAA.AAA
//     pub dhcp_range: Option<String>, // AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA
//     pub dns: Option<String>,        // AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct VirtualLinkDescriptor {
//     pub id: String,
//     pub name: Option<String>,
//     pub is_mgmt: bool, //MGMT from a user point of view
//     pub link_kind: LinkKind,
//     pub ip_version: IPVersion,
//     pub ip_configuration: Option<IPConfiguration>,
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct EntityDescriptor {
//     pub uuid: Option<Uuid>, //verify if there is a UUID crate compatible with Serialize, Deserialize if not present is generated at onboarding in the catalog
//     pub id: String,         // eg. foo.bar.my.entity
//     pub version: Version,    // semantic versioning of the descriptor
//     pub entity_version: Version, //semantic versioning of the entity
//     pub name: String,
//     pub description: Option<String>,
//     pub fdus: Vec<FDUDescriptor>,
//     pub virtual_links: Vec<VirtualLinkDescriptor>,
// }

// // Record

// #[derive(Serialize, Deserialize, Debug, Clone, Display)]
// pub enum EntityStatus {
//     ONBOARDING, //instantiation request received  by orchestrator
//     ONBOARDED,  // instantiation request scheduled
//     STARTING,   //start instantiation
//     RUNNING,    //
//     STOPPING,   //
//     STOPPED,    //fdu are there but not running
//     OFFLOADING, // removing fdu/virtual links
//     OFFLOADED,  // removed, still in registry
//     INVALID,    //error in descriptor
//     ERROR,      //generic error state
//     RECOVERING, //from an ERROR from RUNNING recovering from a recoverable error (eg. fdu an went down)
// }

// #[derive(Serialize, Deserialize, Debug, Clone)]
// pub struct EntityRecord {
//     pub uuid: Uuid,
//     pub id: String, //ref to EntityDescriptor.UUID
//     pub status: EntityStatus,
//     pub fdus: Vec<Uuid>,
//     pub virtual_links: Vec<Uuid>,
//     pub fim_id: Option<Uuid>,
//     pub cloud_id: Option<Uuid>,
// }
