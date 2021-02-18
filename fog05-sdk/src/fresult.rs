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
use std::fmt;
use thiserror::Error;

#[derive(Error, Debug, Serialize, Deserialize, Clone)]
pub enum FError {
    ZConnectorError,
    EncodingError,
    TooMuchError,
    TransitionNotAllowed,
    NotFound,
    WrongKind,
    NotConnected,
    AlreadyPresent,
    Unimplemented,
    MalformedDescriptor,
    HasInstances,
    ConversionError(String),
    IOError(String),
    SerializationDeserializationError(String),
    ZError(String),
    UnknownError(String),
    NetworkingError(String),
    HypervisorError(String),
    UUIDError(String),
}

impl fmt::Display for FError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            FError::ZConnectorError => write!(f, "Connection Error"),
            FError::EncodingError => write!(f, "Data has wrong encoding!"),
            FError::TooMuchError => write!(f, "Expected less data!"),
            FError::TransitionNotAllowed => write!(f, "Transition Not allowed"),
            FError::NotFound => write!(f, "Not Found"),
            FError::WrongKind => write!(f, "Wrong kind!"),
            FError::NotConnected => write!(f, "NotConnected"),
            FError::AlreadyPresent => write!(f, "Already Present"),
            FError::Unimplemented => write!(f, "Function is not implemented!!"),
            FError::MalformedDescriptor => write!(f, "Malformed descriptor!"),
            FError::HasInstances => write!(f, "Has instances!"),
            FError::ConversionError(err) => write!(f, "{}", err),
            FError::IOError(err) => write!(f, "{}", err),
            FError::ZError(err) => write!(f, "{}", err),
            FError::SerializationDeserializationError(err) => write!(f, "{}", err),
            FError::UnknownError(err) => write!(f, "Error {}", err),
            FError::NetworkingError(err) => write!(f, "NetworkingError {}", err),
            FError::HypervisorError(err) => write!(f, "HypervisorError {}", err),
            FError::UUIDError(err) => write!(f, "UUIDError {}", err),
        }
    }
}

impl From<zenoh::ZError> for FError {
    fn from(err: zenoh::ZError) -> Self {
        FError::ZError(err.to_string())
    }
}

impl From<std::io::Error> for FError {
    fn from(err: std::io::Error) -> Self {
        FError::IOError(err.to_string())
    }
}

impl From<std::num::TryFromIntError> for FError {
    fn from(err: std::num::TryFromIntError) -> Self {
        FError::ConversionError(err.to_string())
    }
}

impl From<reqwest::Error> for FError {
    fn from(err: reqwest::Error) -> Self {
        FError::IOError(err.to_string())
    }
}

impl From<zrpc::zrpcresult::ZRPCError> for FError {
    fn from(err: zrpc::zrpcresult::ZRPCError) -> Self {
        FError::ZError(err.to_string())
    }
}

impl From<Box<dyn std::error::Error>> for FError {
    fn from(err: Box<dyn std::error::Error>) -> Self {
        FError::UnknownError(err.to_string())
    }
}

impl From<uuid::Error> for FError {
    fn from(err: uuid::Error) -> Self {
        FError::UUIDError(err.to_string())
    }
}

#[cfg(feature = "data_bincode")]
impl From<Box<bincode::ErrorKind>> for FError {
    fn from(err: Box<bincode::ErrorKind>) -> Self {
        FError::SerializationDeserializationError(err.to_string())
    }
}

#[cfg(feature = "data_cbor")]
impl From<serde_cbor::Error> for FError {
    fn from(err: serde_cbor::Error) -> Self {
        FError::SerializationDeserializationError(err.to_string())
    }
}

#[cfg(feature = "data_json")]
impl From<serde_json::Error> for FError {
    fn from(err: serde_json::Error) -> Self {
        FError::SerializationError(err.to_string())
    }
}

#[cfg(feature = "data_json")]
impl From<std::str::Utf8Error> for FError {
    fn from(err: std::str::Utf8Error) -> Self {
        FError::SerializationDeserializationError(err.to_string())
    }
}

pub type FResult<T> = Result<T, FError>;
