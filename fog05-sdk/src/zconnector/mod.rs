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

extern crate bincode;
extern crate hex;
extern crate serde;

use std::convert::TryInto;
use std::convert::TryFrom;
use super::im::data::*;
use async_std::sync::{Mutex,Arc};
use zenoh::*;
use futures::prelude::*;
use thiserror::Error;
use std::fmt;
use log::{info, trace, warn, error, debug};
use serde::{Serialize,de::DeserializeOwned};
use uuid::Uuid;
use std::str::FromStr;


static GLOBAL_ACTUAL_PREFIX: &str = "/agfos";
static GLOBAL_DESIRED_PREFIX:  &str = "/dgfos";
static LOCAL_ACTUAL_PREFIX:  &str = "/alfos";
static LOCAL_DESIRED_PREFIX:  &str = "/dlfos";
static LOCAL_CONSTRAINT_ACTUAL_PREFIX:  &str = "/aclfos";
static LOCAL_CONSTRAINT_DESIRED_PREFIX:  &str = "/dclfos";

/// Default systemid is 00000000-0000-0000-0000-000000000000
static DEFAULT_SYSTEM_ID : Uuid = Uuid::nil();
static DEFAULT_TENANT_ID : Uuid = Uuid::nil();



// Strings and prefix can be converted to int to reduce the amount of data in zenoh, eg /agfos = /0

macro_rules!  SYS_INFO_PATH { ($prefix:expr, $sysid:expr) => { format!("{}/{}/info", $prefix,$sysid) }; }
macro_rules!  SYS_CONF_PATH { ($prefix:expr, $sysid:expr) => { format!("{}/{}/configuration", $prefix,$sysid) }; }

macro_rules!  SYS_USER_SELECTOR { ($prefix:expr, $sysid:expr) => { format!("{}/{}/users/*", $prefix,$sysid) }; }
macro_rules!  SYS_USER_INFO { ($prefix:expr, $sysid:expr, $userid:expr) => { format!("{}/{}/users/{}/info", $prefix,$sysid,$userid) }; }

macro_rules!  TENANTS_SELECTOR { ($prefix:expr, $sysid:expr) => { format!("{}/{}/tenants/*", $prefix,$sysid) }; }
macro_rules!  TENANT_INFO_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr) => { format!("{}/{}/tenants/{}/info", $prefix,$sysid,$tenantid) }; }
macro_rules!  TENANT_CONF_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr) => { format!("{}/{}/tenants/{}/configuration", $prefix,$sysid,$tenantid) }; }

macro_rules!  NODES_SELECTOR { ($prefix:expr, $sysid:expr, $tenantid:expr) => { format!("{}/{}/tenants/{}/nodes/*/info", $prefix,$sysid,$tenantid) }; }
macro_rules!  NODE_INFO_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/info", $prefix,$sysid,$tenantid,$nodeid) }; }
macro_rules!  NODE_CONF_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/configuration", $prefix,$sysid,$tenantid,$nodeid) }; }
macro_rules!  NODE_STATUS_PATH { ($prefix:expr, $sysid:expr, $tenantid:expr, $nodeid:expr) => { format!("{}/{}/tenants/{}/nodes/{}/status", $prefix,$sysid,$tenantid,$nodeid) }; }



