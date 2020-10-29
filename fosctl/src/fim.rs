extern crate base64;
extern crate exitfailure;

use clap::arg_enum;
use exitfailure::ExitFailure;
use failure::ResultExt;
use prettytable::Table;
use std::io::{Error, ErrorKind};
use std::time::Duration;
use structopt::StructOpt;
use uuid::Uuid;
use fog05_sdk::im::node::{NodeInfo, NodeStatus, NodeStatusEnum};
use fog05_sdk::zconnector::ZConnector;

use async_std::sync::Arc;

use zenoh::*;

use crate::types;
use crate::{FIMCtl, FIMKind, AddFIMKind, GetFIMKind, DeleteFIMKind};

pub fn fim_cli(args : FIMCtl, zlocator : String) -> Result<(), ExitFailure> {
    async_std::task::block_on(
        async move {
            let zenoh = Arc::new(Zenoh::new(Properties::from(format!("mode=client;peer={}",zlocator)).into()).await.unwrap());
            let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));
            let mut table = Table::new();
            match args {
                FIMCtl::Add(ak) => {
                    match ak {
                        AddFIMKind::FDU { descriptor_path } => {
                            unimplemented!()
                        }
                        AddFIMKind::Network { descriptor_path } => {
                            unimplemented!()
                        }
                        AddFIMKind::Instance { fdu_id } => {
                            unimplemented!()
                        }
                    }
                }
                FIMCtl::Get(gk) => match gk {
                    GetFIMKind::FDU { id } =>
                        match id {
                        Some(fdu_id) => {
                            unimplemented!()
                        }
                        None => {
                            unimplemented!()
                        }
                    },
                    GetFIMKind::Network { id } => {
                        match id {
                            Some(net_id) => {
                                unimplemented!()
                            }
                            None => {
                                unimplemented!()
                            }
                        }
                    }
                    GetFIMKind::Instance { id } => {
                        match id {
                            Some(instance_id) => {
                                unimplemented!()
                            }
                            None => {
                                unimplemented!()
                            }
                        }
                    }
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
                                "OS"
                            ]);
                            table.add_row(row![
                                ni.uuid,
                                ni.name,
                                ns.status,
                                ns.supported_hypervisors.join(","),
                                ni.cpu[0].arch,
                                ni.os
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
                FIMCtl::Delete(dk) => {
                    match dk {
                        DeleteFIMKind::FDU { id } => {
                            unimplemented!()
                        }
                        DeleteFIMKind::Network { id } => {
                            unimplemented!()
                        }
                        DeleteFIMKind::Instance { id } => {
                           unimplemented!()
                        }
                    }
                }
            }
        }
    )
}