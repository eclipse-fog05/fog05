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
pub enum ZRPCError {
    DeserializationError(String),
    SerializationError(String),
    ZenohError(String),
    StateTransitionNotAllowed(String),
    Error(String),
    IOError(String),
    ChannelError(String),
    TimedOut,
    MissingValue,
    NotFound,
    Unreachable,
    PermissionDenied,
    Unavailable,
    NoRouter,
}

impl fmt::Display for ZRPCError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ZRPCError::DeserializationError(err) => write!(f, "{}", err),
            ZRPCError::SerializationError(err) => write!(f, "{}", err),
            ZRPCError::ZenohError(err) => write!(f, "{}", err),
            ZRPCError::StateTransitionNotAllowed(err) => write!(f, "{}", err),
            ZRPCError::Error(err) => write!(f, "{}", err),
            ZRPCError::IOError(err) => write!(f, "{}", err),
            ZRPCError::ChannelError(err) => write!(f, "{}", err),
            ZRPCError::MissingValue => write!(f, "Missing Value in Option"),
            ZRPCError::NotFound => write!(f, "Component not found"),
            ZRPCError::Unreachable => write!(f, "Unreachable code!"),
            ZRPCError::TimedOut => write!(f, "ZRPC call has timed out!"),
            ZRPCError::PermissionDenied => write!(f, "ZRPC Permission denied"),
            ZRPCError::Unavailable => write!(f, "ZRPC Unavailable"),
            ZRPCError::NoRouter => write!(f, "No router found"),
        }
    }
}

#[cfg(any(
    feature = "resp_bincode",
    feature = "state_bincode",
    feature = "send_bincode"
))]
impl From<Box<bincode::ErrorKind>> for ZRPCError {
    fn from(err: Box<bincode::ErrorKind>) -> Self {
        ZRPCError::SerializationError(err.to_string())
    }
}

#[cfg(any(feature = "resp_cbor", feature = "state_cbor", feature = "send_cbor"))]
impl From<serde_cbor::Error> for ZRPCError {
    fn from(err: serde_cbor::Error) -> Self {
        ZRPCError::SerializationError(err.to_string())
    }
}

#[cfg(any(
    feature = "send_json",
    feature = "state_json",
    feature = "resp_json",
    feature = "router_json"
))]
impl From<serde_json::Error> for ZRPCError {
    fn from(err: serde_json::Error) -> Self {
        ZRPCError::SerializationError(err.to_string())
    }
}

#[cfg(any(
    feature = "send_json",
    feature = "state_json",
    feature = "resp_json",
    feature = "router_json"
))]
impl From<std::str::Utf8Error> for ZRPCError {
    fn from(err: std::str::Utf8Error) -> Self {
        ZRPCError::DeserializationError(err.to_string())
    }
}

impl From<zenoh::ZError> for ZRPCError {
    fn from(err: zenoh::ZError) -> Self {
        ZRPCError::ZenohError(err.to_string())
    }
}

impl From<std::io::Error> for ZRPCError {
    fn from(err: std::io::Error) -> Self {
        ZRPCError::IOError(err.to_string())
    }
}

impl From<async_std::channel::RecvError> for ZRPCError {
    fn from(err: async_std::channel::RecvError) -> Self {
        ZRPCError::ChannelError(err.to_string())
    }
}

impl<T> From<async_std::channel::SendError<T>> for ZRPCError {
    fn from(err: async_std::channel::SendError<T>) -> Self {
        ZRPCError::ChannelError(err.to_string())
    }
}

pub type ZRPCResult<T> = Result<T, ZRPCError>;
