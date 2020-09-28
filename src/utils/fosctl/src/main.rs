#![feature(let_chains)]
#[macro_use] extern crate failure;
#[macro_use] extern crate prettytable;
extern crate exitfailure;
extern crate base64;

use structopt::StructOpt;
use clap::arg_enum;
use failure::ResultExt;
use exitfailure::ExitFailure;
use std::time::Duration;
use uuid::Uuid;
use prettytable::{Table, Row, Cell};

mod types;


// arg_enum! {
//     #[derive(Debug)]
//     enum Cmd {
//         Add,
//         Get,
//         Delete
//     }
// }

arg_enum! {
    #[derive(Debug)]
    enum Kind {
        Entity,
        FIM,
        Cloud,
        Instance,
    }
}


#[derive(StructOpt,Debug)]
enum AddKind {
    Entity {
        #[structopt(parse(from_os_str),name = "Entity descriptor path")]
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
        #[structopt(parse(from_os_str), name = "Certificate file Path") ]
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

#[derive(StructOpt,Debug)]
enum GetKind {
    Entity {
        id: Option<Uuid>,
    },
    FIM {
        id: Option<Uuid>,
    },
    Cloud {
        id: Option<Uuid>,
    },
    Instance {
        id: Option<Uuid>,
    },
}


#[derive(StructOpt,Debug)]
enum DeleteKind {
    Entity {
        id: Uuid,
    },
    FIM {
        id: Uuid,
    },
    Cloud {
        id: Uuid,
    },
    Instance {
        id: Uuid,
    },
}

#[derive(StructOpt,Debug)]
#[structopt(about = "Eclipse fog05 CLI Tool")]
enum FOSCtl {

    Add(AddKind),
    Get(GetKind),
    Delete(DeleteKind),
}


fn main() -> Result<(), ExitFailure> {

    let force_host = match std::env::var("FORCE") {
        Ok(s) => s,
        Err(_) => String::from("127.0.0.1"),
    };

    let args = FOSCtl::from_args();
    let client = reqwest::blocking::Client::builder().timeout(Duration::from_secs(10)).build().with_context(|_| format!("Unable to build HTTP client"))?;
    println!("{:?}", args);
    match args {
        FOSCtl::Add(ak) => {
            match ak {
                AddKind::Entity{descriptor_path} => {
                    let data = std::fs::read_to_string(&descriptor_path).with_context(|_| format!("could not read file `{:?}`", descriptor_path))?;
                    let _ = serde_json::from_str::<types::EntityDescriptor>(&data).with_context(|_| format!("Descriptor is not valid `{:?}`", descriptor_path))?;
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let body = types::RequestNewJobMessage{
                        sender : String::from("cli"),
                        job_kind : String::from("onboard"),
                            body : data,
                    };

                    let js_body = serde_json::to_string(&body.clone()).with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client.post(url.as_str()).body(js_body).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;

                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job/{}", force_host, resp.job_id);
                    let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::Job>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                    let descriptor = serde_json::from_str::<types::EntityDescriptor>(&resp.body).with_context(|_| format!("Unable to parse server reply"))?;
                    println!("{}",descriptor.uuid.unwrap());
                    Ok(())
                },
                AddKind::FIM{fim_id, locator} => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/fim", force_host);
                    let params = [("id",String::from(&fim_id.to_string())),("locator",String::from(&locator))];
                    let res = client.post(url.as_str()).form(&params).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    match res.status() {
                        reqwest::StatusCode::OK => {
                            println!("{}",fim_id);
                            Ok(())
                        },
                        _ => Ok(())
                    }
                },
                AddKind::Cloud{cloud_id, cloud_conf_path, cloud_ca, cloud_cert, cloud_key} => {
                    let config_data = std::fs::read_to_string(&cloud_conf_path).with_context(|_| format!("could not read file `{:?}`", cloud_conf_path))?;
                    let ca_data = std::fs::read_to_string(&cloud_ca).with_context(|_| format!("could not read file `{:?}`", cloud_ca))?;
                    let cert_data = std::fs::read_to_string(&cloud_cert).with_context(|_| format!("could not read file `{:?}`", cloud_cert))?;
                    let key_data = std::fs::read_to_string(&cloud_key).with_context(|_| format!("could not read file `{:?}`", cloud_key))?;
                    let ca_base64 = base64::encode(ca_data);
                    let cert_base64 = base64::encode(cert_data);
                    let key_base64 = base64::encode(key_data);
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/cloud", force_host);
                    let params = [("id",String::from(&cloud_id.to_string())),("config",String::from(&config_data)), ("ca",ca_base64), ("cert", cert_base64), ("key", key_base64)];
                    let res = client.post(url.as_str()).form(&params).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    match res.status() {
                        reqwest::StatusCode::OK => {
                            println!("{}",cloud_id);
                            Ok(())
                        },
                        _ => Ok(())
                    }
                },
                AddKind::Instance{entity_id, fim_id, cloud_id} =>{
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let data = types::EntityActionBody{
                        uuid : entity_id,
                        fim_id: fim_id,
                        cloud_id: cloud_id,
                    };
                    let js_data = serde_json::to_string(&data.clone()).with_context(|_| format!("Could not create body `{:?}`", &data))?;

                    let body = types::RequestNewJobMessage{
                        sender : String::from("cli"),
                        job_kind : String::from("instantiate"),
                            body : js_data,
                    };

                    let js_body = serde_json::to_string(&body.clone()).with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client.post(url.as_str()).body(js_body).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;

                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job/{}", force_host, resp.job_id);
                    let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::Job>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                    let record = serde_json::from_str::<types::EntityRecord>(&resp.body).with_context(|_| format!("Unable to parse server reply"))?;
                    println!("{}",record.uuid);
                    Ok(())
                },
            }
        },
        FOSCtl::Get(gk) => {
            match gk {
                GetKind::Entity{id} => {
                    match id {
                        Some(entity_id) => {
                            let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity/{}",force_host, entity_id);
                            let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                            let resp = serde_json::from_str::<types::GetEntityResponse>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                            let desc = resp.entity;
                            let mut table = Table::new();
                            table.add_row(row!["UUID","ID", "Name", "Version"]);
                            table.add_row(row![desc.uuid.unwrap().to_string(), desc.id, desc.name, desc.entity_version]);
                            table.printstd();
                            println!("FDUs:");
                            let mut table = Table::new();
                            table.add_row(row!["UUID","ID", "Name", "Version","Hypervisor","Depend On"]);
                            for fdu in &desc.fdus {
                                table.add_row(row![fdu.uuid.unwrap().to_string(), fdu.id, fdu.name, fdu.fdu_version, fdu.hypervisor, format!("{:?}", fdu.depends_on)]);
                            }
                            table.printstd();
                            println!("Networks:");
                            let mut table = Table::new();
                            table.add_row(row!["ID", "Link Kind", "IP Version"]);
                            for net in &desc.virtual_links {
                                table.add_row(row![net.id, net.link_kind, net.ip_version]);
                            }
                            table.printstd();

                            Ok(())

                        },
                        None => {
                            let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity",force_host);
                            let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                            let resp = serde_json::from_str::<types::GetEntitiesResponse>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                            let mut table = Table::new();
                            table.add_row(row!["Entity UUID","ID"]);
                            for id in &resp.entities {
                                let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity/{}",force_host, id);
                                let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                                let resp = serde_json::from_str::<types::GetEntityResponse>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                                let desc = resp.entity;
                                table.add_row(row![id, desc.id]);
                            }
                            table.printstd();
                            Ok(())
                        }
                    }
                },
                GetKind::FIM{id} => {
                    match id {
                        Some(fim_id) => {
                            println!("FIM Get not implemented");
                            Ok(())
                        },
                        None => {
                            println!("FIM Get not implemented");
                            Ok(())
                        }
                    }
                },
                GetKind::Cloud{id} => {
                    match id {
                        Some(cloud_id) => {
                            println!("Cloud Get not implemented");
                            Ok(())
                        },
                        None => {
                            println!("Cloud Get not implemented");
                            Ok(())
                        }
                    }
                },
                GetKind::Instance{id} => {
                    match id {
                        Some(instance_id) => {
                            let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/instances/{}",force_host, instance_id);
                            let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                            let resp = serde_json::from_str::<types::GetInstanceResponse>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                            let desc = resp.instance;
                            let mut table = Table::new();
                            table.add_row(row!["UUID","ID", "Status"]);
                            table.add_row(row![desc.uuid.to_string(), desc.id.to_string(), desc.status]);
                            table.printstd();
                            Ok(())
                        },
                        None => {
                            let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/instances",force_host);
                            let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                            let resp = serde_json::from_str::<types::GetInstancesResponse>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                            let mut table = Table::new();
                            table.add_row(row!["Entity UUID","ID","Status"]);
                            for id in &resp.instances {
                                let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity/{}",force_host, id);
                                let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                                let resp = serde_json::from_str::<types::GetInstanceResponse>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                                let desc = resp.instance;
                                table.add_row(row![id.to_string(), desc.id.to_string(), desc.status]);
                            }
                            table.printstd();
                            Ok(())
                        }
                    }
                },
            }

        }
        FOSCtl::Delete(dk) => {
            match dk {
                DeleteKind::Entity{id} => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let data = types::EntityActionBody{
                        uuid : id,
                        fim_id: None,
                        cloud_id: None,
                    };
                    let js_data = serde_json::to_string(&data.clone()).with_context(|_| format!("Could not create body `{:?}`", &data))?;

                    let body = types::RequestNewJobMessage{
                        sender : String::from("cli"),
                        job_kind : String::from("offload"),
                            body : js_data,
                    };

                    let js_body = serde_json::to_string(&body.clone()).with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client.post(url.as_str()).body(js_body).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;

                    // let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job/{}", force_host, resp.job_id);
                    // let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    // let resp = serde_json::from_str::<types::Job>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                    // let record = serde_json::from_str::<types::EntityRecord>(&resp.body).with_context(|_| format!("Unable to parse server reply"))?;
                    println!("{}",id);
                    Ok(())
                },
                DeleteKind::FIM{id} => {
                    Ok(())
                },
                DeleteKind::Cloud{id} => {
                    Ok(())
                },
                DeleteKind::Instance{id} => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let data = types::EntityActionBody{
                        uuid : id,
                        fim_id: None,
                        cloud_id: None,
                    };
                    let js_data = serde_json::to_string(&data.clone()).with_context(|_| format!("Could not create body `{:?}`", &data))?;

                    let body = types::RequestNewJobMessage{
                        sender : String::from("cli"),
                        job_kind : String::from("teardown"),
                            body : js_data,
                    };

                    let js_body = serde_json::to_string(&body.clone()).with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client.post(url.as_str()).body(js_body).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap()).with_context(|_| format!("Unable to parse server reply"))?;
                    println!("{}",id);
                    Ok(())
                },
            }
        }
    }
}
