
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


macro_rules!  INFO_PATH_TEMPLATE { ($x:expr) => { format!("/components/{}/info", $x) }; }
macro_rules!  STATE_PATH_TEMPLATE { ($x:expr) => { format!("/component/{}/state",$x) }; }
macro_rules!  ADV_SELECTOR { () => { "/advertisement/*/info" }; }
macro_rules!  ADV_PATH { ($x:expr) => { format!("/advertisement/{}/info",$x) }; }
macro_rules!  FN_PATH { ($id:expr, $fname:expr ) => { format!("/component/{}/functions/{}",$id, $fname) }; }

extern crate bincode;
extern crate hex;
extern crate serde;

pub mod services;
pub mod im;
pub mod zconnector;



use std::convert::TryInto;
use std::convert::TryFrom;
use im::data::*;
use async_std::sync::{Mutex,Arc};
use zenoh::*;
use futures::prelude::*;
use thiserror::Error;
use std::fmt;
use log::{info, trace, warn, error, debug};
use serde::{Serialize,de::DeserializeOwned};
use uuid::Uuid;




#[derive(Error, Debug)]
pub enum ZCError {
    ZConnectorError,
    TransitionNotAllowed,
    UnknownError(String),
}

impl fmt::Display for ZCError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ZCError::ZConnectorError => write!(f, "Connection Error"),
            ZCError::TransitionNotAllowed => write!(f, "Transition Not allowed"),
            ZCError::UnknownError(err) => write!(f, "Error {}", err)
        }
     }
}

pub type ZCResult<T> = Result<T, ZCError>;

//move & to Arc<> or object if not shared, do not use references


//create a struct with a generic T that implements Serialize, Deserialize, Clone
pub struct InternalComponent<T> {
    pub state : T,
    pub raw_state : Vec<u8>,
}

impl<T> InternalComponent<T>
    where
    T : Serialize+DeserializeOwned+Clone {

    pub async fn new(raw_state : Vec<u8>, state : T ) -> InternalComponent<T> {
        InternalComponent {
            state : state,
            raw_state : raw_state
        }
    }

    pub async fn from_raw(raw_state : Vec<u8>) -> InternalComponent<T> {
        let state = bincode::deserialize::<T>(&raw_state).unwrap();

        InternalComponent {
            state : state,
            raw_state : raw_state
        }
    }

    pub async fn from_state(state : T) -> InternalComponent<T> {
        let raw_state = bincode::serialize(&state).unwrap();
        InternalComponent {
            state : state,
            raw_state : raw_state
        }
    }

}

pub struct Component<'a,T> {
    zenoh : Option<Arc<&'a zenoh::net::Session>>,
    zworkspace : Option<Arc<Workspace<'a>>>,
    uuid : Uuid,
    pub status :ComponentInformation,
    component : Option<InternalComponent<T>>,
}



