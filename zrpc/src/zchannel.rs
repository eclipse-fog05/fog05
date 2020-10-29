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
extern crate bincode;
extern crate serde_json;
extern crate base64;



use async_std::sync::Arc;
use std::convert::TryFrom;
use futures::prelude::*;
use std::marker::PhantomData;
use uuid::Uuid;

use serde::{Serialize, de::DeserializeOwned};

use log::{trace};

#[derive(Clone)]
pub struct ZClientChannel<Req, Resp> {
    z : Arc<zenoh::Zenoh>,
    path : String,
    server_uuid : Option<Uuid>,
    phantom_resp : PhantomData<Resp>,
    phantom_req : PhantomData<Req>,

}


impl<Req, Resp> ZClientChannel<Req, Resp>
where
    Resp : DeserializeOwned,
    Req : std::fmt::Debug + Serialize,
{

    pub fn new
    (
        z : Arc<zenoh::Zenoh>,
        path : String,
        server_uuid : Option<Uuid>
    ) -> ZClientChannel<Req,Resp>
    {
        ZClientChannel {
            z : z,
            path,
            server_uuid,
            phantom_resp : PhantomData,
            phantom_req : PhantomData,
        }
    }

    /// This functions calls the get on the workspace for the eval
    /// it serialized the request on the as properties in the selector
    /// the request is first serialized as json and then encoded in base64 and
    /// passed as a property named req
    async fn send(&self, ws : zenoh::Workspace<'_> ,request: &Req) -> zenoh::DataStream{
        let req = serde_json::to_string(&request).unwrap(); //those are to be passed to the eval selector
        let selector = zenoh::Selector::try_from(format!("{}/{}/eval?(req={})",self.path, self.server_uuid.unwrap(), base64::encode(req))).unwrap();
        //Should create the appropriate Error type and the conversions form ZError
        trace!("Sending {:?} to  {:?}", request, selector);
        ws.get(&selector).await.unwrap()

    }

    /// This function calls the eval on the server and deserialized the result
    /// if the value is not deserializable or the eval returns none it returns an IOError
    pub async fn call_fun(&self,  request: Req) -> std::io::Result<Resp> {
        let ws = self.z.workspace(None).await.unwrap();
        let mut data_stream = self.send(ws, &request).await;
        //takes only one, eval goes to only one
        let resp = data_stream.next().await;
        if let Some(data) = resp {
            let value = data.value;
            match value {
                zenoh::Value::Raw(_size, rbuf) => {
                    let raw_data = rbuf.to_vec();
                    Ok(bincode::deserialize::<Resp>(&raw_data).unwrap())
                },
                _ => Err(std::io::Error::new(std::io::ErrorKind::Other, "Value is not Raw!"))
            }
        } else {
            Err(std::io::Error::new(std::io::ErrorKind::Other, format!("No data from call_fun for Request {:?}", request)))
        }
    }

    /// This function verifies is the server is still available to reply at requests
    /// it first verifies that it is register in Zenoh, then it verifies if the peer is still connected,
    /// and then verifies the state, it returns an std::io::Result, the Err case describe the error.
    pub async fn verify_server(&self) -> std::io::Result<bool> {

        if self.server_uuid.is_none() { return Ok(false) }

        let ws = self.z.workspace(None).await.unwrap();

        let selector = zenoh::Selector::try_from(format!("{}/{}/state",self.path, self.server_uuid.unwrap())).unwrap();
        let mut ds = ws.get(&selector).await.unwrap();
        let mut idata = Vec::new();

        while let Some(d) = ds.next().await { idata.push(d)}

        if idata.len() == 0 { return Ok(false) }

        let iv = &idata[0];
        match &iv.value {
            zenoh::Value::Raw(_,buf) => {
                let cs = bincode::deserialize::<super::ComponentState>(&buf.to_vec()).unwrap();
                let selector = zenoh::Selector::try_from(format!("/@/router/{}", String::from(&cs.routerid))).unwrap();
                let mut ds = ws.get(&selector).await.unwrap();
                let mut rdata = Vec::new();

                while let Some(d) = ds.next().await { rdata.push(d) }

                if rdata.len() != 1 { return Err(std::io::Error::new(std::io::ErrorKind::NotFound, "Zenoh Router not found!".to_string())) }

                let rv = &rdata[0];
                match &rv.value {
                    zenoh::Value::Json(sv) => {
                        let ri = serde_json::from_str::<super::types::ZRouterInfo>(&sv).unwrap();
                        let mut it = ri.sessions.iter();
                        let f = it.find(|&x| {x.peer == String::from(&cs.peerid).to_uppercase()});

                        if f.is_none() { return Ok(false) }

                        match cs.status {
                            super::ComponentStatus::SERVING => return Ok(true),
                            _ => return Ok(false),
                        }
                    },
                    _ => return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "Router information is not encoded in JSON".to_string())),
                }
            },
            _ => return Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "Component Advertisement is not encoded in RAW".to_string())),
        }
    }

}