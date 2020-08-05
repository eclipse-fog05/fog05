
#![feature(let_chains)]


macro_rules!  INFO_PATH_TEMPLATE { () => { "/components/{}/info" }; }
macro_rules!  STATE_PATH_TEMPLATE { () => { "/component/{}/state" }; }
macro_rules!  ADV_SELECTOR { () => { "/advertisement/*/info" }; }
macro_rules!  ADV_PATH { () => { "/advertisement/{}/info" }; }


pub mod im;

use protobuf::parse_from_bytes;
use std::convert::TryInto;
use std::convert::TryFrom;
use protobuf::Message;
use im::data::*;
use async_std::sync::{Mutex,Arc};
use zenoh::*;
use futures::prelude::*;
use thiserror::Error;
use std::fmt;

extern crate hex;
extern crate bincode;
extern crate serde;


#[derive(Error, Debug)]
pub enum ZCError {
    ZConnectorError,
    TransitionNotAllowed,
    UnknownError(String),
}

impl fmt::Display for ZCError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ZConnectorError => write!(f, "Connection Error"),
            TransitionNotAllowed => write!(f, "Transition Not allowed"),
            UnknownError => write!(f, "Error {}", self)
        }
     }
}

pub type ZCResult<T> = Result<T, ZCError>;

//move & to Arc<> or object if not shared, do not use references


//create a struct with a generic T that implements Serialize, Deserialize, Clone
pub struct InternalComponent<T> {
    zenoh : Option<Zenoh>,
    zworkspace : Option<Arc<Workspace>>,
    uuid : String,
    pub status :ComponentInformation,
    pub state : Option<T>,
    raw_state : Vec<u8>,
}

// pub struct Component<T> {
//     component : Mutex<InternalComponent<T>>,
// }


impl<T> InternalComponent<T>
    where
    T : serde::Serialize+serde::de::DeserializeOwned+Clone {
    pub async fn new(uuid : String, name: String) -> ZCResult<InternalComponent<T>> {
        let mut status = ComponentInformation::new();
        status.uuid = String::from(&uuid);
        status.name = name;
        status.routerid = String::from("");
        status.status = ComponentStatus::HALTED;

        let mut int = InternalComponent {
            zenoh : None,
            zworkspace : None,
            uuid : String::from(&uuid),
            status : status,
            state : None,
            raw_state : Vec::new(),
        };
        Ok(int)
    }

    pub async fn connect(&mut self, locator : &String) -> ZCResult<()> {

        let zconfig = net::Config::client().add_peer(&locator);
        let z = Zenoh::new(zconfig, None).await;
        match z {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(zclient) => {
                let zsession = zclient.session();
                let ws = zclient.workspace(None).await;
                match ws {
                    Err(_) =>
                        //Should log the ZError
                        Err(ZCError::ZConnectorError),
                    Ok(zworkspace) => {
                        let zinfo = zsession.info().await;
                        let rid = hex::encode(&(zinfo.iter().find(|x| x.0 == 2 ).unwrap().1));
                        self.zenoh = Some(zclient);
                        let arc_ws = Arc::new(zworkspace);
                        self.zworkspace = Some(arc_ws.clone());
                        self.status.routerid = rid;
                        self.status.status = ComponentStatus::CONNECTED;
                        InternalComponent::write_status_on_zenoh(self).await?;
                        Ok(())
                    },
                }
            },
        }
    }

    pub async fn authenticate(&mut self) -> ZCResult<()> {
        match self.status.status {
            ComponentStatus::CONNECTED => {
                self.status.status = ComponentStatus::BUILDING;
                InternalComponent::write_status_on_zenoh(self).await?;
                Ok(())
            },
            _ =>
                //Transition is allowed only between connected and building
                Err(ZCError::TransitionNotAllowed),

        }


    }

    pub async fn read(&mut self) -> ZCResult<()> {
        let selector = zenoh::Selector::try_from(format!(STATE_PATH_TEMPLATE!(),&self.uuid)).unwrap();
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
                        self.raw_state = InternalComponent::<T>::extract_state(&data[0].value)?;
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
                InternalComponent::write_status_on_zenoh(self).await?;
                InternalComponent::write_state_zenoh(self).await?;
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
                InternalComponent::write_status_on_zenoh(self).await?;
                InternalComponent::<T>::write_announce_on_zenoh(&self.uuid, arc_ws).await?;
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
                InternalComponent::write_status_on_zenoh(self).await?;
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
        let buf = net::RBuf::from(self.status.write_to_bytes().unwrap());
        let size = buf.len();
        let value = Value::Raw(size.try_into().unwrap(), buf);
        let info_path = Path::try_from(format!(INFO_PATH_TEMPLATE!(),&self.status.uuid)).unwrap();
        match arc_ws.put(&info_path, value).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }
    }

    async fn write_announce_on_zenoh(uuid : &String, ws : &Workspace) -> ZCResult<()> {
        let value = Value::StringUTF8(String::from(uuid));
        let info_path = Path::try_from(format!(ADV_PATH!(),&uuid)).unwrap();
        match ws.put(&info_path, value).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }
    }

    async fn write_state_zenoh(&mut self) -> ZCResult<()> {
        let state_path = Path::try_from(format!(STATE_PATH_TEMPLATE!(),&self.uuid)).unwrap();
        let buf = net::RBuf::from(self.raw_state.clone());
        let size = buf.len();
        let value = Value::Raw(size.try_into().unwrap(), buf);
        let arc_ws = self.zworkspace.as_ref().unwrap();
        match arc_ws.put(&state_path, value).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }


    }

    pub async fn put_state(&mut self, state : T) -> ZCResult<()> {
        self.state = Some(state);
        self.raw_state = bincode::serialize(&self.state).unwrap();
        println!("W: raw_state: {:?}", self.raw_state);
        // Let it crash...
        bincode::deserialize::<T>(&self.raw_state).unwrap();
        //
        Ok(())

    }

    pub async fn get_state(&mut self) -> ZCResult<Option<T>> {
        println!("R: raw_state: {:?}", &self.raw_state);
        match self.raw_state.len() {
            0 => Ok(self.state.clone()),
            _ => {
                let res = bincode::deserialize(&self.raw_state);
                match res {
                    Err(why) => Err(ZCError::UnknownError(format!("Err {:?}", why))),
                    Ok(s) => {
                        self.state = Some(s);
                        InternalComponent::write_status_on_zenoh(self).await?;
                        Ok(self.state.clone())
                    },
                }
            },
        }
    }

    pub async fn get_routerid(&self) -> String {
        String::from(&self.status.routerid)
    }

    pub async fn get_status(&self) -> ComponentStatus {
        self.status.status
    }
}