impl<'a,T> Component<'a,T>
    where
    T : Serialize+DeserializeOwned+Clone {
    pub async fn new(uuid : Uuid, name: String) -> Component<'a,T> {
        let status = ComponentInformation{
            uuid : uuid,
            name : name,
            routerid : String::from(""),
            peerid : String::from(""),
            status : ComponentStatus::HALTED,
        };

        Component {
            zenoh : None,
            zworkspace : None,
            uuid : uuid,
            status : status,
            component : None,
        }
    }

    pub async fn connect(&mut self, ws : Arc<Workspace<'a>>, session : Arc<&'a zenoh::net::Session>) -> ZCResult<()> {
        self.zenoh = Some(session);
        self.zworkspace = Some(ws);
        Ok(())
    }

    pub async fn authenticate(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::CONNECTED => {
                self.status.status = ComponentStatus::BUILDING;
                Component::write_status_on_zenoh(self).await?;
                Ok(())
            },
            _ =>
                //Transition is allowed only between connected and building
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn read(&mut self) -> ZCResult<()> {
        let selector = zenoh::Selector::try_from(STATE_PATH_TEMPLATE!(&self.uuid)).unwrap();
        let arc_ws = self.zworkspace.as_ref().unwrap();
        match arc_ws.get(&selector).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(mut datastream) => {
                let mut data = Vec::new();
                while let Some(d) = datastream.next().await {
                    data.push(d);
                }
                match data.len() {
                    0 =>
                        // There is actually no state stored on Zenoh
                        // we return None to the user
                        Ok(()),
                    1 => {
                        // We should get the available state from Zenoh and
                        // return it to the user
                        let rs = Component::<T>::extract_state(&data[0].value)?;
                        let ic = InternalComponent::from_raw(rs).await;
                        self.component = Some(ic);

                        Ok(())
                    },
                    _ =>
                        // Given the Selector no more than 1 result can be returned
                        // returning error if more than one
                        Err(ZCError::ZConnectorError),
                }
            },
        }
    }


    pub async fn register(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::BUILDING => {
                self.status.status = ComponentStatus::REGISTERED;
                Component::write_status_on_zenoh(self).await?;
                Component::write_state_zenoh(self).await?;
                Ok(())
            },
            _ =>
                //Transition is allowed only between building and register
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn announce(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::REGISTERED => {
                let arc_ws = self.zworkspace.as_ref().unwrap();
                self.status.status = ComponentStatus::ANNOUNCED;
                Component::write_status_on_zenoh(self).await?;
                Component::<T>::write_announce_on_zenoh(&self.uuid, arc_ws).await?;
                Ok(())
            },
            _ =>
                //Transition is allowed only between registered and announced
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn work(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::ANNOUNCED => {
                self.status.status = ComponentStatus::WORK;
                Component::write_status_on_zenoh(self).await?;
                Ok(())
            },
            _ =>
                //Transition is allowed only between announced and working
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn unwork(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::WORK => {
                self.status.status = ComponentStatus::UNWORK;
                Component::write_status_on_zenoh(self).await?;
                Ok(())
            },
            _ =>
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn unannounce(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::UNWORK => {
                self.status.status = ComponentStatus::UNANNOUNCED;
                Component::write_status_on_zenoh(self).await?;
                Component::<T>::remove_announce_from_zenoh(&self.uuid, self.zworkspace.as_ref().unwrap()).await?;
                Ok(())
            },
            _ =>
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn unregister(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::UNANNOUNCED => {
                self.status.status = ComponentStatus::UNREGISTERED;
                Component::write_status_on_zenoh(self).await?;
                Ok(())
            },
            _ =>
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn disconnect(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::UNREGISTERED => {
                self.status.status = ComponentStatus::DISCONNECTED;
                Component::write_status_on_zenoh(self).await?;
                Component::remove_status_from_zenoh(self).await?;
                Ok(())
            },
            _ =>
                //Transition is allowed only between announced and working
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn stop(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::DISCONNECTED => {
                self.status.status = ComponentStatus::HALTED;
                self.zenoh = None;
                self.zworkspace = None;
                self.status.routerid = String::from("");

                Ok(())
            },
            _ =>
                //Transition is allowed only between announced and working
                Err(ZCError::TransitionNotAllowed),
        }
    }

    fn extract_state(value : &Value) -> Result<Vec<u8>, ZCError> {
        match value {
            Value::Raw(_, buf) => Ok(buf.to_vec()),
            _ =>
                //State data is always expected as Raw
                Err(ZCError::ZConnectorError),
        }
    }


    async fn write_status_on_zenoh(&self) -> ZCResult<()> {
        let arc_ws = self.zworkspace.as_ref().unwrap();
        let buf = net::RBuf::from(bincode::serialize(&self.status).unwrap());
        let size = buf.len();
        let value = Value::Raw(size.try_into().unwrap(), buf);
        let info_path = Path::try_from(INFO_PATH_TEMPLATE!(&self.status.uuid)).unwrap();
        match arc_ws.put(&info_path, value).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }
    }

    async fn remove_status_from_zenoh(&self) -> ZCResult<()> {
        let arc_ws = self.zworkspace.as_ref().unwrap();
        let info_path = Path::try_from(INFO_PATH_TEMPLATE!(&self.status.uuid)).unwrap();
        match arc_ws.delete(&info_path).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }
    }

    async fn remove_announce_from_zenoh(uuid : &Uuid, ws : &Workspace<'_>) -> ZCResult<()> {
        let info_path = Path::try_from(ADV_PATH!(&uuid)).unwrap();
        match ws.delete(&info_path).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }
    }

    async fn write_announce_on_zenoh(uuid : &Uuid, ws : &Workspace<'_>) -> ZCResult<()> {
        let value = Value::StringUTF8(format!("{}",uuid));
        let info_path = Path::try_from(ADV_PATH!(&uuid)).unwrap();
        match ws.put(&info_path, value).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }
    }

    async fn write_state_zenoh(&mut self) -> ZCResult<()> {
        match &self.component {
            None => Err(ZCError::ZConnectorError),
            Some(ic) => {
                let state_path = Path::try_from(STATE_PATH_TEMPLATE!(&self.uuid)).unwrap();
                let buf = net::RBuf::from(ic.raw_state.clone());
                let size = buf.len();
                let value = Value::Raw(size.try_into().unwrap(), buf);
                let arc_ws = self.zworkspace.as_ref().unwrap();
                match arc_ws.put(&state_path, value).await {
                    Err(e) => {
                        //Should log the ZError
                        warn!("Got error on Zenoh state sync {}", e);
                        Err(ZCError::ZConnectorError)
                    },
                    Ok(_) => Ok(()),
                }
            }
        }
    }

    pub async fn sync_state(&mut self) -> ZCResult<()> {
        self.write_state_zenoh().await
    }

    pub async fn put_state(&mut self, state : T) -> ZCResult<()> {
        self.component = Some(InternalComponent::from_state(state).await);
        Ok(())
    }

    pub async fn get_state(&mut self) -> Option<T> {
        match &self.component {
            None => None,
            Some(ic) => {
                match ic.raw_state.len() {
                    0 => None,
                    _ => Some(ic.state.clone()),
                }
            },
        }
    }

    pub async fn get_routerid(&self) -> String {
        String::from(&self.status.routerid)
    }

    pub async fn get_peerid(&self) -> String {
        String::from(&self.status.peerid)
    }

    pub async fn get_status(&self) -> ComponentStatus {
        self.status.status.clone()
    }
}

