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
#![allow(clippy::upper_case_acronyms)]

pub mod im;
pub mod zconnector;

pub mod agent;
pub mod fresult;
pub mod plugins;
pub mod types;

pub mod api;

pub fn get_node_uuid() -> crate::fresult::FResult<uuid::Uuid> {
    let node_id_raw = machine_uid::get()?;
    let node_str: &str = &node_id_raw;
    Ok(uuid::Uuid::parse_str(node_str)?)
}
