
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
use std::sync::{Arc, Mutex};
use zenoh::*;
use futures::prelude::*;

extern crate hex;
extern crate bincode;
extern crate serde;


#[derive(Debug)]
pub enum ZCError {
    ZConnectorError,
    TransitionNotAllowed,
}

pub type ZCResult<T> = Result<T, ZCError>;

//move & to Arc<> or object if not shared, do not use references
pub struct InternalComponent {
    zenoh : Option<Zenoh>,
    zworkspace : Option<Arc<Workspace>>,
    uuid : String,
    pub status :ComponentInformation,
    pub state : Vec<u8>,
}

pub struct Component {
    component : Mutex<InternalComponent>,
}


impl Component {
    pub async fn new(uuid : String, name: String) -> ZCResult<Component> {
        let mut status = ComponentInformation::new();
        status.uuid = String::from(&uuid);
        status.name = name;
        status.routerid = String::from("");
        status.status = ComponentStatus::HALTED;

        let mut int = InternalComponent{
                zenoh : None,
                zworkspace : None,
                uuid : String::from(&uuid),
                status : status,
                state : Vec::new(),
        };

        Ok(Component{ component : Mutex::new(int)})
    }

    pub async fn connect(&mut self, locator : &String) -> ZCResult<()> {
        let zconfig = net::Config::client().add_peer(&locator);
        let z = Zenoh::new(zconfig, None).await;
        match z {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(zclient) =>
                {
                    let zsession = zclient.session();
                    let ws = zclient.workspace(None).await;
                    match ws {
                        Err(_) =>
                            //Should log the ZError
                            Err(ZCError::ZConnectorError),
                        Ok(zworkspace) =>
                            {
                                let zinfo = zsession.info().await;
                                let rid = hex::encode(&(zinfo.iter().find(|x| x.0 == 2 ).unwrap().1));
                                self.zenoh = Some(zclient);
                                let arc_ws = Arc::new(zworkspace);
                                self.zworkspace = Some(arc_ws.clone());
                                let mut s = self.status.lock().unwrap();
                                s.routerid = rid;
                                s.status = ComponentStatus::CONNECTED;



                                // let buf = net::RBuf::from(s.write_to_bytes().unwrap());
                                // let size = buf.len();
                                // let value = Value::Raw(size.try_into().unwrap(), buf);

                                // let info_path = Path::try_from(format!(INFO_PATH_TEMPLATE!(),&self.uuid)).unwrap();

                                Component::write_status_on_zenoh(&s, &arc_ws).await?;
                                Ok(())
                            },
                    }
                },
        }
    }

    pub async fn authenticate(&mut self) -> ZCResult<()> {
        let mut s = self.status.lock().unwrap();
        match s.status {
            ComponentStatus::CONNECTED =>
                {
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
                                    // we can populate with this component instance state
                                    // Doing nothing from the time being...
                                    {
                                        s.status = ComponentStatus::BUILDING;
                                        Component::write_status_on_zenoh(&s, &arc_ws).await?;
                                        Ok(())
                                    },
                                1 =>
                                    // We should get the available state from Zenoh and
                                    // store it in self
                                    {
                                        let state_data = Component::extract_state(&data[0].value)?;
                                        self.state = Some(Mutex::new(state_data));
                                        s.status = ComponentStatus::BUILDING;

                                        Component::write_status_on_zenoh(&s, &arc_ws).await?;
                                        Ok(())
                                    },
                                _ =>
                                    // Given the Selector no more than 1 result can be returned
                                    // returning error if more than one
                                    Err(ZCError::ZConnectorError),
                            }
                        },
                    }
                },
            _ =>
                //Transition is allowed only between connected and building
                Err(ZCError::TransitionNotAllowed),

        }


    }


    pub async fn register(&mut self) -> ZCResult<()> {
        let mut s = self.status.lock().unwrap();
        match s.status {
            ComponentStatus::BUILDING =>
                {
                    let arc_ws = self.zworkspace.as_ref().unwrap();
                    s.status = ComponentStatus::REGISTERED;

                    Component::write_status_on_zenoh(&s, &arc_ws).await?;
                    Ok(())
                },
            _ =>
                //Transition is allowed only between building and register
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn announce(&mut self) -> ZCResult<()> {
        let mut s = self.status.lock().unwrap();
        match s.status {
            ComponentStatus::REGISTERED =>
                {
                    let arc_ws = self.zworkspace.as_ref().unwrap();
                    s.status = ComponentStatus::ANNOUNCED;

                    Component::write_status_on_zenoh(&s, &arc_ws).await?;
                    Component::write_announce_on_zenoh(&self.uuid, arc_ws).await?;
                    Ok(())
                },
            _ =>
                //Transition is allowed only between registered and announced
                Err(ZCError::TransitionNotAllowed),
        }
    }

    pub async fn work(&mut self) -> ZCResult<()> {
        let mut s = self.status.lock().unwrap();
        match s.status {
            ComponentStatus::ANNOUNCED =>
                {
                    let arc_ws = self.zworkspace.as_ref().unwrap();
                    s.status = ComponentStatus::WORK;

                    Component::write_status_on_zenoh(&s, &arc_ws).await?;
                    Ok(())
                },
            _ =>
                //Transition is allowed only between announced and working
                Err(ZCError::TransitionNotAllowed),
        }
    }

    fn extract_state(value : &Value) -> Result<Vec<u8>, ZCError> {
        match value {
            Value::Raw(_, buf) =>
                Ok(buf.to_vec()),
            _ =>
                //State data is always expected as Raw
                Err(ZCError::ZConnectorError),
        }
    }


    async fn write_status_on_zenoh(status : &ComponentInformation, ws : &Workspace) -> ZCResult<()> {
        let buf = net::RBuf::from(status.write_to_bytes().unwrap());
        let size = buf.len();
        let value = Value::Raw(size.try_into().unwrap(), buf);

        let info_path = Path::try_from(format!(INFO_PATH_TEMPLATE!(),&status.uuid)).unwrap();

        match ws.put(&info_path, value).await {
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

    async fn write_state_zenoh(state : &Vec<u8>, uuid : &String, ws : &Workspace) -> ZCResult<()> {
        let state_path = Path::try_from(format!(STATE_PATH_TEMPLATE!(),&uuid)).unwrap();
        let buf = net::RBuf::from(*state);
        let size = buf.len();
        let value = Value::Raw(size.try_into().unwrap(), buf);
        match ws.put(&state_path, value).await {
            Err(_) =>
                //Should log the ZError
                Err(ZCError::ZConnectorError),
            Ok(_) => Ok(()),
        }


    }

    pub async fn put_state<T: ?Sized>(&mut self, state : Box<T> ) -> ZCResult<()>
    where
        T : serde::Serialize
    {
        let s = bincode::serialize(state.as_ref()).unwrap();
        match self.state.as_ref() {
            Some(old_state) =>
                {
                    let mut old = old_state.lock().unwrap();
                    let _ = std::mem::replace(&mut *old, s);
                    Ok(())
                },
            None =>
                {
                    self.state = Some(Mutex::new(s));
                    Ok(())
                },
        }

    }
}

