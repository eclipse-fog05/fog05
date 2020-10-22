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
use thiserror::Error;
use zenoh::*;
use std::fmt;

#[derive(Error, Debug)]
pub enum FError {
    ZConnectorError,
    TransitionNotAllowed,
    NotFound,
    ZError(String),
    UnknownError(String),
}

impl fmt::Display for FError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            FError::ZConnectorError => write!(f, "Connection Error"),
            FError::TransitionNotAllowed => write!(f, "Transition Not allowed"),
            FError::NotFound => write!(f, "Not Found"),
            FError::ZError(zerr) => write!(f, "{}", zerr),
            FError::UnknownError(err) => write!(f, "Error {}", err)
        }
     }
}

impl From<zenoh::ZError> for FError {
    fn from(err: zenoh::ZError) -> Self {
        FError::ZError(err.to_string())
    }
}

pub type FResult<T> = Result<T, FError>;