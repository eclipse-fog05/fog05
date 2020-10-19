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


use serde::{Serialize, de::DeserializeOwned};

pub struct ZClientChannel<'a, Req, Resp> {

    workspace : Arc<zenoh::Workspace<'a>>,
    path : String,
    // tx_ch : async_std::sync::Sender<Resp>,
    // rx_ch : async_std::sync::Receiver<Resp>,
    phantom_resp : PhantomData<Resp>,
    phantom_req : PhantomData<Req>,

}


impl<'a, Req, Resp> Clone for ZClientChannel<'a, Req, Resp> {
    fn clone(&self) -> Self {
        Self {
            workspace : self.workspace.clone(),
            path : self.path.clone(),
            // tx_ch : self.tx_ch.clone(),
            // rx_ch : self.rx_ch.clone(),
            phantom_resp : self.phantom_resp.clone(),
            phantom_req : self.phantom_req.clone(),
        }
    }
}


impl<'a, Req, Resp> ZClientChannel<'a, Req, Resp>
where
    Resp : DeserializeOwned,
    Req : std::fmt::Debug + Serialize,
{

    pub fn new
    (
        ws : Arc<zenoh::Workspace<'a>>,
        path : String,
    ) -> ZClientChannel<Req,Resp>
    {
        ZClientChannel {
            workspace : ws,
            path: path,
            phantom_resp : PhantomData,
            phantom_req : PhantomData,
        }
    }

    async fn send(&self, request: &Req) -> zenoh::DataStream{
        let req = serde_json::to_string(&request).unwrap(); //those are to be passed to the eval selector
        let selector = zenoh::Selector::try_from(format!("{}?(req={})",self.path, base64::encode(req))).unwrap();
        //Should create the appropriate Error type and the conversions form ZError
        self.workspace.get(&selector).await.unwrap()

    }


    pub async fn call_fun(&self,  request: Req) -> std::io::Result<Resp> {
        let mut data_stream = self.send(&request).await;
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
}
