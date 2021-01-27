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

extern crate base64;
extern crate serde;

use async_std::sync::Arc;
use futures::prelude::*;
use serde::{de::DeserializeOwned, Serialize};
use std::marker::PhantomData;
use uuid::Uuid;

use zenoh::net::QueryConsolidation;
use zenoh::net::QueryTarget;

use log::trace;

use crate::serialize;
use crate::zrpcresult::{ZRPCError, ZRPCResult};

#[derive(Clone)]
pub struct ZNClientChannel<Req, Resp> {
    z: Arc<zenoh::net::Session>,
    path: String,
    server_uuid: Option<Uuid>,
    phantom_resp: PhantomData<Resp>,
    phantom_req: PhantomData<Req>,
}

impl<Req, Resp> ZNClientChannel<Req, Resp>
where
    Resp: DeserializeOwned,
    Req: std::fmt::Debug + Serialize,
{
    pub fn new(
        z: Arc<zenoh::net::Session>,
        path: String,
        server_uuid: Option<Uuid>,
    ) -> ZNClientChannel<Req, Resp> {
        ZNClientChannel {
            z,
            path,
            server_uuid,
            phantom_resp: PhantomData,
            phantom_req: PhantomData,
        }
    }

    /// This functions calls the get on the workspace for the eval
    /// it serialized the request on the as properties in the selector
    /// the request is first serialized as json and then encoded in base64 and
    /// passed as a property named req
    async fn send(
        &self,
        zsession: &zenoh::net::Session,
        request: &Req,
    ) -> ZRPCResult<async_std::channel::Receiver<zenoh::net::Reply>> {
        let req = serialize::serialize_request(&request)?;
        let selector = format!("{}{}/eval", self.path, self.server_uuid.unwrap(),);
        let predicate = base64::encode(req).to_string();

        //Should create the appropriate Error type and the conversions form ZError
        trace!("Sending {:?} to  {:?} {:?}", request, selector, predicate);
        let replies = zsession
            .query(
                &selector.into(),
                &predicate,
                QueryTarget::default(),
                QueryConsolidation::default(),
            )
            .await?;
        Ok(replies)
    }

    /// This function calls the eval on the server and deserialized the result
    /// if the value is not deserializable or the eval returns none it returns an IOError
    pub async fn call_fun(&self, request: Req) -> ZRPCResult<Resp> {
        let mut data_stream = self.send(&self.z, &request).await?;
        //takes only one, eval goes to only one
        let resp = data_stream.next().await;
        log::trace!("Response from zenoh is {:?}", resp);
        if let Some(reply) = resp {
            let rbuf = reply.data.payload;
            let raw_data = rbuf.to_vec();
            log::trace!("Size of response is {}", raw_data.len());
            Ok(serialize::deserialize_response(&raw_data)?)
        } else {
            log::error!("No data from server");
            Err(ZRPCError::ZenohError(format!(
                "No data from call_fun for Request {:?}",
                request
            )))
        }
    }

    /// This function verifies is the server is still available to reply at requests
    /// it first verifies that it is register in Zenoh, then it verifies if the peer is still connected,
    /// and then verifies the state, it returns an std::io::Result, the Err case describe the error.
    pub async fn verify_server(&self) -> ZRPCResult<bool> {
        if self.server_uuid.is_none() {
            return Ok(false);
        }

        log::trace!(
            "Check server selector {}",
            format!("{}{}/state", self.path, self.server_uuid.unwrap())
        );
        let selector = format!("{}{}/state", self.path, self.server_uuid.unwrap());
        let mut replies = self
            .z
            .query(
                &selector.into(),
                "",
                QueryTarget::default(),
                QueryConsolidation::default(),
            )
            .await?;

        let resp = replies.next().await;
        log::trace!("Response from zenoh is {:?}", resp);

        if let Some(reply) = resp {
            let rbuf = reply.data.payload;
            let ca = crate::serialize::deserialize_state::<crate::types::ComponentState>(
                &rbuf.to_vec(),
            )?;
            if ca.status == crate::types::ComponentStatus::SERVING {
                return Ok(true);
            }
        }
        Ok(false)
    }
}
