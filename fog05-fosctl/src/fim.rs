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

#![allow(unused_variables)]

extern crate base64;
extern crate exitfailure;

use exitfailure::ExitFailure;
use failure::ResultExt;
use prettytable::Table;

use async_std::sync::Arc;

use zenoh::*;

use rand::seq::SliceRandom;

use fog05_sdk::agent::AgentOrchestratorInterfaceClient;
use fog05_sdk::fresult::FError;
use fog05_sdk::im::entity::EntityDescriptor;
use fog05_sdk::im::fdu::FDUDescriptor;
use fog05_sdk::zconnector::ZConnector;

use crate::{AddFIMKind, DeleteFIMKind, FIMCtl, GetFIMKind};

pub fn fim_cli(args: FIMCtl, zlocator: String) -> Result<(), ExitFailure> {
    async_std::task::block_on(async move {
        let zenoh = Arc::new(
            Zenoh::new(Properties::from(format!("mode=client;peer={}", zlocator)).into())
                .await
                .unwrap(),
        );
        let zsession = Arc::new(
            zenoh::net::open(Properties::from(format!("mode=client;peer={}", zlocator)).into())
                .await
                .unwrap(),
        );
        let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));
        let mut table = Table::new();
        match args {
            FIMCtl::Add(ak) => match ak {
                AddFIMKind::FDU { descriptor_path } => {
                    let data = std::fs::read_to_string(&descriptor_path)
                        .with_context(|_| format!("could not read file `{:?}`", descriptor_path))?;

                    let fdu = serde_yaml::from_str::<FDUDescriptor>(&data).with_context(|_| {
                        format!("Descriptor is not valid `{:?}`", descriptor_path)
                    })?;
                    let nodes = zconnector.global.get_all_nodes().await?;
                    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                    log::trace!(
                        "Selected node entry point: {}",
                        entry_point.agent_service_uuid
                    );
                    let node_client = AgentOrchestratorInterfaceClient::new(
                        zsession.clone(),
                        entry_point.agent_service_uuid,
                    );
                    match node_client.onboard_fdu(fdu).await? {
                        Ok(fdu_uuid) => {
                            println!("{}", fdu_uuid);
                            Ok(())
                        }
                        Err(e) => {
                            panic!("Error occured: {}", e);
                        }
                    }
                }
                AddFIMKind::Entity { descriptor_path } => {
                    let data = std::fs::read_to_string(&descriptor_path)
                        .with_context(|_| format!("could not read file `{:?}`", descriptor_path))?;

                    let entity =
                        serde_yaml::from_str::<EntityDescriptor>(&data).with_context(|_| {
                            format!("Descriptor is not valid `{:?}`", descriptor_path)
                        })?;
                    let nodes = zconnector.global.get_all_nodes().await?;
                    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                    log::trace!(
                        "Selected node entry point: {}",
                        entry_point.agent_service_uuid
                    );
                    let node_client = AgentOrchestratorInterfaceClient::new(
                        zsession.clone(),
                        entry_point.agent_service_uuid,
                    );
                    match node_client.onboard_entity(entity).await? {
                        Ok(entity_uuid) => {
                            println!("{}", entity_uuid);
                            Ok(())
                        }
                        Err(e) => {
                            panic!("Error occured: {}", e);
                        }
                    }
                }
                AddFIMKind::Network { descriptor_path } => unimplemented!(),
                AddFIMKind::Instance { id } => {
                    let nodes = zconnector.global.get_all_nodes().await?;
                    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                    let node_client = AgentOrchestratorInterfaceClient::new(
                        zsession.clone(),
                        entry_point.agent_service_uuid,
                    );

                    match zconnector.global.get_fdu(id).await {
                        Ok(_fdu) => {
                            let instance = node_client.schedule_fdu(id).await??;
                            node_client.configure_fdu(instance.uuid).await??;
                            let instance = node_client.start_fdu(instance.uuid).await??;
                            println!("{}", instance.uuid);
                            Ok(())
                        }
                        Err(FError::NotFound) => match zconnector.global.get_entity(id).await {
                            Ok(_entity) => {
                                let instance_uuid = node_client.schedule_entity(id).await??;
                                println!("{}", instance_uuid);
                                Ok(())
                            }
                            Err(e) => {
                                panic!("Error occured: {}", e);
                            }
                        },
                        Err(e) => {
                            panic!("Error occured: {}", e);
                        }
                    }
                }
            },
            FIMCtl::Get(gk) => match gk {
                GetFIMKind::FDU { id } => match id {
                    Some(fdu_id) => {
                        let fdu = zconnector.global.get_fdu(fdu_id).await?;
                        table.add_row(row!["UUID", "ID", "Name", "Hypervisor", "Version",]);
                        table.add_row(row![
                            fdu.uuid.unwrap(),
                            fdu.id,
                            fdu.name,
                            fdu.hypervisor,
                            fdu.fdu_version,
                        ]);
                        table.printstd();
                        Ok(())
                    }
                    None => {
                        let fdus = zconnector.global.get_all_fdu().await?;
                        table.add_row(row!["UUID", "ID", "Name", "Hypervisor", "Version",]);
                        for f in fdus {
                            table.add_row(row![
                                f.uuid.unwrap(),
                                f.id,
                                f.name,
                                f.hypervisor,
                                f.fdu_version,
                            ]);
                        }

                        table.printstd();
                        Ok(())
                    }
                },
                GetFIMKind::Entity { id } => match id {
                    Some(entity_id) => unimplemented!(),
                    None => unimplemented!(),
                },
                GetFIMKind::Network { id } => match id {
                    Some(net_id) => unimplemented!(),
                    None => unimplemented!(),
                },
                GetFIMKind::Instance { id } => match id {
                    Some(instance_id) => match zconnector.global.get_instance(instance_id).await {
                        Ok(fdu) => {
                            table.add_row(row!["UUID", "ID", "Node", "Status", "Restarts"]);
                            table.add_row(row![
                                fdu.uuid,
                                fdu.fdu_uuid,
                                fdu.node,
                                fdu.status,
                                fdu.restarts
                            ]);
                            table.printstd();
                            Ok(())
                        }
                        Err(FError::NotFound) => {
                            match zconnector.global.get_entity_instance(instance_id).await {
                                Ok(entity) => {
                                    let mut fdus = String::from("");

                                    for fdu in entity.fdus {
                                        let f = format!("{}\n", fdu);
                                        fdus.push_str(&f);
                                    }

                                    table.add_row(row!["UUID", "ID", "FDUs", "Status"]);
                                    table.add_row(row![
                                        entity.uuid,
                                        entity.id,
                                        fdus,
                                        entity.status,
                                    ]);
                                    table.printstd();
                                    Ok(())
                                }
                                Err(e) => {
                                    panic!("Error occured: {}", e);
                                }
                            }
                        }
                        Err(e) => {
                            panic!("Error occured: {}", e);
                        }
                    },
                    None => {
                        // first getting FDUs ...

                        table.add_row(row![
                            "UUID", "ID", "Node", "Status", "Kind", "FDUs", "Restarts"
                        ]);
                        let fdus = zconnector.global.get_all_instances().await?;
                        for f in fdus {
                            table.add_row(row![
                                f.uuid, f.fdu_uuid, f.node, f.status, "FDU", "-", f.restarts
                            ]);
                        }

                        // then
                        let entities = zconnector.global.get_all_entities_instances().await?;
                        for e in entities {
                            let mut efdus = String::from("");

                            for fdu in e.fdus {
                                let f = format!("{}\n", fdu);
                                efdus.push_str(&f);
                            }

                            table.add_row(row![e.uuid, e.id, "", e.status, "Entity", efdus, "-"]);
                        }

                        table.printstd();
                        Ok(())
                    }
                },
                GetFIMKind::Node { id } => match id {
                    Some(node_id) => {
                        let ni = zconnector.global.get_node_info(node_id).await?;
                        let ns = zconnector.global.get_node_status(node_id).await?;
                        table.add_row(row![
                            "UUID",
                            "Hostname",
                            "Status",
                            "Hypervisors",
                            "Architecture",
                            "OS",
                            "Addresses"
                        ]);

                        let mut ips = String::from("");

                        for iface in ns.interfaces {
                            if iface.name != "lo" {
                                let mut face = String::from("");

                                for address in iface.ips {
                                    let f = format!("{} {}\n", iface.name, address);
                                    face.push_str(&f);
                                }
                                ips.push_str(&face);
                            }
                        }

                        table.add_row(row![
                            ni.uuid,
                            ni.name,
                            ns.status,
                            ns.supported_hypervisors.join(","),
                            ni.cpu[0].arch,
                            ni.os,
                            ips,
                        ]);
                        table.printstd();
                        Ok(())
                    }
                    None => {
                        table.add_row(row![
                            "UUID",
                            "Hostname",
                            "Status",
                            "Hypervisors",
                            "Architecture",
                            "OS"
                        ]);
                        let nodes = zconnector.global.get_all_nodes().await?;
                        for node in nodes {
                            let ns = zconnector.global.get_node_status(node.uuid).await?;
                            table.add_row(row![
                                node.uuid,
                                node.name,
                                ns.status,
                                ns.supported_hypervisors.join(","),
                                node.cpu[0].arch,
                                node.os
                            ]);
                        }
                        table.printstd();
                        Ok(())
                    }
                },
            },
            FIMCtl::Delete(dk) => match dk {
                DeleteFIMKind::FDU { id } => {
                    let nodes = zconnector.global.get_all_nodes().await?;
                    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                    log::trace!(
                        "Selected node entry point: {}",
                        entry_point.agent_service_uuid
                    );
                    let node_client = AgentOrchestratorInterfaceClient::new(
                        zsession.clone(),
                        entry_point.agent_service_uuid,
                    );
                    match node_client.offload_fdu(id).await? {
                        Ok(fdu_uuid) => {
                            println!("{}", fdu_uuid);
                            Ok(())
                        }
                        Err(e) => {
                            panic!("Error occured: {}", e);
                        }
                    }
                }
                DeleteFIMKind::Entity { id } => {
                    let nodes = zconnector.global.get_all_nodes().await?;
                    let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                    log::trace!(
                        "Selected node entry point: {}",
                        entry_point.agent_service_uuid
                    );
                    let node_client = AgentOrchestratorInterfaceClient::new(
                        zsession.clone(),
                        entry_point.agent_service_uuid,
                    );
                    match node_client.offload_entity(id).await? {
                        Ok(entity_uuid) => {
                            println!("{}", entity_uuid);
                            Ok(())
                        }
                        Err(e) => {
                            panic!("Error occured: {}", e);
                        }
                    }
                }
                DeleteFIMKind::Network { id } => unimplemented!(),
                DeleteFIMKind::Instance { id } => match zconnector.global.get_instance(id).await {
                    Ok(_fdu) => {
                        let nodes = zconnector.global.get_all_nodes().await?;
                        let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                        let node_client = AgentOrchestratorInterfaceClient::new(
                            zsession.clone(),
                            entry_point.agent_service_uuid,
                        );

                        let instance = node_client.stop_fdu(id).await??;
                        node_client.clean_fdu(instance.uuid).await??;
                        let instance = node_client.undefine_fdu(instance.uuid).await??;
                        println!("{}", instance.uuid);
                        Ok(())
                    }
                    Err(FError::NotFound) => {
                        match zconnector.global.get_entity_instance(id).await {
                            Ok(_entity) => {
                                let nodes = zconnector.global.get_all_nodes().await?;
                                let entry_point = nodes.choose(&mut rand::thread_rng()).unwrap();
                                let node_client = AgentOrchestratorInterfaceClient::new(
                                    zsession.clone(),
                                    entry_point.agent_service_uuid,
                                );

                                let entity_uuid = node_client.deschedule_entity(id).await??;
                                println!("{}", entity_uuid);
                                Ok(())
                            }
                            Err(e) => {
                                panic!("Error occured: {}", e);
                            }
                        }
                    }
                    Err(e) => {
                        panic!("Error occured: {}", e);
                    }
                },
            },
        }
    })
}
