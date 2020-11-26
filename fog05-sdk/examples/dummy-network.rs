use std::process;
use std::time::Duration;

use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};
use async_std::task;

use log::{error, info, trace};

use zenoh::*;

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
use fog05_sdk::zconnector::ZConnector;

use async_ctrlc::CtrlC;
use uuid::Uuid;

use rand::distributions::Alphanumeric;
use rand::{thread_rng, Rng};

use structopt::StructOpt;

#[derive(StructOpt, Debug)]
struct DummyArgs {
    /// Config file
    #[structopt(short, long, default_value = "tcp/127.0.0.1:7447")]
    zenoh: String,
}

#[derive(Clone)]
pub struct DummyNetwork {
    pub z: Arc<zenoh::Zenoh>,
    pub connector: Arc<fog05_sdk::zconnector::ZConnector>,
    pub pid: u32,
    pub agent: Option<AgentPluginInterfaceClient>,
    pub os: Option<OSClient>,
    pub uuid: Arc<RwLock<Option<Uuid>>>,
}

#[zserver]
impl NetworkingPlugin for DummyNetwork {
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
        let default_net_uuid = Uuid::nil();
        let mut default_vnet = VirtualNetwork {
            uuid: default_net_uuid,
            id: String::from("fos-default"),
            name: Some(String::from("Eclipse fog05 default virtual network")),
            is_mgmt: false,
            link_kind: LinkKind::L2(MCastVXLANInfo {
                vni: 3845,
                mcast_addr: IPAddress::V4(std::net::Ipv4Addr::new(239, 15, 5, 0)),
                port: 3845,
            }),
            ip_version: IPVersion::IPV4,
            ip_configuration: None,
            connection_points: Vec::new(),
            interfaces: Vec::new(),
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
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        self.connector
            .global
            .add_node_virutal_network(node_uuid, &default_vnet)
            .await?;
        Ok(default_vnet)
    }

