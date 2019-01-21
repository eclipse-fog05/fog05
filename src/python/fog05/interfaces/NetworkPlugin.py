# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors: Gabriele Baldoni, ADLINK Technology Inc.
# Initial implementation and API

from fog05.interfaces.Plugin import Plugin


class NetworkPlugin(Plugin):
    '''
    Class: NetworkPlugin

    This class is an interface for plugins that control the network resouces,
    and provide an abstraction layer
    for networking managment functions
    '''

    def __init__(self, version, plugin_uuid):
        super(NetworkPlugin, self).__init__(version, plugin_uuid)

    def create_virtual_interface(self, name, uuid):
        '''
        This should create a virtual network interface

        :name: String
        :return: tuple (interface_name,interface_uuid) or
        None in case of failure

        '''
        raise NotImplementedError('This is and interface!')

    def create_virtual_bridge(self, name, uuid):
        '''
        This should create a virtual bridge

        :name: String
        :return: tuple (bridge_name,bridge_uuid) or None in case of failure
        '''
        raise NotImplementedError('This is and interface!')

    def allocate_bandwidth(self, intf_uuid, bandwidth):
        '''
        This should allocate bandwidth to a certaint virtual interface,
        if the interface not exists throw an exception

        :intf_uuid: String
        :bandwidth: tuple (up,down)
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def create_virtual_network(self, network_name, uuid, ip_range, has_dhcp,
                               gateway, manifest):
        '''
        This should create a virtual network, with given caratteristics

        range should specified as CIRD subnet
        eg. 192.168.0.0/24 which means from 192.168.0.1 to 192.168.0.254
        if gateway address is none the entities connected to that network
         cannot reach internet
        if dhcp is true the easiest way to have a dhcp server is using dnsmasq
        eg. sudo dnsmasq -d  --interface=<bridge_associated_to_this_network>
                 --bind-interfaces  --dhcp-range=<start_ip>,<end_ip>
        using -d you can parse dnsmasq output to listen to events like dhcp ack

        :network_name: String
        :ip_range: String
        :has_dhcp: bool
        :gateway: String
        :return: tuple (net_name,net_uuid) or None in case of failure


        #TODO on fog05 -> support dhcp as used on OSM

        '''

        raise NotImplementedError('This is and interface!')

    def assign_interface_to_network(self, network_uuid, intf_uuid):
        '''
        This should assign the interface identified by intf_uuid to the network
         identified by network_uuid,
        if the interface not exists throw an exception

        :network_uuid: String
        :intf_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def delete_virtual_interface(self, intf_uuid):
        '''
        This should delete a virtual interface identified by intf_uuid, if the
         interface is assigned to a network
        maybe can also call removeInterfaceFromNetwork() to avoid any problem,
        if the interface not exists throw an exception

        :intf_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def delete_virtual_bridge(self, br_uuid):
        '''
        Delete a virtual bride, if the bridge is one assigned to a network
         should throw an exception, if the bridge not exists throw an exception

        :br_uuid: String
        :return: bool
        '''

        raise NotImplementedError('This is and interface!')

    def remove_interface_from_network(self, network_uuid, intf_uuid):
        '''
        Remove the interface intf_uuid from network network_uuid,
         if interface not present throw an exception

        :network_uuid: String
        :intf_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def delete_virtual_network(self, network_uuid):
        '''
        Delete the virtual network network_uuid, for correct network shutdown
         should kill the dnsmasq process eventually associated
        for dhcp and remove the bridge, if there are interface associate
         to this network should throw an exception

        :network_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def create_virtual_link(self, vl_uuid, connection_points):
        '''
        Create a virtual link between 2 connection points

        eg if is a linux bridge

        sudo ip link add vl_name type bridge
        sudo ip link set cp_1 master bridge_name
        sudo ip link set cp_2 master bridge_name


        :param vl_uuid: string uuid of the new virtual link
        :param connection_points: list of 2 connection point uuid
        :return: the virtual name
        (vl is a linux bridge or a openvswitch with only 2 ports)
        '''

    def create_connection_point(self, cp_uuid):
        '''
        Create a connection point with the given uuid

        ip tuntap add dev tun0 mode tun

        ip tuntap add dev tap0-1 mode tap

        attach one to the atomic entity and the other will be the
         connection point


        DEVICE TYPE FOR IP2ROUTE
          TYPE := { vlan | veth | vcan | dummy | ifb | macvlan | macvtap |
          bridge | bond | ipoib | ip6tnl | ipip | sit | vxlan |
          gre | gretap | ip6gre | ip6gretap | vti | nlmon |
          bond_slave | ipvlan | geneve | bridge_slave | vrf }

        :param cp_uuid:
        :return: the name of the connection point
         (the connection point is a virtual interface like a vtap interface)
        '''

    def stop_network(self):
        raise NotImplementedError

    def get_network_info(self, network_uuid):
        raise NotImplementedError


class BridgeAssociatedToNetworkException(Exception):
    def __init__(self, message, errors=0):
        super(BridgeAssociatedToNetworkException, self).__init__(message)
        self.errors = errors


class NetworkAlreadyExistsException(Exception):
    def __init__(self, message, errors=0):
        super(NetworkAlreadyExistsException, self).__init__(message)
        self.errors = errors


class NetworkHasPendingInterfacesException(Exception):
    def __init__(self, message, errors=0):

        super(NetworkHasPendingInterfacesException, self).__init__(message)
        self.errors = errors


class InterfaceNotInNetworkException(Exception):
    def __init__(self, message, errors=0):

        super(InterfaceNotInNetworkException, self).__init__(message)
        self.errors = errors


class BridgeNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(BridgeNotExistingException, self).__init__(message)
        self.errors = errors


class InterfaceNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(InterfaceNotExistingException, self).__init__(message)
        self.errors = errors
