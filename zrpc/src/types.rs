extern crate serde;
extern crate serde_json;
extern crate serde_yaml;

use uuid::Uuid;
use serde::{Serialize, Deserialize};


#[derive(Clone,PartialEq,Eq,Debug,Hash, Serialize, Deserialize)]
// pub enum ComponentStatus {
//     HALTED = 0,
//     CONNECTED = 1,
//     BUILDING = 2,
//     REGISTERED = 3,
//     ANNOUNCED = 4,
//     WORK = 5,
//     UNWORK = 6,
//     UNANNOUNCED = 7,
//     UNREGISTERED = 8,
//     DISCONNECTED = 9,
// }
pub enum ComponentStatus {
    HALTED = 0,
    INITIALIZING = 1,
    REGISTERED = 2,
    SERVING = 3,
}

// #[derive(PartialEq,Clone, Serialize, Deserialize, Debug)]
// pub struct ComponentAdvertisement {
//     pub uuid : Uuid,
//     pub name : String,
//     pub routerid : String,
//     pub peerid : String,
// }

#[derive(PartialEq,Clone, Serialize, Deserialize, Debug)]
pub struct ComponentState {
    pub uuid : Uuid,
    pub name : String,
    pub routerid : String,
    pub peerid : String,
    pub status : ComponentStatus,
}



#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ZSessionInfo {
    pub peer : String,
    pub links : Vec<String>,
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ZPluginInfo {
    pub name : String,
    pub path : String,
}


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct ZRouterInfo {
    pub pid : String,
    pub locators : Vec<String>,
    pub sessions : Vec<ZSessionInfo>,
    pub plugins : Vec<ZPluginInfo>,
    pub time : Option<String>,
}