    async fn create_virtual_network(&self, vnet_uuid: Uuid) -> FResult<VirtualNetwork> {
        // this function is never called directly from API/Orchestrator
        match self.connector.global.get_virtual_network(vnet_uuid).await {
            Ok(vnet) => {
                let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
                self.connector
                    .global
                    .add_node_virutal_network(node_uuid, &vnet)
                    .await?;
                Ok(vnet)
            }
            Err(FError::NotFound) => {
                // a virtual network with this UUID does not exists
                Err(FError::NotFound)
            }
            Err(err) => {
                //any other error just return the error
                Err(err)
            }
        }
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
                self.connector
                    .global
                    .remove_node_virtual_network(node_uuid, vnet_uuid)
                    .await?;
                Ok(vnet)
            }
        }
    }

    async fn create_connection_point(&self) -> FResult<ConnectionPoint> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let cp_uuid = Uuid::new_v4();
        match self
            .connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await
        {
            Err(_) => {
                let cp = ConnectionPoint {
                    uuid: cp_uuid,
                    net_ns: Uuid::new_v4(),
                    bridge: Uuid::new_v4(),
                    internal_veth: Uuid::new_v4(),
                    external_veth: Uuid::new_v4(),
                };
                self.connector
                    .global
                    .add_node_connection_point(node_uuid, &cp)
                    .await?;
                Ok(cp)
            }
            Ok(_) => Err(FError::AlreadyPresent),
        }
    }

    async fn get_connection_point(&self, cp_uuid: Uuid) -> FResult<ConnectionPoint> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        self.connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await
    }

    async fn delete_connection_point(&self, cp_uuid: Uuid) -> FResult<Uuid> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match self
            .connector
            .global
            .get_node_connection_point(node_uuid, cp_uuid)
            .await
        {
            Err(_) => Err(FError::NotFound),
            Ok(_) => {
                self.connector
                    .global
                    .remove_node_connection_point(node_uuid, cp_uuid)
                    .await?;
                Ok(cp_uuid)
            }
        }
    }

    async fn create_virtual_interface(
        &self,
        intf: VirtualInterfaceConfig,
    ) -> FResult<VirtualInterface> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        match intf.kind {
            VirtualInterfaceConfigKind::VXLAN(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VXLAN(VXLANKind {
                        vni: conf.vni,
                        mcast_addr: conf.mcast_addr,
                        port: conf.port,
                        dev: self.get_dummy_face(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::BRIDGE => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::BRIDGE(BridgeKind { childs: Vec::new() }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
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
                    if_name: intf.if_name,
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
                    if_name: external_face_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VETH(VETHKind {
                        pair: internal_iface_uuid,
                        internal: false,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };

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
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: None,
                    parent: None,
                    kind: VirtualInterfaceKind::VLAN(VLANKind {
                        tag: conf.tag,
                        dev: self.get_dummy_face(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
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
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
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
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
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
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
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
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
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
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
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
            Ok(intf) => {
                if let VirtualInterfaceKind::VETH(ref info) = intf.kind {
                    self.connector
                        .global
                        .remove_node_interface(node_uuid, info.pair)
                        .await?;
                }
                self.connector
                    .global
                    .remove_node_interface(node_uuid, intf_uuid)
                    .await?;
                Ok(intf)
            }
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
            Ok(i) => match i.kind {
                VirtualInterfaceKind::BRIDGE(_) => {
                    self.connector
                        .global
                        .remove_node_interface(node_uuid, br_uuid)
                        .await?;
                    Ok(i)
                }
                _ => Err(FError::WrongKind),
            },
        }
    }

    async fn create_network_namespace(&self) -> FResult<NetworkNamespace> {
        let node_uuid = self.agent.as_ref().unwrap().get_node_uuid().await??;
        let netns = NetworkNamespace {
            uuid: Uuid::new_v4(),
            ns_name: self.generate_random_netns_name(),
            interfaces: Vec::new(),
        };
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
        iface.net_ns = Some(cp.net_ns);
        self.connector
            .global
            .add_node_interface(node_uuid, &iface)
            .await?;
        Ok(iface)
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
        match iface.net_ns {
            Some(ns) => {
                if ns == cp.net_ns {
                    iface.net_ns = None;
                    self.connector
                        .global
                        .add_node_interface(node_uuid, &iface)
                        .await?;
                    return Ok(iface);
                }
                Err(FError::NotConnected)
            }
            None => Err(FError::NotConnected),
        }
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
        vnet.connection_points.push(cp.uuid);
        self.connector
            .global
            .add_node_virutal_network(node_uuid, &vnet)
            .await?;
        Ok(cp)
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
        match vnet.connection_points.iter().position(|&x| x == cp.uuid) {
            Some(p) => {
                vnet.connection_points.remove(p);
                self.connector
                    .global
                    .add_node_virutal_network(node_uuid, &vnet)
                    .await?;
                Ok(cp)
            }
            None => Err(FError::NotConnected),
        }
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
        Ok(self.get_dummy_face().if_name)
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
        self.connector
            .global
            .add_node_interface(node_uuid, &v_iface)
            .await?;
        Ok(v_iface)
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
            Ok(i) => match i.kind {
                VirtualInterfaceKind::MACVLAN(_) => {
                    self.connector
                        .global
                        .remove_node_interface(node_uuid, intf_uuid)
                        .await?;
                    Ok(i)
                }
                _ => Err(FError::WrongKind),
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
        let mut netns = self
            .connector
            .global
            .get_node_network_namespace(node_uuid, ns_uuid)
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
        match iface.net_ns {
            Some(netns_uuid) => {
                iface.net_ns = None;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &iface)
                    .await?;
                let mut netns = self
                    .connector
                    .global
                    .get_node_network_namespace(node_uuid, netns_uuid)
                    .await?;
                match netns.interfaces.iter().position(|&x| x == iface.uuid) {
                    Some(p) => {
                        netns.interfaces.remove(p);
                        self.connector
                            .global
                            .add_node_network_namespace(node_uuid, &netns)
                            .await?;
                        Ok(iface)
                    }
                    None => Err(FError::NotConnected),
                }
            }
            None => Ok(iface),
        }
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
        iface.if_name = intf_name;
        self.connector
            .global
            .add_node_interface(node_uuid, &iface)
            .await?;
        Ok(iface)
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
            VirtualInterfaceKind::BRIDGE(mut info) => {
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
        match bridge.kind {
            VirtualInterfaceKind::BRIDGE(mut info) => match iface.parent {
                Some(br) => {
                    if br == bridge.uuid {
                        iface.parent = None;
                        self.connector
                            .global
                            .add_node_interface(node_uuid, &iface)
                            .await?;
                        match info.childs.iter().position(|&x| x == iface.uuid) {
                            Some(p) => {
                                info.childs.remove(p);
                                let mut new_bridge = self
                                    .connector
                                    .global
                                    .get_node_interface(node_uuid, br_uuid)
                                    .await?;
                                new_bridge.kind = VirtualInterfaceKind::BRIDGE(info);
                                self.connector
                                    .global
                                    .add_node_interface(node_uuid, &new_bridge)
                                    .await?;
                                return Ok(iface);
                            }
                            None => return Err(FError::NotConnected),
                        }
                    }
                    Err(FError::NotConnected)
                }
                None => Err(FError::NotConnected),
            },
            _ => Err(FError::WrongKind),
        }
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
        match intf.kind {
            VirtualInterfaceConfigKind::VXLAN(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::VXLAN(VXLANKind {
                        vni: conf.vni,
                        mcast_addr: conf.mcast_addr,
                        port: conf.port,
                        dev: self.get_dummy_face(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
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
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::BRIDGE(BridgeKind { childs: Vec::new() }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
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
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
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
                    if_name: external_face_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::VETH(VETHKind {
                        pair: internal_iface_uuid,
                        internal: false,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };

                netns.interfaces.push(internal_iface_uuid);
                netns.interfaces.push(external_iface_uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
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
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::VLAN(VLANKind {
                        tag: conf.tag,
                        dev: self.get_dummy_face(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
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
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::MACVLAN(MACVLANKind {
                        dev: self.get_dummy_face(),
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::GRE(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::GRE(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::GRETAP(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::GRETAP(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::IP6GRE(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::IP6GRE(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
            VirtualInterfaceConfigKind::IP6GRETAP(conf) => {
                let v_iface = VirtualInterface {
                    uuid: Uuid::new_v4(),
                    if_name: intf.if_name,
                    net_ns: Some(netns.uuid),
                    parent: None,
                    kind: VirtualInterfaceKind::IP6GRETAP(GREKind {
                        local_addr: conf.local_addr,
                        remote_addr: conf.remote_addr,
                        ttl: conf.ttl,
                    }),
                    addresses: Vec::new(),
                    phy_address: MACAddress::new(0, 0, 0, 0, 0, 0),
                };
                netns.interfaces.push(v_iface.uuid);
                self.connector
                    .global
                    .add_node_network_namespace(node_uuid, &netns)
                    .await?;
                self.connector
                    .global
                    .add_node_interface(node_uuid, &v_iface)
                    .await?;
                Ok(v_iface)
            }
        }
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
        match iface.net_ns {
            None => Err(FError::NotConnected),
            Some(nid) => {
                if nid == netns.uuid {
                    match netns.interfaces.iter().position(|&x| x == iface.uuid) {
                        Some(p) => {
                            netns.interfaces.remove(p);
                            if let VirtualInterfaceKind::VETH(ref info) = iface.kind {
                                self.connector
                                    .global
                                    .remove_node_interface(node_uuid, info.pair)
                                    .await?;
                            }
                            self.connector
                                .global
                                .add_node_network_namespace(node_uuid, &netns)
                                .await?;
                            self.connector
                                .global
                                .remove_node_interface(node_uuid, intf_uuid)
                                .await?;
                            return Ok(iface);
                        }
                        None => return Err(FError::NotConnected),
                    }
                }
                Err(FError::NotConnected)
            }
        }
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
        iface.addresses.push(address);
        self.connector
            .global
            .add_node_interface(node_uuid, &iface)
            .await?;
        Ok(iface)
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
        match iface.addresses.iter().position(|&x| x == address) {
            Some(p) => {
                iface.addresses.remove(p);
                self.connector
                    .global
                    .add_node_interface(node_uuid, &iface)
                    .await?;
                Ok(iface)
            }
            None => Err(FError::NotConnected),
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
        iface.phy_address = address;
        self.connector
            .global
            .add_node_interface(node_uuid, &iface)
            .await?;
        Ok(iface)
    }
}

impl DummyNetwork {
    async fn run(&self, stop: async_std::sync::Receiver<()>) {
        info!("DummyNetwork main loop starting...");

        //starting the Agent-Plugin Server
        let hv_server = self
            .clone()
            .get_networking_plugin_server(self.z.clone(), None);
        hv_server.connect().await;
        hv_server.initialize().await;

        let mut guard = self.uuid.write().await;
        *guard = Some(hv_server.instance_uuid());
        drop(guard);

        self.agent
            .clone()
            .unwrap()
            .register_plugin(self.uuid.read().await.unwrap(), PluginKind::NETWORKING)
            .await
            .unwrap()
            .unwrap();

        hv_server.register().await;

        let (shv, _hhv) = hv_server.start().await;

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
            .unregister_plugin(self.uuid.read().await.unwrap())
            .await
            .unwrap()
            .unwrap();

        hv_server.stop(shv).await;
        hv_server.unregister().await;
        hv_server.disconnect().await;

        info!("DummyNetwork main loop exiting")
    }

    pub async fn start(
        &mut self,
    ) -> (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>) {
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
            async_std::task::block_on(async {
                plugin.run(r).await;
            })
        });
        (s, h)
    }

    pub async fn stop(&self, stop: async_std::sync::Sender<()>) {
        stop.send(()).await;
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
}

#[async_std::main]
async fn main() {
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );

    let args = DummyArgs::from_args();
    info!("Dummy Network Plugin -- bootstrap");
    let my_pid = process::id();
    info!("PID is {}", my_pid);

    let properties = format!("mode=client;peer={}", args.zenoh.clone());
    let zproperties = Properties::from(properties);
    let zenoh = Arc::new(Zenoh::new(zproperties.into()).await.unwrap());
    let zconnector = Arc::new(ZConnector::new(zenoh.clone(), None, None));

    let mut dummy = DummyNetwork {
        uuid: Arc::new(RwLock::new(None)),
        z: zenoh.clone(),
        connector: zconnector.clone(),
        pid: my_pid,
        agent: None,
        os: None,
    };

    let (s, h) = dummy.start().await;

    //Creating the Ctrl-C handler and racing with agent.run
    let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
    let mut stream = ctrlc.enumerate().take(1);

    stream.next().await;
    trace!("Received Ctrl-C start teardown");

    //Here we send the stop signal to the agent object and waits that it ends
    dummy.stop(s).await;

    //wait for the futures to ends
    h.await;

    //zconnector.close();
    //zenoh.close();

    info!("Bye!")
}
