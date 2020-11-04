extern crate base64;
extern crate exitfailure;

use exitfailure::ExitFailure;
use failure::ResultExt;
use prettytable::Table;
use std::io::{Error, ErrorKind};
use std::time::Duration;

use fog05_sdk::im::entity::{EntityDescriptor, EntityRecord};

use crate::types;
use crate::{AddKind, DeleteKind, FOSCtl, GetKind};

pub fn force_cli(args: FOSCtl, force_host: String) -> Result<(), ExitFailure> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(10))
        .build()
        .with_context(|_| "Unable to build HTTP client".to_string())?;
    match args {
        FOSCtl::Add(ak) => {
            match ak {
                AddKind::Entity { descriptor_path } => {
                    let data = std::fs::read_to_string(&descriptor_path)
                        .with_context(|_| format!("could not read file `{:?}`", descriptor_path))?;
                    let _ = serde_json::from_str::<EntityDescriptor>(&data).with_context(|_| {
                        format!("Descriptor is not valid `{:?}`", descriptor_path)
                    })?;
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let body = types::RequestNewJobMessage {
                        sender: String::from("cli"),
                        job_kind: String::from("onboard"),
                        body: data,
                    };

                    let js_body = serde_json::to_string(&body)
                        .with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client
                        .post(url.as_str())
                        .body(js_body)
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp =
                        serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;

                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job/{}", force_host, resp.job_id);
                    let res = client
                        .get(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp = serde_json::from_str::<types::Job>(&res.text().unwrap())
                        .with_context(|_| "Unable to parse server reply".to_string())?;
                    let descriptor = serde_json::from_str::<EntityDescriptor>(&resp.body)
                        .with_context(|_| "Unable to parse server reply".to_string())?;
                    println!("{}", descriptor.uuid.unwrap());
                    Ok(())
                }
                AddKind::FIM { fim_id, locator } => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/fim", force_host);
                    let params = [
                        ("id", String::from(&fim_id.to_string())),
                        ("locator", String::from(&locator)),
                    ];
                    let res = client
                        .post(url.as_str())
                        .form(&params)
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    match res.status() {
                        reqwest::StatusCode::OK => {
                            println!("{}", fim_id);
                            Ok(())
                        }
                        _ => Ok(()),
                    }
                }
                AddKind::Cloud {
                    cloud_id,
                    cloud_conf_path,
                    cloud_ca,
                    cloud_cert,
                    cloud_key,
                } => {
                    let config_data = std::fs::read_to_string(&cloud_conf_path)
                        .with_context(|_| format!("could not read file `{:?}`", cloud_conf_path))?;
                    let ca_data = std::fs::read_to_string(&cloud_ca)
                        .with_context(|_| format!("could not read file `{:?}`", cloud_ca))?;
                    let cert_data = std::fs::read_to_string(&cloud_cert)
                        .with_context(|_| format!("could not read file `{:?}`", cloud_cert))?;
                    let key_data = std::fs::read_to_string(&cloud_key)
                        .with_context(|_| format!("could not read file `{:?}`", cloud_key))?;
                    let ca_base64 = base64::encode(ca_data);
                    let cert_base64 = base64::encode(cert_data);
                    let key_base64 = base64::encode(key_data);
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/cloud", force_host);
                    let params = [
                        ("id", String::from(&cloud_id.to_string())),
                        ("config", String::from(&config_data)),
                        ("ca", ca_base64),
                        ("cert", cert_base64),
                        ("key", key_base64),
                    ];
                    let res = client
                        .post(url.as_str())
                        .form(&params)
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    match res.status() {
                        reqwest::StatusCode::OK => {
                            println!("{}", cloud_id);
                            Ok(())
                        }
                        _ => Ok(()),
                    }
                }
                AddKind::Instance {
                    entity_id,
                    fim_id,
                    cloud_id,
                } => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let data = types::EntityActionBody {
                        uuid: entity_id,
                        fim_id,
                        cloud_id,
                    };
                    let js_data = serde_json::to_string(&data)
                        .with_context(|_| format!("Could not create body `{:?}`", &data))?;

                    let body = types::RequestNewJobMessage {
                        sender: String::from("cli"),
                        job_kind: String::from("instantiate"),
                        body: js_data,
                    };

                    let js_body = serde_json::to_string(&body)
                        .with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client
                        .post(url.as_str())
                        .body(js_body)
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp =
                        serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;

                    let mut flag = false;
                    while !flag {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job/{}", force_host, resp.job_id);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp = serde_json::from_str::<types::Job>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;
                        if resp.status == "failed" {
                            return Err(ExitFailure::from(Error::new(
                                ErrorKind::InvalidData,
                                "Add Instance failed",
                            )));
                        }
                        if let Ok(record) = serde_json::from_str::<EntityRecord>(&resp.body) {
                            flag = true;
                            println!("{}", record.uuid);
                        }
                    }

                    //let record = serde_json::from_str::<EntityRecord>(&resp.body).with_context(|_| "Unable to parse server reply".to_string())?;

                    Ok(())
                }
            }
        }
        FOSCtl::Get(gk) => match gk {
            GetKind::Entity { id } => match id {
                Some(entity_id) => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity/{}",force_host, entity_id);
                    let res = client
                        .get(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp =
                        serde_json::from_str::<types::GetEntityResponse>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;
                    let desc = resp.entity;
                    let mut table = Table::new();
                    table.add_row(row!["UUID", "ID", "Name", "Version"]);
                    table.add_row(row![
                        desc.uuid.unwrap().to_string(),
                        desc.id,
                        desc.name,
                        desc.entity_version
                    ]);
                    table.printstd();
                    println!("FDUs:");
                    let mut table = Table::new();
                    table.add_row(row![
                        "UUID",
                        "ID",
                        "Name",
                        "Version",
                        "Hypervisor",
                        "Depend On"
                    ]);
                    for fdu in &desc.fdus {
                        table.add_row(row![
                            fdu.uuid.unwrap().to_string(),
                            fdu.id,
                            fdu.name,
                            fdu.fdu_version,
                            fdu.hypervisor,
                            format!("{:?}", fdu.depends_on)
                        ]);
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
                }
                None => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity",force_host);
                    let res = client
                        .get(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp =
                        serde_json::from_str::<types::GetEntitiesResponse>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;
                    let mut table = Table::new();
                    table.add_row(row!["Entity UUID", "ID"]);
                    for id in &resp.entities {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity/{}",force_host, id);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp =
                            serde_json::from_str::<types::GetEntityResponse>(&res.text().unwrap())
                                .with_context(|_| "Unable to parse server reply".to_string())?;
                        let desc = resp.entity;
                        table.add_row(row![id, desc.id]);
                    }
                    table.printstd();
                    Ok(())
                }
            },
            GetKind::FIM { id } => {
                let mut table = Table::new();
                match id {
                    Some(fim_id) => {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/fim/{}",force_host, fim_id);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp =
                            serde_json::from_str::<types::GetFIMResponse>(&res.text().unwrap())
                                .with_context(|_| "Unable to parse server reply".to_string())?;
                        table.add_row(row!["UUID", "Locator"]);
                        table.add_row(row![resp.fim.uuid, resp.fim.locator]);
                        table.printstd();
                        Ok(())
                    }
                    None => {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/fim",force_host);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp =
                            serde_json::from_str::<types::GetFIMsResponse>(&res.text().unwrap())
                                .with_context(|_| "Unable to parse server reply".to_string())?;
                        table.add_row(row!["UUID"]);
                        for f in resp.fims {
                            table.add_row(row![f]);
                        }
                        table.printstd();
                        Ok(())
                    }
                }
            }
            GetKind::Cloud { id } => {
                let mut table = Table::new();
                match id {
                    Some(cloud_id) => {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/cloud/{}",force_host, cloud_id);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp =
                            serde_json::from_str::<types::GetCloudResponse>(&res.text().unwrap())
                                .with_context(|_| "Unable to parse server reply".to_string())?;
                        table.add_row(row!["UUID", "Config"]);
                        table.add_row(row![resp.cloud.uuid, resp.cloud.config]);
                        table.printstd();
                        Ok(())
                    }
                    None => {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/cloud",force_host);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp =
                            serde_json::from_str::<types::GetCloudsResponse>(&res.text().unwrap())
                                .with_context(|_| "Unable to parse server reply".to_string())?;
                        table.add_row(row!["UUID"]);
                        for s in resp.clouds {
                            table.add_row(row![s]);
                        }
                        table.printstd();
                        Ok(())
                    }
                }
            }
            GetKind::Instance { id } => match id {
                Some(instance_id) => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/instances/{}",force_host, instance_id);
                    let res = client
                        .get(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp =
                        serde_json::from_str::<types::GetInstanceResponse>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;
                    let desc = resp.instance;
                    let mut table = Table::new();
                    table.add_row(row!["UUID", "ID", "Status", "FIM", "Cloud"]);

                    let fim_id = match desc.fim_id {
                        Some(id) => format!("{}", id),
                        None => String::from(""),
                    };
                    let cloud_id = match desc.cloud_id {
                        Some(id) => format!("{}", id),
                        None => String::from(""),
                    };

                    table.add_row(row![desc.uuid, desc.id, desc.status, fim_id, cloud_id]);
                    table.printstd();
                    Ok(())
                }
                None => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/instances",force_host);
                    let res = client
                        .get(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let resp =
                        serde_json::from_str::<types::GetInstancesResponse>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;
                    let mut table = Table::new();
                    table.add_row(row!["Entity UUID", "ID", "Status"]);
                    for id in &resp.instances {
                        let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/entity/{}",force_host, id);
                        let res = client
                            .get(url.as_str())
                            .send()
                            .with_context(|_| format!("cold not contact `{:?}`", url))?;
                        let resp = serde_json::from_str::<types::GetInstanceResponse>(
                            &res.text().unwrap(),
                        )
                        .with_context(|_| "Unable to parse server reply".to_string())?;
                        let desc = resp.instance;
                        table.add_row(row![id.to_string(), desc.id.to_string(), desc.status]);
                    }
                    table.printstd();
                    Ok(())
                }
            },
        },
        FOSCtl::Delete(dk) => {
            match dk {
                DeleteKind::Entity { id } => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let data = types::EntityActionBody {
                        uuid: id,
                        fim_id: None,
                        cloud_id: None,
                    };
                    let js_data = serde_json::to_string(&data)
                        .with_context(|_| format!("Could not create body `{:?}`", &data))?;

                    let body = types::RequestNewJobMessage {
                        sender: String::from("cli"),
                        job_kind: String::from("offload"),
                        body: js_data,
                    };

                    let js_body = serde_json::to_string(&body)
                        .with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client
                        .post(url.as_str())
                        .body(js_body)
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let _resp =
                        serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;

                    // let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job/{}", force_host, resp.job_id);
                    // let res = client.get(url.as_str()).send().with_context(|_| format!("cold not contact `{:?}`", url))?;
                    // let resp = serde_json::from_str::<types::Job>(&res.text().unwrap()).with_context(|_| "Unable to parse server reply".to_string())?;
                    // let record = serde_json::from_str::<EntityRecord>(&resp.body).with_context(|_| "Unable to parse server reply".to_string())?;
                    println!("{}", id);
                    Ok(())
                }
                DeleteKind::FIM { id } => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/fim/{}", force_host, id);
                    let _res = client
                        .delete(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    println!("{}", id);
                    Ok(())
                }
                DeleteKind::Cloud { id } => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/cloud/{}", force_host, id);
                    let _res = client
                        .delete(url.as_str())
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    println!("{}", id);
                    Ok(())
                }
                DeleteKind::Instance { id } => {
                    let url = format!("http://{}:9191/system/00000000-0000-0000-0000-000000000000/tenant/00000000-0000-0000-0000-000000000000/job", force_host);
                    let data = types::EntityActionBody {
                        uuid: id,
                        fim_id: None,
                        cloud_id: None,
                    };
                    let js_data = serde_json::to_string(&data)
                        .with_context(|_| format!("Could not create body `{:?}`", &data))?;

                    let body = types::RequestNewJobMessage {
                        sender: String::from("cli"),
                        job_kind: String::from("teardown"),
                        body: js_data,
                    };

                    let js_body = serde_json::to_string(&body)
                        .with_context(|_| format!("Could not create body `{:?}`", &body))?;
                    let res = client
                        .post(url.as_str())
                        .body(js_body)
                        .send()
                        .with_context(|_| format!("cold not contact `{:?}`", url))?;
                    let _resp =
                        serde_json::from_str::<types::ReplyNewJobMessage>(&res.text().unwrap())
                            .with_context(|_| "Unable to parse server reply".to_string())?;
                    println!("{}", id);
                    Ok(())
                }
            }
        }
        _ => unreachable!(),
    }
}
