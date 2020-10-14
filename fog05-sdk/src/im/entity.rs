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
extern crate serde_aux;
extern crate serde_json;
extern crate serde_yaml;


use derive_more::Display;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use semver::Version;


// Entity

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
    pub subnet: Option<String>,     // AAA.AAA.AAA.AAA/S
    pub gateway: Option<String>,    // AAA.AAA.AAA.AAA
    pub dhcp_range: Option<String>, // AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA
    pub dns: Option<String>,        // AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA,AAA.AAA.AAA.AAA
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct VirtualLinkDescriptor {
    pub id: String,
    pub name: Option<String>,
    pub is_mgmt: bool, //MGMT from a user point of view
    pub link_kind: LinkKind,
    pub ip_version: IPVersion,
    pub ip_configuration: Option<IPConfiguration>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EntityDescriptor {
    pub uuid: Option<Uuid>, //verify if there is a UUID crate compatible with Serialize, Deserialize if not present is generated at onboarding in the catalog
    pub id: String,         // eg. foo.bar.my.entity
    pub version: Version,    // semantic versioning of the descriptor
    pub entity_version: Version, //semantic versioning of the entity
    pub name: String,
    pub description: Option<String>,
    pub fdus: Vec<super::fdu::FDUDescriptor>,
    pub virtual_links: Vec<VirtualLinkDescriptor>,
}

// Record

#[derive(Serialize, Deserialize, Debug, Clone, Display)]
pub enum EntityStatus {
    ONBOARDING, //instantiation request received  by orchestrator
    ONBOARDED,  // instantiation request scheduled
    STARTING,   //start instantiation
    RUNNING,    //
    STOPPING,   //
    STOPPED,    //fdu are there but not running
    OFFLOADING, // removing fdu/virtual links
    OFFLOADED,  // removed, still in registry
    INVALID,    //error in descriptor
    ERROR,      //generic error state
    RECOVERING, //from an ERROR from RUNNING recovering from a recoverable error (eg. fdu an went down)
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EntityRecord {
    pub uuid: Uuid,
    pub id: String, //ref to EntityDescriptor.UUID
    pub status: EntityStatus,
    pub fdus: Vec<Uuid>,
    pub virtual_links: Vec<Uuid>,
    pub fim_id: Option<Uuid>,
    pub cloud_id: Option<Uuid>,
}