

extern crate serde;
extern crate serde_json;
extern crate serde_yaml;

use serde::{Serialize, Deserialize};


#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct SystemInfo {
    pub name : String,
    pub uuid : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct SystemConfig {
    pub config : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct TenantInfo {
    pub name : String,
    pub uuid : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct CPUSpec {
    pub model : String,
    pub frequency : f64,
    pub arch : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct RAMSpec {
    pub size : f64
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct DiskSpec {
    pub local_address : String,
    pub dimension : f64,
    pub mount_point : String,
    pub file_system : String
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct IOSpec {
    pub name : String,
    pub io_type : String,
    pub io_file : String,
    pub available : bool
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct VolatilitySpec {
    pub avg_availability_minutes : u64,
    pub quartile_availability_minutes : Vec<u64>
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct AcceleratorSpec {
    pub hw_address : String,
    pub name : String,
    pub supported_libraries : Vec<String>,
    pub available : bool
}

#[derive(Serialize,Deserialize,Debug, Clone)]
pub struct InterfaceConfiguration {
    pub ipv4_address : String,
    pub ipv4_netmask : String,
    pub ipv4_gateway : String,
    pub ipv6_address : String,
    pub ipv6_netmask : String,
    pub ipv6_gateway : Option<String>,
    pub bus_address : Option<String>
}