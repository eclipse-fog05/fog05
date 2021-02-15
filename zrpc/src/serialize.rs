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

#[cfg(any(feature = "resp_cbor", feature = "state_cbor", feature = "send_cbor"))]
extern crate serde_cbor;

#[cfg(any(feature = "send_json", feature = "state_json", feature = "resp_json"))]
extern crate serde_json;

use serde::{de::DeserializeOwned, Serialize};

use crate::types::ZRouterInfo;
use crate::zrpcresult::ZRPCResult;

#[cfg(feature = "resp_bincode")]
pub fn serialize_response<T: ?Sized>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(bincode::serialize(data)?)
}

#[cfg(feature = "resp_json")]
pub fn serialize_response<T: ?Sized>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_json::to_string(data)?.into_bytes())
}

#[cfg(feature = "resp_cbor")]
pub fn serialize_response<T>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_cbor::to_vec(data)?)
}

pub fn deserialize_response<T>(raw_data: &[u8]) -> ZRPCResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "resp_bincode")]
    return Ok(bincode::deserialize::<T>(&raw_data)?);

    #[cfg(feature = "resp_cbor")]
    return Ok(serde_cbor::from_slice::<T>(&raw_data)?);

    #[cfg(feature = "resp_json")]
    return Ok(serde_json::from_str::<T>(std::str::from_utf8(raw_data)?)?);
}

#[cfg(feature = "state_bincode")]
pub fn serialize_state<T: ?Sized>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(bincode::serialize(data)?)
}

#[cfg(feature = "state_cbor")]
pub fn serialize_state<T>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_cbor::to_vec(data)?)
}

#[cfg(feature = "state_json")]
pub fn serialize_state<T: ?Sized>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_json::to_string(data)?.into_bytes())
}

pub fn deserialize_state<T>(raw_data: &[u8]) -> ZRPCResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "state_bincode")]
    return Ok(bincode::deserialize::<T>(&raw_data)?);

    #[cfg(feature = "state_cbor")]
    return Ok(serde_cbor::from_slice::<T>(&raw_data)?);

    #[cfg(feature = "state_json")]
    return Ok(serde_json::from_str::<T>(std::str::from_utf8(raw_data)?)?);
}

#[cfg(feature = "send_json")]
pub fn serialize_request<T: ?Sized>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_json::to_string(data)?.into_bytes())
}

#[cfg(feature = "send_bincode")]
pub fn serialize_request<T: ?Sized>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(bincode::serialize(data)?)
}

#[cfg(feature = "send_cbor")]
pub fn serialize_request<T>(data: &T) -> ZRPCResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_cbor::to_vec(data)?)
}

pub fn deserialize_request<T>(raw_data: &[u8]) -> ZRPCResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "send_json")]
    return Ok(serde_json::from_str::<T>(std::str::from_utf8(raw_data)?)?);

    #[cfg(feature = "send_cbor")]
    return Ok(serde_cbor::from_slice::<T>(&raw_data)?);
}

pub fn deserialize_router_info(raw_data: &[u8]) -> ZRPCResult<ZRouterInfo> {
    #[cfg(feature = "router_json")]
    Ok(serde_json::from_str::<ZRouterInfo>(std::str::from_utf8(
        raw_data,
    )?)?)
}
