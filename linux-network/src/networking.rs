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
#![allow(unused)]

use std::time::Duration;

use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};
use async_std::task;

use log::{error, info, trace};

use zrpc::ZServe;
use zrpc_macros::zserver;

use fog05_sdk::agent::{AgentPluginInterfaceClient, OSClient};
use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::plugins::NetworkingPlugin;
use fog05_sdk::types::{
    BridgeKind, ConnectionPoint, GREKind, IPAddress, IPConfiguration, IPVersion, Interface,
    InterfaceKind, LinkKind, MACAddress, MACVLANKind, MCastVXLANInfo, NetworkNamespace, PluginKind,
    VETHKind, VLANKind, VXLANKind, VirtualInterface, VirtualInterfaceConfig,
    VirtualInterfaceConfigKind, VirtualInterfaceKind, VirtualNetwork,
};

use uuid::Uuid;

use futures::stream::TryStreamExt;

use rand::distributions::Alphanumeric;
use rand::{thread_rng, Rng};

use netlink_packet_route::rtnl::address::nlas::Nla;
use rtnetlink::new_connection;
use rtnetlink::NetworkNamespace as NetlinkNetworkNamespace;

use std::os::unix::io::IntoRawFd;

use crate::types::{LinuxNetwork, LinuxNetworkState};

#[zserver]
impl NetworkingPlugin for LinuxNetwork {
    /// Creates the default fosbr0 virtual network
    /// it's UUID is 00000000-0000-0000-0000-000000000000
    /// it is a VXLAN kind of virtual network
    /// VNI: 3845
    /// MCast Addr: 239.15.5.0
    /// Port 3845
    /// Net: 10.240.0.0/16
    /// Gateway: 10.240.0.1
    /// Agents checks if there is already a default network in the system
    /// if so it calls with the DHCP set to false
    /// otherwise it is set to true an a DHCP for the default network
    /// is started in the node
    async fn create_default_virtual_network(&self, dhcp: bool) -> FResult<VirtualNetwork> {
        log::debug!(
            "entering create_default_virtual_network with dhcp: {}",
            dhcp
        );

        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let default_net_uuid = Uuid::nil();

        let default_br_uuid = Uuid::new_v4();
        let default_br_name = String::from("fosbr0");

        let default_vxl_uuid = Uuid::new_v4();
        let default_vxl_name = String::from("fosvxl0");
        let default_vni: u32 = 3845;
        let default_mcast_addr = IPAddress::V4(std::net::Ipv4Addr::new(239, 15, 5, 0));
        let default_port: u16 = 3845;

        let dafault_ext_if_name = self.get_overlay_iface()?;

        let mut default_vnet = VirtualNetwork {
            uuid: default_net_uuid,
            id: String::from("fos-default"),
            name: Some(String::from("Eclipse fog05 default virtual network")),
            is_mgmt: false,
            link_kind: LinkKind::L2(MCastVXLANInfo {
                vni: default_vni,
                mcast_addr: default_mcast_addr,
                port: default_port,
            }),
            ip_version: IPVersion::IPV4,
            ip_configuration: None,
            connection_points: Vec::new(),
            interfaces: vec![default_br_uuid, default_vxl_uuid],
        };
        if dhcp {
            let ip_conf = IPConfiguration {
                subnet: Some((IPAddress::V4(std::net::Ipv4Addr::new(10, 240, 0, 0)), 16)),
                gateway: Some(IPAddress::V4(std::net::Ipv4Addr::new(10, 240, 0, 1))),
                dhcp_range: Some((
                    IPAddress::V4(std::net::Ipv4Addr::new(10, 240, 0, 2)),
                    IPAddress::V4(std::net::Ipv4Addr::new(10, 240, 255, 254)),
                )),
                dns: Some(vec![
                    IPAddress::V4(std::net::Ipv4Addr::new(208, 67, 222, 222)),
                    IPAddress::V4(std::net::Ipv4Addr::new(208, 67, 222, 220)),
                ]),
            };
            default_vnet.ip_configuration = Some(ip_conf);
        }

        let v_bridge = VirtualInterface {
            uuid: default_br_uuid,
            if_name: default_br_name.clone(),
            net_ns: None,
            parent: None,
            kind: VirtualInterfaceKind::BRIDGE(BridgeKind {
                childs: vec![default_vxl_uuid],
            }),
            addresses: Vec::new(),
            phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        };

        let res = self.create_bridge(default_br_name.clone()).await?;
        log::trace!("Bridge creation res: {:?}", res);
        self.set_iface_up(default_br_name.clone()).await?;

        let v_vxl = VirtualInterface {
            uuid: default_vxl_uuid,
            if_name: default_vxl_name.clone(),
            net_ns: None,
            parent: Some(default_br_uuid),
            kind: VirtualInterfaceKind::VXLAN(VXLANKind {
                vni: default_vni,
                mcast_addr: default_mcast_addr,
                port: default_port,
                dev: Interface {
                    if_name: dafault_ext_if_name.clone(),
                    kind: InterfaceKind::ETHERNET,
                    addresses: Vec::new(),
                    phy_address: None,
                },
            }),
            addresses: Vec::new(),
            phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        };

        let res = self
            .create_mcast_vxlan(
                default_vxl_name.clone(),
                dafault_ext_if_name.clone(),
                default_vni,
                default_mcast_addr,
                default_port,
            )
            .await?;

        log::trace!("VXLAN creation res: {:?}", res);
        self.set_iface_master(default_vxl_name.clone(), default_br_name.clone())
            .await?;
        self.set_iface_up(default_vxl_name).await?;

        self.add_iface_address(
            default_br_name,
            IPAddress::V4(std::net::Ipv4Addr::new(10, 240, 0, 1)),
            16,
        )
        .await?;

        self.connector
            .global
            .add_node_interface(node_uuid, &v_bridge)
            .await?;

        self.connector
            .global
            .add_node_interface(node_uuid, &v_vxl)
            .await?;

        self.connector
            .global
            .add_node_virutal_network(node_uuid, &default_vnet)
            .await?;

        log::debug!(
            "leaving create_default_virtual_network with res: {:?}",
            default_vnet
        );
        Ok(default_vnet)
    }

