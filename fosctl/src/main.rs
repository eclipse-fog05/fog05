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

#[macro_use]
extern crate failure;
#[macro_use]
extern crate prettytable;
extern crate base64;
extern crate exitfailure;

use clap::arg_enum;
use exitfailure::ExitFailure;
use structopt::StructOpt;
use uuid::Uuid;
mod fim;
mod force;
mod types;

arg_enum! {
    #[derive(Debug)]
    pub enum Kind {
        Entity,
        FIM,
        Cloud,
        Instance,
    }
}

arg_enum! {
    #[derive(Debug)]
    pub enum FIMKind {
        FDU,
        Network,
        Node,
        Instance,
    }
}

#[derive(StructOpt, Debug)]
pub enum AddKind {
    Entity {
        #[structopt(parse(from_os_str), name = "Entity descriptor path")]
        descriptor_path: std::path::PathBuf,
    },
    FIM {
        #[structopt(name = "FIM UUID (v4)")]
        fim_id: Uuid,
        #[structopt(name = "Zenoh Locator for the FIM")]
        locator: String,
    },
    Cloud {
        #[structopt(name = "K8s UUID (v4)")]
        cloud_id: Uuid,
        #[structopt(parse(from_os_str), name = "K8s configuration path")]
        cloud_conf_path: std::path::PathBuf,
        #[structopt(parse(from_os_str), name = "CA file Path")]
        cloud_ca: std::path::PathBuf,
        #[structopt(parse(from_os_str), name = "Certificate file Path")]
        cloud_cert: std::path::PathBuf,
        #[structopt(parse(from_os_str), name = "Key file Path")]
        cloud_key: std::path::PathBuf,
    },
    Instance {
        entity_id: Uuid,
        #[structopt(short = "f", long = "fim-id", name = "FIM UUID")]
        fim_id: Option<Uuid>,
        #[structopt(short = "c", long = "cloud-id", name = "Cloud UUID")]
        cloud_id: Option<Uuid>,
    },
}

#[derive(StructOpt, Debug)]
pub enum GetKind {
    Entity { id: Option<Uuid> },
    FIM { id: Option<Uuid> },
    Cloud { id: Option<Uuid> },
    Instance { id: Option<Uuid> },
}

#[derive(StructOpt, Debug)]
pub enum DeleteKind {
    Entity { id: Uuid },
    FIM { id: Uuid },
    Cloud { id: Uuid },
    Instance { id: Uuid },
}

#[derive(StructOpt, Debug)]
pub enum FOSCtl {
    Add(AddKind),
    Get(GetKind),
    Delete(DeleteKind),
    FIM(FIMCtl),
}

#[derive(StructOpt, Debug)]
pub enum AddFIMKind {
    FDU {
        #[structopt(parse(from_os_str), name = "FDU descriptor path")]
        descriptor_path: std::path::PathBuf,
    },
    Network {
        #[structopt(parse(from_os_str), name = "Network descriptor path")]
        descriptor_path: std::path::PathBuf,
    },
    Instance {
        fdu_id: Uuid,
    },
}

#[derive(StructOpt, Debug)]
pub enum DeleteFIMKind {
    FDU { id: Uuid },
    Network { id: Uuid },
    Instance { id: Uuid },
}

#[derive(StructOpt, Debug)]
pub enum GetFIMKind {
    FDU { id: Option<Uuid> },
    Network { id: Option<Uuid> },
    Instance { id: Option<Uuid> },
    Node { id: Option<Uuid> },
}

#[derive(StructOpt, Debug)]
pub enum FIMCtl {
    Add(AddFIMKind),
    Get(GetFIMKind),
    Delete(DeleteFIMKind),
}

fn main() -> Result<(), ExitFailure> {
    let force_host = match std::env::var("FORCE") {
        Ok(s) => s,
        Err(_) => String::from("127.0.0.1"),
    };

    let zlocator = match std::env::var("FOSZENOH") {
        Ok(s) => s,
        Err(_) => String::from("tcp/127.0.0.1:7447"),
    };

    let args = FOSCtl::from_args();
    println!("{:?}", args);
    match args {
        FOSCtl::FIM(fim_args) => fim::fim_cli(fim_args, zlocator),
        _ => force::force_cli(args, force_host),
    }
}
