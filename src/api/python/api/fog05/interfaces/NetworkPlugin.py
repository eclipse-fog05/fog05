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

import time
from fog05.interfaces.Plugin import Plugin


class NetworkPlugin(Plugin):
    '''
    Class: NetworkPlugin

    This class is an interface for plugins that control the network resouces,
    and provides an abstraction layer
    for networking managment functions
    '''

    def __init__(self, version, plugin_uuid):
        super(NetworkPlugin, self).__init__(version, plugin_uuid)

    def wait_dependencies(self):
        '''
        Waits for the Agent and the OS plugin to be ready
        '''
        self.get_agent()
        os = None
        while os is None:
            try:
                os = self.get_os_plugin()
            except (RuntimeError, ValueError):
                time.sleep(1)
        return

    def create_virtual_interface(self, intf_id, descriptor):
        '''
        This should create a virtual network interface

        paramters
        ---------
        intf_id : string
            UUID of the virtual interface
        descriptor : dictionary
            descriptor of the virtual interface

        returns
        ---------
        dictionary
            in the form of {'result':interface_info}

        '''
        raise NotImplementedError('This is and interface!')

    def create_virtual_bridge(self, name, uuid):
        '''
        This should create a virtual bridge

        parameters
        -----------
        name : string
            name of the virtual bridge to be created


        returns
        -------
        dictionary

            in the form of {'result':{'uuid': bridge uuid, 'name':bridge name}}
        '''
        raise NotImplementedError('This is and interface!')

    def allocate_bandwidth(self, intf_uuid, bandwidth):
        '''
        This should allocate bandwidth to a given virtual interface,
        if the interface not exists throw an exception

        parameters
        ----------
        intf_uuid : string

            UUID of the virtual interface

        bandwidth : int

            bandwidth to be allocated in Mbps

        returns
        -------
        bool

        '''
        raise NotImplementedError('This is and interface!')

    def create_virtual_network(self, network_name, uuid, ip_range, has_dhcp,
                               gateway, manifest):
        '''
        This should create a virtual network, with given caratteristics


        parameters
        ----------


        network_name : string

            name of the virtual network to be created

        uuid : string

            UUID of the virtual network to be created

        ip_range : string

            range should specified as CIRD subnet
            eg. 192.168.0.0/24 which means from 192.168.0.1 to 192.168.0.254

        has_dhcp : bool

            if the virtual network will have a DHCP server

        gateway : string

            IP address of the default gateway,if  None the FDUS connected to the
            network cannot reach internet

        manifest : dictionary

            the virtual network descriptor


        returns
        -------

        (string, string)

            in the form of (net_name,net_uuid)

        '''

        raise NotImplementedError('This is and interface!')

    def delete_virtual_interface(self, intf_id):
        '''
        Deletes the given virtual interface


        parameters
        ---------

        intf_id : string


        returns
        -------
        dictionary

            {'result':interface info}

        '''

        raise NotImplementedError('This is and interface!')

    def delete_virtual_bridge(self, br_uuid):
        '''
        Deletes a virtual bride, if the bridge is one assigned to a network
         should throw an exception, if the bridge not exists throw an exception

        parameters
        ----------

        br_uuid : string

            bridge UUID

        returns
        -------

        dictionary

            {'result': bridge UUID}

        '''

        raise NotImplementedError('This is and interface!')

    def delete_virtual_network(self, network_uuid):
        '''
        Delete the virtual network network_uuid, for correct network shutdown
         should kill the dnsmasq process eventually associated
        for dhcp and remove the bridge, if there are interface associate
         to this network should throw an exception


        parameters
        ----------


        network_uuid : string

            Network UUID

        returns
        -------
        bool

        '''

        raise NotImplementedError('This is and interface!')

    def get_virtual_bridges_in_node(self):
        '''
        Gets a list with the names of the current virtual bridges running in the node

        returns
        ------
        string list

        '''

    def stop_network(self):
        '''
        Stops the networking plugin
        '''
        raise NotImplementedError

    def get_network_info(self, network_uuid):
        '''
        Gives information on a given virtual network


        parameters
        ---------

        network_uuid : string

            network UUID

        returns
        -------

        dictionary

        '''
        raise NotImplementedError

    def create_bridges_if_not_exist(self, expected_bridges):
        '''
        Creates the bridges missing after checking the manifest file

        parameters
        ----------

        expected_bridges : string list

            names of expected bridges

        returns
        -------
        dictionary

            in the form {'result': string list}

        '''
        raise NotImplementedError

    def connect_interface_to_connection_point(self, intf_id, cp_id):
        '''
        Connects the given interace to the given connection point

        parameters
        ----------
        intf_id : string
            ID of the virtual interface
        cp_id : string
            UUID of the connection point

        returns
        -------
        dictionary
            {'result':{'int':string, 'ext':string}}
        '''
        raise NotImplementedError

    def disconnect_interface(self, intf_id):
        '''
        Disconnects the given interface

        parameters
        ----------
        intf_id : string
            ID of the virtual interace

        returns
        -------
        dictionary
            {'result':{'int':string, 'ext':string}}
        '''
        raise NotImplementedError

    def connect_cp_to_vnetwork(self, cp_id, vnet_id):
        '''
        Connects the given connection point to the given network

        parameters
        ----------
        cp_id : string
            UUID of the connection point
        vnet_id : string
            UUID of the virtual network

        returns
        -------
        dictionary
            {'result':{'int':string, 'ext':string}}

        '''
        raise NotImplementedError

    def disconnect_cp(self, cp_id):
        '''
        Disconnects the given connection point

        parameters
        ----------
        cp_id : string
            UUID of connection point

        returns
        -------
        dictionary
            {'result':{'int':string, 'ext':string}}
        '''
        raise NotImplementedError

    def delete_port(self, cp_id):
        '''
        Deletes the given connection point

        parameters
        ----------
        cp_id : string
            UUID of the connection point

        returns
        -------
        dictionary
            {'result':dictionary}
        '''
        raise NotImplementedError

    def get_address(self, mac_address):
        '''
        Gets the IP address associated to the interface with the given MAC address

        parameters
        ----------
        mac_address : string
            the MAC address of the interface

        returns
        -------
        dictionary
            {'result':string}
        '''
        raise NotImplementedError

    def add_port_to_router(self, router_id, port_type, vnet_id=None, ip_address=None):
        '''
        Adds a port to the given virtual router

        parameters
        ----------
        router_id : string
            UUID of the virtual router
        port_type : string
            kind of the port to be added (INTERNAL, EXTERNAL)
        vnet_id : string
            eventual network to be connected
        ip_address : string
            eventual address for the new router port

        returns
        -------
        dictionary
        '''
        raise NotImplementedError

    def remove_port_from_router(self, router_id, vnet_id):
        '''
        Removes a port from the given router

        parameters
        ----------
        router_id : string
            UUID of the virtual router
        vnet_id : string
            network to be disconnected

        returns
        -------
        dictionary
            {'result':dictionary}
        '''
        raise NotImplementedError

    def create_floating_ip(self):
        '''
        Creates a floating IP

        returns
        -------
        dictionary
            {'result':dictionary}
        '''
        raise NotImplementedError

    def delete_floating_ip(self, ip_id):
        '''
        Deletes the given floating IP

        parameters
        ----------
        ip_id : string
            UUID of the floating IP

        returns
        -------
        dictionary
            {'result':dictionary}
        '''
        raise NotImplementedError

    def assign_floating_ip(self, ip_id, cp_id):
        '''
        Assigns the given floating IP to the given conncetion point

        parameters
        ----------
        ip_id : string
            UUID of the floating IP
        cp_id : string
            UUID of the connection point

        returns
        -------
        dictionary
            {'result':dictionary}
        '''
        raise NotImplementedError

    def remove_floating_ip(self, ip_id, cp_id):
        '''
        Retains the given floating IP to the given conncetion point

        parameters
        ----------
        ip_id : string
            UUID of the floating IP
        cp_id : string
            UUID of the connection point

        returns
        -------
        dictionary
            {'result':dictionary}
        '''
        raise NotImplementedError

    def get_overlay_face(self):
        '''
        Gets the configured interface for overlay networks

        returns
        -------
        string
        '''
        raise NotImplementedError

    def get_vlan_face(self):
        '''
        Gets the configured interface for VLAN networks

        returns
        -------
        string
        '''
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