    async fn create_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork> {
        // this function is never called directly from API/Orchestrator
        Err(FError::Unimplemented)
        // match self.connector.global.get_virtual_network(vnet_uuid).await {
        //     Ok(vnet) => {
        //         let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        //         self.connector
        //             .global
        //             .add_node_virutal_network(node_uuid, &vnet)
        //             .await?;
        //         Ok(vnet)
        //     }
        //     Err(FError::NotFound) => {
        //         // a virtual network with this UUID does not exists
        //         Err(FError::NotFound)
        //     }
        //     Err(err) => {
        //         //any other error just return the error
        //         Err(err)
        //     }
        // }
    }

    async fn get_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        self.connector
            .global
            .get_node_virtual_network(node_uuid, vnet_uuid)
            .await
    }

    async fn delete_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_virtual_network(node_uuid, vnet_uuid)
            .await
        {
            Err(_) => Err(FError::NotFound),
            Ok(vnet) => {
                if !vnet.interfaces.is_empty() {
                    return Err(FError::NetworkingError(
                        "Cannot remove virtual network that has attached interfaces".into(),
                    ));
                }
                if !vnet.connection_points.is_empty() {
                    return Err(FError::NetworkingError(
                        "Cannot remove virtual network that has attached connection points".into(),
                    ));
                }

                self.connector
                    .global
                    .remove_node_virtual_network(node_uuid, vnet_uuid)
                    .await?;
                Ok(vnet)
            }
        }
    }

    async fn create_connection_point(&self) -> FResult<ConnectionPoint> {
        Err(FError::Unimplemented)
        // let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        // let cp_uuid = Uuid::new_v4();
        // match self
        //     .connector
        //     .global
        //     .get_node_connection_point(node_uuid, cp_uuid)
        //     .await
        // {
        //     Err(_) => {
        //         let cp = ConnectionPoint {
        //             uuid: cp_uuid,
        //             net_ns: Uuid::new_v4(),
        //             bridge: Uuid::new_v4(),
        //             internal_veth: Uuid::new_v4(),
        //             external_veth: Uuid::new_v4(),
        //         };
        //         self.connector
        //             .global
        //             .add_node_connection_point(node_uuid, &cp)
        //             .await?;
        //         Ok(cp)
        //     }
        //     Ok(_) => Err(FError::AlreadyPresent),
        // }
    }

    async fn get_connection_point(&self, cp_uuid: Uuid) -> FResult<ConnectionPoint> {
        Err(FError::Unimplemented)
        // let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        // self.connector
        //     .global
        //     .get_node_connection_point(node_uuid, cp_uuid)
        //     .await
    }

    async fn delete_connection_point(&self, cp_uuid: Uuid) -> FResult<Uuid> {
        Err(FError::Unimplemented)
        // let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        // match self
        //     .connector
        //     .global
        //     .get_node_connection_point(node_uuid, cp_uuid)
        //     .await
        // {
        //     Err(_) => Err(FError::NotFound),
        //     Ok(_) => {
        //         self.connector
        //             .global
        //             .remove_node_connection_point(node_uuid, cp_uuid)
        //             .await?;
        //         Ok(cp_uuid)
        //     }
        // }
    }

    async fn create_virtual_interface(
        &self,
        intf: VirtualInterfaceConfig,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match intf.kind {
            VirtualInterfaceConfigKind::VXLAN(conf) => {
                let ext_face = self.get_dummy_face();
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name.clone(),
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VXLAN(VXLANKind {
                        vni: conf.vni,
                        mcast_addr: conf.mcast_addr,
                        port: conf.port,
                        dev: ext_face.clone(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };

                self.create_mcast_vxlan(
                    intf.if_name,
                    ext_face.if_name.clone(),
                    conf.vni,
                    conf.mcast_addr,
                    conf.port,
                )
                .await?;

                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::BRIDGE => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name.clone(),
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::BRIDGE(BridgeKind { childs: Vec::new() }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };

                self.create_bridge(intf.if_name).await?;

                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::VETH => {
                let external_face_name = self.generate_random_interface_name();
                let internal_iface_uuid = Uuid::new_v4();
                let external_iface_uuid = Uuid::new_v4();
                let v_iface_internal = VirtualInterface {
                    uuid: internal_iface_uuid,
                    if_name: intf.if_name.clone(),
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VETH(VETHKind {
                        pair: external_iface_uuid,
                        internal: true,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                let v_iface_external = VirtualInterface {
                    uuid: external_iface_uuid,
                    if_name: external_face_name.clone(),
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VETH(VETHKind {
                        pair: internal_iface_uuid,
                        internal: false,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };

                self.create_veth(intf.if_name, external_face_name).await?;

                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface_internal)
                    .await?;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface_external)
                    .await?;
                Ok(v_iface_internal)
            }
            VirtualInterfaceConfigKind::VLAN(conf) => {
                let ext_face = self.get_dummy_face();
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name.clone(),
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VLAN(VLANKind {
                        tag: conf.tag,
                        dev: ext_face.clone(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };

                self.create_vlan(intf.if_name, ext_face.if_name, conf.tag)
                    .await?;

                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::MACVLAN => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::MACVLAN(MACVLANKind {
                        dev: self.get_dummy_face(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                Err(FError::Unimplemented)
                // self.connector
                //     .global
                //     .add_node_interface(node_uuid, &v_iface)
                //     .await?;
                // Ok(v_iface)
            }
            VirtualInterfaceConfigKind::GRE(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::GRE(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                Err(FError::Unimplemented)
                // self.connector
                //     .global
                //     .add_node_interface(node_uuid, &v_iface)
                //     .await?;
                // Ok(v_iface)
            }
            VirtualInterfaceConfigKind::GRETAP(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::GRETAP(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                Err(FError::Unimplemented)
                // self.connector
                //     .global
                //     .add_node_interface(node_uuid, &v_iface)
                //     .await?;
                // Ok(v_iface)
            }
            VirtualInterfaceConfigKind::IP6GRE(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::IP6GRE(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                Err(FError::Unimplemented)
                // self.connector
                //     .global
                //     .add_node_interface(node_uuid, &v_iface)
                //     .await?;
                // Ok(v_iface)
            }
            VirtualInterfaceConfigKind::IP6GRETAP(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::IP6GRETAP(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                Err(FError::Unimplemented)
                // self.connector
                //     .global
                //     .add_node_interface(node_uuid, &v_iface)
                //     .await?;
                // Ok(v_iface)
            }
        }
    }

    async fn get_virtual_interface(&self, intf_uuid: Uuid) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        self.connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await
    }

    async fn delete_virtual_interface(&self, intf_uuid: Uuid) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await
        {
            Err(_) => Err(FError::NotFound),
            Ok(intf) => match intf.net_ns {
                Some(_) => Err(FError::Unimplemented),
                None => {
                    if let VirtualInterfaceKind::VETH(ref info) = intf.kind {
                        let pair = self
                            .connector
                            .global
                            .get_node_interface(node_uuid, info.pair)
                            .await?;
                        self.del_iface(pair.if_name.clone()).await?;
                        self.connector
                            .global
                            .remove_node_interface(node_uuid, info.pair)
                            .await?;
                    }

                    self.del_iface(intf.if_name.clone()).await?;
                    self.connector
                        .global
                        .remove_node_interface(node_uuid, intf_uuid)
                        .await?;
                    Ok(intf)
                }
            },
        }
    }

    async fn create_virtual_bridge(&self, br_name: String) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let v_iface = VirtualInterface {
            uuid: Uuid::new_v4(),
            if_name: br_name,
            net_ns: None,
            parent: None,
            kind: VirtualInterfaceKind::BRIDGE(BridgeKind { childs: Vec::new() }),
            addresses: Vec::new(),
            phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        };

        self.create_bridge(v_iface.if_name.clone()).await?;

        self.connector
            .global
            .add_node_interface(node_uuid, &v_iface)
            .await?;
        Ok(v_iface)
    }

    async fn get_virtual_bridge(&self, br_uuid: Uuid) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_interface(node_uuid, br_uuid)
            .await
        {
            Err(err) => Err(err),
            Ok(i) => match i.kind {
                VirtualInterfaceKind::BRIDGE(_) => Ok(i),
                _ => Err(FError::WrongKind),
            },
        }
    }

    async fn delete_virtual_bridge(&self, br_uuid: Uuid) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_interface(node_uuid, br_uuid)
            .await
        {
            Err(err) => Err(err),
            Ok(i) => match i.net_ns {
                Some(_) => Err(FError::Unimplemented),
                None => match i.kind {
                    VirtualInterfaceKind::BRIDGE(_) => {
                        self.del_iface(i.if_name.clone()).await?;
                        self.connector
                            .global
                            .remove_node_interface(node_uuid, br_uuid)
                            .await?;
                        Ok(i)
                    }
                    _ => Err(FError::WrongKind),
                },
            },
        }
    }

    async fn create_network_namespace(&self) -> FResult<NetworkNamespace> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let ns_name = self.generate_random_netns_name();
        let netns = NetworkNamespace {
            uuid: Uuid::new_v4(),
            ns_name: ns_name.clone(),
            interfaces: Vec::new(),
        };
        self.add_netns(ns_name).await?;
        self.connector
            .global
            .add_node_network_namespace(node_uuid, &netns)
            .await?;
        Ok(netns)
    }

    async fn get_network_namespace(&self, ns_uuid: Uuid) -> FResult<NetworkNamespace> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        self.connector
            .global
            .get_node_network_namespace(node_uuid, ns_uuid)
            .await
    }

    async fn delete_network_namespace(&self, ns_uuid: Uuid) -> FResult<NetworkNamespace> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_network_namespace(node_uuid, ns_uuid)
            .await
        {
            Err(_) => Err(FError::NotFound),
            Ok(netns) => {
                self.del_netns(netns.ns_name.clone()).await?;
                self.connector
                    .global
                    .remove_node_network_namespace(node_uuid, ns_uuid)
                    .await?;
                Ok(netns)
            }
        }
    }

    async fn bind_interface_to_connection_point(
        &self,
        intf_uuid: Uuid,
        cp_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let cp = self
            .connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await?;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;

        Err(FError::Unimplemented)
        // iface.net_ns = Some(cp.net_ns);
        // self.connector
        //     .global
        //     .add_node_interface(node_uuid, &iface)
        //     .await?;
        // Ok(iface)
    }

    async fn unbind_interface_from_connection_point(
        &self,
        intf_uuid: Uuid,
        cp_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let cp = self
            .connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await?;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;

        Err(FError::Unimplemented)

        // match iface.net_ns {
        //     Some(ns) => {
        //         if ns == cp.net_ns {
        //             iface.net_ns = None;
        //             self.connector
        //                 .global
        //                 .add_node_interface(node_uuid, &iface)
        //                 .await?;
        //             return Ok(iface);
        //         }
        //         Err(FError::NotConnected)
        //     }
        //     None => Err(FError::NotConnected),
        // }
    }

    async fn bind_connection_point_to_virtual_network(
        &self,
        cp_uuid: Uuid,
        vnet_uuid: Uuid,
    ) -> FResult<ConnectionPoint> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let cp = self
            .connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await?;
        let mut vnet = self
            .connector
            .global
            .get_node_virtual_network(node_uuid, vnet_uuid)
            .await?;
        Err(FError::Unimplemented)
        // vnet.connection_points.push(cp.uuid);
        // self.connector
        //     .global
        //     .add_node_virutal_network(node_uuid, &vnet)
        //     .await?;
        // Ok(cp)
    }

    async fn unbind_connection_point_from_virtual_network(
        &self,
        cp_uuid: Uuid,
        vnet_uuid: Uuid,
    ) -> FResult<ConnectionPoint> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let cp = self
            .connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await?;
        let mut vnet = self
            .connector
            .global
            .get_node_virtual_network(node_uuid, vnet_uuid)
            .await?;
        Err(FError::Unimplemented)
        // match vnet.connection_points.iter().position(|&x| x == cp.uuid) {
        //     Some(p) => {
        //         vnet.connection_points.remove(p);
        //         self.connector
        //             .global
        //             .add_node_virutal_network(node_uuid, &vnet)
        //             .await?;
        //         Ok(cp)
        //     }
        //     None => Err(FError::NotConnected),
        // }
    }

    async fn get_interface_addresses(&self, intf_uuid: Uuid) -> FResult<Vec<IPAddress>> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        Ok(iface.addresses)
    }

    async fn get_overlay_iface(&self) -> FResult<String> {
        Ok(self.get_overlay_face_from_config().if_name)
    }
    async fn get_vlan_face(&self) -> FResult<String> {
        Ok(self.get_dummy_face().if_name)
    }

    async fn create_macvlan_interface(&self, master_intf: String) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let v_iface = VirtualInterface {
            uuid: Uuid::new_v4(),
            if_name: self.generate_random_interface_name(),
            net_ns: None,
            parent: None,
            kind: VirtualInterfaceKind::MACVLAN(MACVLANKind {
                dev: Interface {
                    if_name: master_intf,
                    kind: InterfaceKind::ETHERNET,
                    addresses: Vec::new(),
                    phy_address: None,
                },
            }),
            addresses: Vec::new(),
            phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        };
        Err(FError::Unimplemented)
        // self.connector
        //     .global
        //     .add_node_interface(node_uuid, &v_iface)
        //     .await?;
        // Ok(v_iface)
    }

    async fn delete_macvan_interface(&self, intf_uuid: Uuid) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await
        {
            Err(err) => Err(err),
            Ok(i) => match i.net_ns {
                Some(_) => Err(FError::Unimplemented),
                None => match i.kind {
                    VirtualInterfaceKind::MACVLAN(_) => {
                        self.del_iface(i.if_name.clone()).await?;
                        self.connector
                            .global
                            .remove_node_interface(node_uuid, intf_uuid)
                            .await?;
                        Ok(i)
                    }
                    _ => Err(FError::WrongKind),
                },
            },
        }
    }

    async fn move_interface_info_namespace(
        &self,
        intf_uuid: Uuid,
        ns_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;

        match iface.net_ns {
            Some(_) => Err(FError::Unimplemented),
            None => {
                let mut netns = self
                    .connector
                    .global
                    .get_node_network_namespace(node_uuid, ns_uuid)
                    .await?;

                self.set_iface_ns(iface.if_name.clone(), netns.ns_name.clone())
                    .await?;

                iface.net_ns = Some(netns.uuid);
                netns.interfaces.push(iface.uuid);

                self.connector
                    .global
                    .add_node_interface(node_uuid, &iface)
                    .await?;
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
                Ok(iface)
            }
        }
    }

    async fn move_interface_into_default_namespace(
        &self,
        intf_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        Err(FError::Unimplemented)
        // match iface.net_ns {
        //     Some(netns_uuid) => {
        //         iface.net_ns = None;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &iface)
        //             .await?;
        //         let mut netns = self
        //             .connector
        //             .global
        //             .get_node_network_namespace(node_uuid, netns_uuid)
        //             .await?;
        //         match netns.interfaces.iter().position(|&x| x == iface.uuid) {
        //             Some(p) => {
        //                 netns.interfaces.remove(p);
        //                 self.connector
        //                     .global
        //                     .add_node_network_namespace(node_uuid, &netns)
        //                     .await?;
        //                 Ok(iface)
        //             }
        //             None => Err(FError::NotConnected),
        //         }
        //     }
        //     None => Ok(iface),
        // }
    }

    async fn rename_virtual_interface(
        &self,
        intf_uuid: Uuid,
        intf_name: String,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        match iface.net_ns {
            Some(_) => Err(FError::Unimplemented),
            None => {
                self.set_iface_name(iface.if_name.clone(), intf_name.clone())
                    .await?;
                iface.if_name = intf_name;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &iface)
                    .await?;
                Ok(iface)
            }
        }
    }

    async fn attach_interface_to_bridge(
        &self,
        intf_uuid: Uuid,
        br_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        let bridge = self
            .connector
            .global
            .get_node_interface(node_uuid, br_uuid)
            .await?;
        match bridge.kind {
            VirtualInterfaceKind::BRIDGE(mut info) => match (iface.net_ns, bridge.net_ns) {
                (Some(_), Some(_)) => Err(FError::Unimplemented),
                (Some(_), None) | (None, Some(_)) => Err(FError::NetworkingError(String::from(
                    "Interface in different namespaces",
                ))),
                (None, None) => {
                    self.set_iface_master(iface.if_name.clone(), bridge.if_name.clone())
                        .await?;

                    iface.parent = Some(bridge.uuid);
                    info.childs.push(iface.uuid);
                    let mut new_bridge = self
                        .connector
                        .global
                        .get_node_interface(node_uuid, br_uuid)
                        .await?;
                    new_bridge.kind = VirtualInterfaceKind::BRIDGE(info);
                    self.connector
                        .global
                        .add_node_interface(node_uuid, &iface)
                        .await?;
                    self.connector
                        .global
                        .add_node_interface(node_uuid, &new_bridge)
                        .await?;
                    Ok(iface)
                }
            },
            _ => Err(FError::WrongKind),
        }
    }

    async fn detach_interface_from_bridge(
        &self,
        intf_uuid: Uuid,
        br_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        let bridge = self
            .connector
            .global
            .get_node_interface(node_uuid, br_uuid)
            .await?;
        Err(FError::Unimplemented)
        // match bridge.kind {
        //     VirtualInterfaceKind::BRIDGE(mut info) => match iface.parent {
        //         Some(br) => {
        //             if br == bridge.uuid {
        //                 iface.parent = None;
        //                 self.connector
        //                     .global
        //                     .add_node_interface(node_uuid, &iface)
        //                     .await?;
        //                 match info.childs.iter().position(|&x| x == iface.uuid) {
        //                     Some(p) => {
        //                         info.childs.remove(p);
        //                         let mut new_bridge = self
        //                             .connector
        //                             .global
        //                             .get_node_interface(node_uuid, br_uuid)
        //                             .await?;
        //                         new_bridge.kind = VirtualInterfaceKind::BRIDGE(info);
        //                         self.connector
        //                             .global
        //                             .add_node_interface(node_uuid, &new_bridge)
        //                             .await?;
        //                         return Ok(iface);
        //                     }
        //                     None => return Err(FError::NotConnected),
        //                 }
        //             }
        //             Err(FError::NotConnected)
        //         }
        //         None => Err(FError::NotConnected),
        //     },
        //     _ => Err(FError::WrongKind),
        // }
    }

    async fn create_virtual_interface_in_namespace(
        &self,
        intf: VirtualInterfaceConfig,
        ns_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut netns = self
            .connector
            .global
            .get_node_network_namespace(node_uuid, ns_uuid)
            .await?;
        Err(FError::Unimplemented)
        // match intf.kind {
        //     VirtualInterfaceConfigKind::VXLAN(conf) => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::VXLAN(VXLANKind {
        //                 vni: conf.vni,
        //                 mcast_addr: conf.mcast_addr,
        //                 port: conf.port,
        //                 dev: self.get_dummy_face(),
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::BRIDGE => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::BRIDGE(BridgeKind { childs: Vec::new() }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::VETH => {
        //         let external_face_name = self.generate_random_interface_name();
        //         let internal_iface_uuid = Uuid::new_v4();
        //         let external_iface_uuid = Uuid::new_v4();
        //         let v_iface_internal = VirtualInterface {
        //             uuid: internal_iface_uuid,
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::VETH(VETHKind {
        //                 pair: external_iface_uuid,
        //                 internal: true,
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         let v_iface_external = VirtualInterface {
        //             uuid: external_iface_uuid,
        //             if_name: external_face_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::VETH(VETHKind {
        //                 pair: internal_iface_uuid,
        //                 internal: false,
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };

        //         netns.interfaces.push(internal_iface_uuid);
        //         netns.interfaces.push(external_iface_uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface_internal)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface_external)
        //             .await?;
        //         Ok(v_iface_internal)
        //     }
        //     VirtualInterfaceConfigKind::VLAN(conf) => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::VLAN(VLANKind {
        //                 tag: conf.tag,
        //                 dev: self.get_dummy_face(),
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::MACVLAN => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::MACVLAN(MACVLANKind {
        //                 dev: self.get_dummy_face(),
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::GRE(conf) => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::GRE(GREKind {
        //                 local_addr: conf.local_addr,
        //                 remote_addr: conf.remote_addr,
        //                 ttl: conf.ttl,
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::GRETAP(conf) => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::GRETAP(GREKind {
        //                 local_addr: conf.local_addr,
        //                 remote_addr: conf.remote_addr,
        //                 ttl: conf.ttl,
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::IP6GRE(conf) => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::IP6GRE(GREKind {
        //                 local_addr: conf.local_addr,
        //                 remote_addr: conf.remote_addr,
        //                 ttl: conf.ttl,
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        //     VirtualInterfaceConfigKind::IP6GRETAP(conf) => {
        //         let v_iface = VirtualInterface {
        //             uuid: Uuid::new_v4(),
        //             if_name: intf.if_name,
        //             net_ns: Some(netns.uuid),
        //             parent: None,
        //             kind: VirtualInterfaceKind::IP6GRETAP(GREKind {
        //                 local_addr: conf.local_addr,
        //                 remote_addr: conf.remote_addr,
        //                 ttl: conf.ttl,
        //             }),
        //             addresses: Vec::new(),
        //             phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
        //         };
        //         netns.interfaces.push(v_iface.uuid);
        //         self.connector
        //             .global
        //             .add_node_network_namespace(node_uuid, &netns)
        //             .await?;
        //         self.connector
        //             .global
        //             .add_node_interface(node_uuid, &v_iface)
        //             .await?;
        //         Ok(v_iface)
        //     }
        // }
    }

    async fn delete_virtual_interface_in_namespace(
        &self,
        intf_uuid: Uuid,
        ns_uuid: Uuid,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut netns = self
            .connector
            .global
            .get_node_network_namespace(node_uuid, ns_uuid)
            .await?;
        let iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        Err(FError::Unimplemented)
        // match iface.net_ns {
        //     None => Err(FError::NotConnected),
        //     Some(nid) => {
        //         if nid == netns.uuid {
        //             match netns.interfaces.iter().position(|&x| x == iface.uuid) {
        //                 Some(p) => {
        //                     netns.interfaces.remove(p);
        //                     if let VirtualInterfaceKind::VETH(ref info) = iface.kind {
        //                         self.connector
        //                             .global
        //                             .remove_node_interface(node_uuid, info.pair)
        //                             .await?;
        //                     }
        //                     self.connector
        //                         .global
        //                         .add_node_network_namespace(node_uuid, &netns)
        //                         .await?;
        //                     self.connector
        //                         .global
        //                         .remove_node_interface(node_uuid, intf_uuid)
        //                         .await?;
        //                     return Ok(iface);
        //                 }
        //                 None => return Err(FError::NotConnected),
        //             }
        //         }
        //         Err(FError::NotConnected)
        //     }
        // }
    }

    async fn assing_address_to_interface(
        &self,
        intf_uuid: Uuid,
        address: IPAddress,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        match iface.net_ns {
            Some(_) => Err(FError::Unimplemented),
            None => {
                // TODO we should move to ipnetwork instead of IPAddress to have
                // visibility of the prefix, leaving 24 for the time being.address
                self.add_iface_address(iface.if_name.clone(), address, 24)
                    .await?;
                iface.addresses.push(address);
                self.connector
                    .global
                    .add_node_interface(node_uuid, &iface)
                    .await?;
                Ok(iface)
            }
        }
    }

    async fn remove_address_from_interface(
        &self,
        intf_uuid: Uuid,
        address: IPAddress,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;
        match iface.net_ns {
            Some(_) => Err(FError::Unimplemented),
            None => match iface.addresses.iter().position(|&x| x == address) {
                Some(p) => {
                    self.del_iface_address(iface.if_name.clone(), address)
                        .await?;
                    iface.addresses.remove(p);
                    self.connector
                        .global
                        .add_node_interface(node_uuid, &iface)
                        .await?;
                    Ok(iface)
                }
                None => Err(FError::NotConnected),
            },
        }
    }

    async fn set_macaddres_of_interface(
        &self,
        intf_uuid: Uuid,
        address: MACAddress,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let mut iface = self
            .connector
            .global
            .get_node_interface(node_uuid, intf_uuid)
            .await?;

        let vec_addr = vec![
            address.0, address.1, address.2, address.3, address.4, address.5,
        ];
        match iface.net_ns {
            Some(_) => Err(FError::Unimplemented),
            None => {
                self.set_iface_mac(iface.if_name.clone(), vec_addr).await?;
                iface.phy_address = address;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &iface)
                    .await?;
                Ok(iface)
            }
        }
    }
}

impl LinuxNetwork {
    pub fn new(
        z: Arc<zenoh::Zenoh>,
        connector: Arc<fog05_sdk::zconnector::ZConnector>,
        pid: u32,
    ) -> FResult<Self> {
        let state = LinuxNetworkState {
            uuid: None,
            tokio_rt: tokio::runtime::Runtime::new()?,
        };

        Ok(Self {
            z,
            connector,
            pid,
            agent: None,
            os: None,
            state: Arc::new(RwLock::new(state)),
        })
    }

    async fn run(&self, stop: async_std::sync::Receiver<()>) -> FResult<()> {
        info!("LinuxNetwork main loop starting...");

        //starting the Agent-Plugin Server
        let hv_server = self
            .clone()
            .get_networking_plugin_server(self.z.clone(), None);
        hv_server.connect().await?;
        hv_server.initialize().await?;

        let mut guard = self.state.write().await;
        guard.uuid = Some(hv_server.instance_uuid());
        drop(guard);

        self.agent
            .clone()
            .unwrap()
            .register_plugin(hv_server.instance_uuid(), PluginKind::NETWORKING)
            .await??;

        hv_server.register().await?;

        let (shv, _hhv) = hv_server.start().await?;

        let monitoring = async {
            loop {
                info!("Monitoring loop started");
                task::sleep(Duration::from_secs(60)).await;
            }
        };

        match monitoring.race(stop.recv()).await {
            Ok(_) => trace!("Monitoring ending correct"),
            Err(e) => trace!("Monitoring ending got error: {}", e),
        }

        self.agent
            .clone()
            .unwrap()
            .unregister_plugin(hv_server.instance_uuid())
            .await??;

        hv_server.stop(shv).await?;
        hv_server.unregister().await?;
        hv_server.disconnect().await?;

        info!("LinuxNetwork main loop exiting");
        Ok(())
    }

    pub async fn start(
        &mut self,
    ) -> (
        async_std::sync::Sender<()>,
        async_std::task::JoinHandle<FResult<()>>,
    ) {
        let local_os = OSClient::find_local_servers(self.z.clone()).await.unwrap();
        if local_os.is_empty() {
            error!("Unable to find a local OS interface");
            panic!("No OS Server");
        }

        let local_agent = AgentPluginInterfaceClient::find_local_servers(self.z.clone())
            .await
            .unwrap();
        if local_agent.is_empty() {
            error!("Unable to find a local Agent interface");
            panic!("No Agent Server");
        }

        let os = OSClient::new(self.z.clone(), local_os[0]);
        let agent = AgentPluginInterfaceClient::new(self.z.clone(), local_agent[0]);

        self.agent = Some(agent);
        self.os = Some(os);

        // Starting main loop in a task
        let (s, r) = async_std::sync::channel::<()>(1);
        let plugin = self.clone();
        let h = async_std::task::spawn_blocking(move || {
            async_std::task::block_on(async { plugin.run(r).await })
        });
        (s, h)
    }

    pub async fn stop(&self, stop: async_std::sync::Sender<()>) -> FResult<()> {
        stop.send(()).await;

        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let default_vnet = self
            .connector
            .global
            .get_node_virtual_network(node_uuid, Uuid::nil())
            .await?;

        for iface_uuid in default_vnet.interfaces {
            let iface = self
                .connector
                .global
                .get_node_interface(node_uuid, iface_uuid)
                .await?;
            self.del_iface(iface.if_name.clone()).await?;
            self.connector
                .global
                .remove_node_interface(node_uuid, iface_uuid)
                .await?;
        }
        self.connector
            .global
            .remove_node_virtual_network(node_uuid, Uuid::nil())
            .await?;

        Ok(())
    }

    fn get_overlay_face_from_config(&self) -> Interface {
        Interface {
            if_name: String::from("eno0"),
            kind: InterfaceKind::ETHERNET,
            addresses: Vec::new(),
            phy_address: None,
        }
    }

    fn get_dummy_face(&self) -> Interface {
        Interface {
            if_name: String::from("dummy"),
            kind: InterfaceKind::ETHERNET,
            addresses: Vec::new(),
            phy_address: None,
        }
    }

    fn generate_random_interface_name(&self) -> String {
        let iface: String = thread_rng().sample_iter(&Alphanumeric).take(8).collect();
        iface
    }

    fn generate_random_netns_name(&self) -> String {
        let ns: String = thread_rng().sample_iter(&Alphanumeric).take(8).collect();
        format!("ns-{}", ns)
    }

    async fn add_netns(&self, ns_name: String) -> FResult<()> {
        log::trace!("add_netns {}", ns_name);
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                NetlinkNetworkNamespace::add(ns_name).await
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn del_netns(&self, ns_name: String) -> FResult<()> {
        log::trace!("del_netns {}", ns_name);
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                NetlinkNetworkNamespace::del(ns_name).await
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn create_bridge(&self, br_name: String) -> FResult<()> {
        log::trace!("create_bridge {}", br_name);
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                handle.link().add().bridge(br_name).execute().await
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn create_veth(&self, iface_i: String, iface_e: String) -> FResult<()> {
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                handle.link().add().veth(iface_i, iface_e).execute().await
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn create_vlan(&self, iface: String, dev: String, tag: u16) -> FResult<()> {
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                let mut links = handle.link().get().set_name_filter(dev).execute();
                if let Some(link) = links
                    .try_next()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))?
                {
                    handle
                        .link()
                        .add()
                        .vlan(iface, link.header.index, tag)
                        .execute()
                        .await
                        .map_err(|e| FError::NetworkingError(format!("{}", e)))
                } else {
                    Err(FError::NotFound)
                }
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn create_mcast_vxlan(
        &self,
        iface: String,
        dev: String,
        vni: u32,
        mcast_addr: IPAddress,
        port: u16,
    ) -> FResult<()> {
        log::trace!(
            "create_mcast_vxlan {} {} {} {} {}",
            iface,
            dev,
            vni,
            mcast_addr,
            port
        );
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                let mut links = handle.link().get().set_name_filter(dev).execute();
                if let Some(link) = links
                    .try_next()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))?
                {
                    let vxlan = handle
                        .link()
                        .add()
                        .vxlan(iface, vni)
                        .link(link.header.index);

                    let vxlan = match mcast_addr {
                        IPAddress::V4(v4) => vxlan.group(v4),
                        IPAddress::V6(v6) => vxlan.group6(v6),
                    };

                    vxlan
                        .port(port)
                        .execute()
                        .await
                        .map_err(|e| FError::NetworkingError(format!("{}", e)))
                } else {
                    Err(FError::NotFound)
                }
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn create_ptp_vxlan(
        &self,
        iface: String,
        dev: String,
        vni: u32,
        local_addr: IPAddress,
        remote_addr: IPAddress,
        port: u16,
    ) -> FResult<()> {
        log::trace!(
            "create_ptp_vxlan {} {} {} {} {} {}",
            iface,
            dev,
            vni,
            local_addr,
            remote_addr,
            port
        );
        let mut state = self.state.write().await;
        state
            .tokio_rt
            .block_on(async {
                let (connection, handle, _) = new_connection().unwrap();
                tokio::spawn(connection);
                let mut links = handle.link().get().set_name_filter(dev).execute();
                if let Some(link) = links
                    .try_next()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))?
                {
                    let vxlan = handle
                        .link()
                        .add()
                        .vxlan(iface, vni)
                        .link(link.header.index);

                    let vxlan = match local_addr {
                        IPAddress::V4(v4) => vxlan.local(v4),
                        IPAddress::V6(v6) => vxlan.local6(v6),
                    };

                    let vxlan = match remote_addr {
                        IPAddress::V4(v4) => vxlan.remote(v4),
                        IPAddress::V6(v6) => vxlan.remote6(v6),
                    };

                    vxlan
                        .port(port)
                        .execute()
                        .await
                        .map_err(|e| FError::NetworkingError(format!("{}", e)))
                } else {
                    Err(FError::NotFound)
                }
            })
            .map_err(|e| FError::NetworkingError(format!("{}", e)))
    }

    async fn del_iface(&self, iface: String) -> FResult<()> {
        log::trace!("del_iface {}", iface);
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .del(link.header.index)
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_master(&self, iface: String, master: String) -> FResult<()> {
        log::trace!("set_iface_master {} {}", iface, master);
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                let mut masters = handle.link().get().set_name_filter(master).execute();
                if let Some(master) = masters
                    .try_next()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))?
                {
                    handle
                        .link()
                        .set(link.header.index)
                        .master(master.header.index)
                        .execute()
                        .await
                        .map_err(|e| FError::NetworkingError(format!("{}", e)))
                } else {
                    log::error!("set_iface_master master not found");
                    Err(FError::NotFound)
                }
            } else {
                log::error!("set_iface_master iface not found");
                Err(FError::NotFound)
            }
        })
    }

    async fn add_iface_address(&self, iface: String, addr: IPAddress, prefix: u8) -> FResult<()> {
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .address()
                    .add(link.header.index, addr, prefix)
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn del_iface_address(&self, iface: String, addr: IPAddress) -> FResult<()> {
        let mut state = self.state.write().await;
        use netlink_packet_route::rtnl::address::nlas::Nla;
        use netlink_packet_route::rtnl::address::AddressMessage;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);

            let octets = match addr {
                IPAddress::V4(a) => a.octets().to_vec(),
                IPAddress::V6(a) => a.octets().to_vec(),
            };
            let mut nl_addresses = Vec::new();
            let mut links = handle.link().get().set_name_filter(iface.clone()).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                let mut addresses = handle
                    .address()
                    .get()
                    .set_link_index_filter(link.header.index)
                    .execute();
                while let Some(msg) = addresses
                    .try_next()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))?
                {
                    for nla in &msg.nlas {
                        match nla {
                            Nla::Address(nl_addr) => {
                                nl_addresses.push((msg.header.clone(), nl_addr.clone()))
                            }
                            _ => continue,
                        }
                    }
                }
                match nl_addresses.into_iter().find(|(_, x)| *x == octets) {
                    Some((hdr, addr)) => {
                        let msg = AddressMessage {
                            header: hdr,
                            nlas: vec![Nla::Address(addr)],
                        };
                        handle
                            .address()
                            .del(msg)
                            .execute()
                            .await
                            .map_err(|e| FError::NetworkingError(format!("{}", e)))?;
                        Ok(())
                    }
                    None => Err(FError::NotFound),
                }
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_name(&self, iface: String, new_name: String) -> FResult<()> {
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .set(link.header.index)
                    .name(new_name)
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_mac(&self, iface: String, address: Vec<u8>) -> FResult<()> {
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .set(link.header.index)
                    .address(address)
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_ns(&self, iface: String, netns: String) -> FResult<()> {
        let mut state = self.state.write().await;
        let nsfile = std::fs::File::open(netns)?;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .set(link.header.index)
                    .setns_by_fd(nsfile.into_raw_fd())
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_default_ns(&self, iface: String) -> FResult<()> {
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .set(link.header.index)
                    .setns_by_pid(0)
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_up(&self, iface: String) -> FResult<()> {
        log::trace!("set_iface_up {}", iface);
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .set(link.header.index)
                    .up()
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn set_iface_down(&self, iface: String) -> FResult<()> {
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                handle
                    .link()
                    .set(link.header.index)
                    .down()
                    .execute()
                    .await
                    .map_err(|e| FError::NetworkingError(format!("{}", e)))
            } else {
                Err(FError::NotFound)
            }
        })
    }

    async fn iface_exists(&self, iface: String) -> FResult<bool> {
        log::trace!("iface_exists {}", iface);
        let mut state = self.state.write().await;
        state.tokio_rt.block_on(async {
            let (connection, handle, _) = new_connection().unwrap();
            tokio::spawn(connection);
            let mut links = handle.link().get().set_name_filter(iface).execute();
            if let Some(link) = links
                .try_next()
                .await
                .map_err(|e| FError::NetworkingError(format!("{}", e)))?
            {
                Ok(true)
            } else {
                Ok(false)
            }
        })
    }
}
