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


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct SystemInfo {
    pub name : String,
    pub uuid : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct SystemConfig {
    pub config : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct TenantInfo {
    pub name : String,
    pub uuid : String
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub enum IPKind {
    IPV4,
    IPV6
}