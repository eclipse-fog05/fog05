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
use std::convert::TryFrom;
use std::marker::PhantomData;
use uuid::Uuid;

use serde::{de::DeserializeOwned, Serialize};

use log::trace;

use crate::serialize;
use crate::zrpcresult::{ZRPCError, ZRPCResult};

#[derive(Clone)]
pub struct ZClientChannel<Req, Resp> {
    z: Arc<zenoh::Zenoh>,
    path: String,
    server_uuid: Option<Uuid>,
    phantom_resp: PhantomData<Resp>,
    phantom_req: PhantomData<Req>,
}

impl<Req, Resp> ZClientChannel<Req, Resp>
where
    Resp: DeserializeOwned,
    Req: std::fmt::Debug + Serialize,
{
    pub fn new(
        z: Arc<zenoh::Zenoh>,
        path: String,
        server_uuid: Option<Uuid>,
    ) -> ZClientChannel<Req, Resp> {
        ZClientChannel {
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
    async fn send(&self, ws: zenoh::Workspace<'_>, request: &Req) -> ZRPCResult<zenoh::DataStream> {
        let req = serialize::serialize_request(&request)?;
        let selector = zenoh::Selector::try_from(format!(
            "{}/{}/eval?(req={})",
            self.path,
            self.server_uuid.unwrap(),
            base64::encode(req)
        ))?;
        //Should create the appropriate Error type and the conversions form ZError
        trace!("Sending {:?} to  {:?}", request, selector);
        Ok(ws.get(&selector).await?)
    }

    /// This function calls the eval on the server and deserialized the result
    /// if the value is not deserializable or the eval returns none it returns an IOError
    pub async fn call_fun(&self, request: Req) -> ZRPCResult<Resp> {
        let ws = self.z.workspace(None).await?;
        let mut data_stream = self.send(ws, &request).await?;
        //takes only one, eval goes to only one
        let resp = data_stream.next().await;
        log::trace!("Response from zenoh is {:?}", resp);
        if let Some(data) = resp {
            let value = data.value;
            match value {
                zenoh::Value::Raw(_size, rbuf) => {
                    let raw_data = rbuf.to_vec();
                    log::trace!("Size of response is {}", raw_data.len());
                    Ok(serialize::deserialize_response(&raw_data)?)
                }
                _ => Err(ZRPCError::ZenohError(
                    "Response data is expected to be RAW in Zenoh!!".to_string(),
                )),
            }
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

        let ws = self.z.workspace(None).await?;

        let selector = zenoh::Selector::try_from(format!(
            "{}/{}/state",
            self.path,
            self.server_uuid.unwrap()
        ))?;

        let ds = ws.get(&selector).await?;
        let idata: Vec<zenoh::Data> = ds.collect().await;

        if idata.is_empty() {
            return Ok(false);
        }

        let iv = &idata[0];
        match &iv.value {
            zenoh::Value::Raw(_, buf) => {
                let raw_data = buf.to_vec();
                log::trace!("Size of state is {}", raw_data.len());
                let cs = serialize::deserialize_state::<super::ComponentState>(&raw_data)?;
                let selector =
                    zenoh::Selector::try_from(format!("/@/router/{}", String::from(&cs.routerid)))?;
                let mut ds = ws.get(&selector).await?;
                let mut rdata = Vec::new();

                while let Some(d) = ds.next().await {
                    rdata.push(d)
                }

                if rdata.len() != 1 {
                    return Err(ZRPCError::NotFound);
                }

                let rv = &rdata[0];
                match &rv.value {
                    zenoh::Value::Json(sv) => {
                        log::trace!("Size of Zenoh router state is {}", sv.len());
                        let ri = serde_json::from_str::<super::types::ZRouterInfo>(&sv)?;
                        let mut it = ri.sessions.iter();
                        let f = it.find(|&x| x.peer == String::from(&cs.peerid).to_uppercase());

                        if f.is_none() {
                            return Ok(false);
                        }

                        match cs.status {
                            super::ComponentStatus::SERVING => return Ok(true),
                            _ => return Ok(false),
                        }
                    }
                    _ => {
                        return Err(ZRPCError::ZenohError(
                            "Router information is not encoded in JSON".to_string(),
                        ));
                    }
                }
            }
            _ => {
                return Err(ZRPCError::ZenohError(
                    "Component state is expected to be RAW in Zenoh!!".to_string(),
                ));
            }
        }
    }
}
