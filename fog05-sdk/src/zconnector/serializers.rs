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

#[cfg(feature = "data_bincode")]
extern crate bincode;

#[cfg(feature = "data_cbor")]
extern crate serde_cbor;

#[cfg(feature = "data_json")]
extern crate serde_json;

use crate::fresult::FResult;
use serde::{de::DeserializeOwned, Serialize};

#[cfg(feature = "data_bincode")]
pub fn serialize_data<T: ?Sized>(data: &T) -> FResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(bincode::serialize(data)?)
}

#[cfg(feature = "data_json")]
pub fn serialize_data<T: ?Sized>(data: &T) -> FResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_json::to_string(data)?.into_bytes())
}

#[cfg(feature = "data_cbor")]
pub fn serialize_data<T>(data: &T) -> FResult<Vec<u8>>
where
    T: Serialize,
{
    Ok(serde_cbor::to_vec(data)?)
}

pub fn deserialize_data<T>(raw_data: &[u8]) -> FResult<T>
where
    T: DeserializeOwned,
{
    #[cfg(feature = "data_bincode")]
    return Ok(bincode::deserialize::<T>(&raw_data)?);

    #[cfg(feature = "data_cbor")]
    return Ok(serde_cbor::from_slice::<T>(&raw_data)?);

    #[cfg(feature = "data_json")]
    return Ok(serde_json::from_str::<T>(std::str::from_utf8(raw_data)?)?);
}
