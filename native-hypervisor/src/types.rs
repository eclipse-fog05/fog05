#![allow(unused_variables)]

extern crate machine_uid;
extern crate serde;
extern crate serde_json;
extern crate serde_yaml;

use std::collections::HashMap;
use std::process::Child;

use async_std::sync::{Arc, Mutex, RwLock};

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::im::fdu::*;
use fog05_sdk::plugins::NetworkingPluginClient;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NativeHVSpecificInfo {
    //pub netns: Uuid,
    pub pid: u32,
    pub env: HashMap<String, String>,
    pub instance_path: String,
    pub instance_files: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NativeHVSpecificDescriptor {
    pub path: Option<String>,
    pub cmd: String,
    pub args: Vec<String>,
    pub env: HashMap<String, String>,
}

#[derive(Clone)]
pub struct NativeHVState {
    pub fdus: HashMap<Uuid, FDURecord>,
    pub childs: HashMap<Uuid, Arc<Mutex<Child>>>,
    pub uuid: Option<Uuid>,
}

#[derive(Clone)]
pub struct NativeHypervisor {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid: u32,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub net: Option<NetworkingPluginClient>,
    pub fdus: Arc<RwLock<NativeHVState>>,
}
