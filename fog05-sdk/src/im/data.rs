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

use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Clone, PartialEq, Eq, Debug, Hash, Serialize, Deserialize)]
pub enum ComponentStatus {
    HALTED = 0,
    CONNECTED = 1,
    BUILDING = 2,
    REGISTERED = 3,
    ANNOUNCED = 4,
    WORK = 5,
    UNWORK = 6,
    UNANNOUNCED = 7,
    UNREGISTERED = 8,
    DISCONNECTED = 9,
}

#[derive(PartialEq, Clone, Serialize, Deserialize, Debug)]
pub struct ComponentAdvertisement {
    pub uuid: Uuid,
    pub name: String,
    pub routerid: String,
    pub peerid: String,
}

#[derive(PartialEq, Clone, Serialize, Deserialize, Debug)]
pub struct ComponentInformation {
    pub uuid: Uuid,
    pub name: String,
    pub routerid: String,
    pub peerid: String,
    pub status: ComponentStatus,
}
