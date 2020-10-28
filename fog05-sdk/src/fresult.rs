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

use thiserror::Error;
use std::fmt;
use serde::{Deserialize,Serialize};

#[derive(Error, Debug, Serialize,Deserialize, Clone)]
pub enum FError {
    ZConnectorError,
    EncodingError,
    TooMuchError,
    TransitionNotAllowed,
    NotFound,
    AlreadyPresent,
    ConversionError(String),
    IOError(String),
    BincodeError(String),
    ZError(String),
    UnknownError(String),
}

impl fmt::Display for FError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            FError::ZConnectorError => write!(f, "Connection Error"),
            FError::EncodingError => write!(f, "Data has wrong encoding!"),
            FError::TooMuchError => write!(f, "Expected less data!"),
            FError::TransitionNotAllowed => write!(f, "Transition Not allowed"),
            FError::NotFound => write!(f, "Not Found"),
            FError::AlreadyPresent => write!(f, "Already Present"),
            FError::ConversionError(err) => write!(f, "{}",err),
            FError::IOError(ioerr) => write!(f, "{}",ioerr),
            FError::ZError(zerr) => write!(f, "{}", zerr),
            FError::BincodeError(berr) => write!(f, "{}", berr),
            FError::UnknownError(err) => write!(f, "Error {}", err)
        }
     }
}

impl From<zenoh::ZError> for FError {
    fn from(err: zenoh::ZError) -> Self {
        FError::ZError(err.to_string())
    }
}

impl From<Box<bincode::ErrorKind>> for FError {
    fn from(err : Box<bincode::ErrorKind>) -> Self {
        FError::BincodeError(err.to_string())
    }
}

impl From<std::io::Error> for FError {
    fn from(err : std::io::Error) -> Self {
        FError::IOError(err.to_string())
    }
}

impl From<std::num::TryFromIntError> for FError {
    fn from(err : std::num::TryFromIntError) -> Self {
        FError::ConversionError(err.to_string())
    }
}

pub type FResult<T> = Result<T, FError>;