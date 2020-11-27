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

#[cfg(any(
    feature = "resp_bincode",
    feature = "state_bincode",
    feature = "send_bincode"
))]
extern crate bincode;

#[cfg(any(feature = "send_json", feature = "state_json", feature = "resp_json"))]
extern crate serde_json;

use serde::{de::DeserializeOwned, Serialize};

use crate::zrpcresult::ZRPCResult;

pub fn serialize_response<T>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: ?Sized + Serialize,
{
    #[cfg(feature = "resp_bincode")]
    Ok(bincode::serialize(data)?)
}

pub fn deserialize_response<T>(raw_data: &[u8]) -> ZRPCResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "resp_bincode")]
    Ok(bincode::deserialize::<T>(&raw_data)?)
}

pub fn serialize_state<T>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: ?Sized + Serialize,
{
    #[cfg(feature = "state_bincode")]
    return Ok(bincode::serialize(data)?);
    #[cfg(feature = "state_json")]
    return Ok(serde_json::to_string(data)?.into_bytes());
}

pub fn deserialize_state<T>(raw_data: &[u8]) -> ZRPCResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "state_bincode")]
    return Ok(bincode::deserialize::<T>(&raw_data)?);
    #[cfg(feature = "state_json")]
    return Ok(serde_json::from_str::<T>(std::str::from_utf8(raw_data)?)?);
}

pub fn serialize_request<T>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: ?Sized + Serialize,
{
    #[cfg(feature = "send_json")]
    Ok(serde_json::to_string(data)?.into_bytes())
}

pub fn deserialize_request<T>(raw_data: &[u8]) -> ZRPCResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "send_json")]
    Ok(serde_json::from_str::<T>(std::str::from_utf8(raw_data)?)?)
}
