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
# OCaml implementation and API

import uuid
import binascii
import base64

class Plugin(object):

    '''
    Class: Plugin

    This class is an interface for plugins

    '''


    class OS(object):
        '''
        Class: OS

        This class encapsulates the comunication with an OS plugin using YAKS Evals
        '''
        def __init__(self,uuid, connector, node):
            self.uuid = uuid
            self.connector =  connector
            self.node =  node

        def call_os_plugin_function(self, fname, fparameters):
            '''
            Calls an Eval registered within the OS Plugin

            parameters
            ----------
            fname : string
                function name

            fparameters : dictionary
                parameters for the function

            returns
            ------
            whatever the fname function returns or raises a ValueError
            '''
            res = self.connector.loc.actual.exec_os_eval(
                self.node, fname, fparameters)
            if res.get('error'):
                raise ValueError('OS Eval returned {}'.format(res.get('error')))
                # return None
            return res.get('result')

        def dir_exists(self, dir_path):
            '''
            Checks if the given directory exists

            parameters
            ----------
            dir_path : string
                path to the directory

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('dir_exists',{'dir_path':dir_path})

        def create_dir(self, dir_path):
            '''
            Creates the given new directory

            parameters
            ----------
            dir_path : string
                path to the directory

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('create_dir',{'dir_path':dir_path})

        def download_file(self, url, file_path):
            '''
            Downloads the given file in the given path

            parameters
            ----------
            url : string
                url for the source file
            file_path : string
                path to destination file

            returns
            ------
            bool
            '''
            return self.call_os_plugin_function('download_file',{'url':url,'file_path':file_path})

        def execute_command(self, command, blocking=False, external=False):
            '''
            Executes a command on underlying os,

            parameters
            ---------

            command : string
                command to be executed

            blocking : bool
                true if the call has to block until the end of the command

            external : bool
                true if the command has to be executed in an external os shell

            returns
            ------
            string
            '''
            return self.call_os_plugin_function('execute_command',{'command':command,'blocking':blocking,'external':external})

        def remove_dir(self, dir_path):
            '''
            Removes the given directory

            parameters
            ----------
            dir_path : string
                path to the directory

            returns
            -------
            bool

            '''
            return self.call_os_plugin_function('remove_dir',{'dir_path':dir_path})

        def create_file(self, file_path):
            '''
            Creates the given new empty file

            parameters
            ----------
            file_path : string
                path to the file

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('create_file',{'file_path':file_path})

        def remove_file(self, file_path):
            '''
            Removes the given file

            parameters
            ----------
            file_path : string
                path to the directory

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('remove_file',{'file_path':file_path})

        def store_file(self, content, file_path, filename):
            '''
            Stores a file in local disk

            parameters
            ----------

            content : string
                file content

            file_path : string
                path where the content will stored

            filename : string
                name of the file

            returns
            -------
            bool
            '''
            content = binascii.hexlify(base64.b64encode(bytes(content,'utf-8'))).decode()
            return self.call_os_plugin_function('store_file',{'content':content,'file_path':file_path,'filename':filename})

        def read_file(self, file_path, root=False):
            '''
            Read the content from a file in the local disk,
            maybe can convert from windows dir separator to unix dir separator
            return the file content
            throw an exception if file not exits

            parameters
            ----------

            file_path : string
                path to file

            root : bool
                if true it will use sudo cat to read the file

            returns
            --------
            bytes
            '''
            return self.call_os_plugin_function('read_file',{'file_path':file_path,'root':root})

        def file_exists(self, file_path):
            '''
            Checks if the given file exists

            parameters
            ----------
            file_path : string
                path to the file

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('file_exists',{'file_path':file_path})

        def send_sig_int(self, pid):
            '''
            Sends a SigKill (Ctrl+C) to the given PID

            parameters
            ----------
            pid : int
                pid to be signaled

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('send_sig_int',{'pid':pid})

        def check_if_pid_exists(self, pid):
            '''
            Checks if a  given PID exists

            parameters
            ----------
            pid : int
                PID to be verified

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('check_if_pid_exists',{'pid':pid})

        def send_sig_kill(self, pid):
            '''
            Sends a SigKill (kill the process) to the given pid
            throw an exception if pid not exits

            parameters
            ----------
            pid : int
                pid to be signaled

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('send_sig_kill',{'pid':pid})

        def get_intf_type(self, name):
            '''
            Gets the inteface type for the given interface

            parameters
            ----------
            name : string
                name of the interface

            returns
            -------
            string
            '''
            return self.call_os_plugin_function('get_intf_type',{'name':name})

        def set_interface_unaviable(self, intf_name):
            '''
            Sets a given network device as unavailable

            paramters
            ---------
            intf_name : string
                name of the network device

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('set_interface_unaviable',{'intf_name':intf_name})

        def set_interface_available(self, intf_name):
            '''
            Sets a given network device as available

            paramters
            ---------
            intf_name : string
                name of the network device

            returns
            -------
            bool
            '''
            return self.call_os_plugin_function('set_interface_available',{'intf_name':intf_name})

        def get_network_informations(self):
            '''
            Gets information about node network interfaces

            returns
            -------
            list of dictionaties
                {
                    'intf_name':string,
                    'intf_mac_address':string,
                    'intf_speed': int,
                    'type':string,
                    'available':bool,
                    'default_gw':bool,
                    'intf_configuration':
                    {
                        'ipv4_address':string,
                        'ipv4_netmask':string,
                        'ipv4_gateway':string.
                        'ipv6_address':string,
                        'ipv6_netmask':string,
                        'ipv6_gateway':string.
                        'bus_address':string
                    }
                }

            '''
            return self.call_os_plugin_function('set_interface_available',{})

        def checksum(self, file_path):
            '''
            Calculates the SHA256 checksum for the given file

            parameters
            -----------
            file_path : string
                path to file

            returns
            -------
            string
            '''
            return self.call_os_plugin_function('checksum',{'file_path':file_path})

        def local_mgmt_address(self):
            '''
            Gets node management IP address

            returns
            -------
            string
            '''
            return self.call_os_plugin_function('local_mgmt_address',{})

    class NM(object):
        '''
        Class: NM

        This class encapsulates the comunication with an NM plugin using YAKS Evals
        '''

        def __init__(self, uuid, connector, node):
            self.uuid = uuid
            self.connector =  connector
            self.node =  node

        def call_nw_plugin_function(self, fname, fparameters):
            '''
            Calls an Eval registered within the NM Plugin

            parameters
            ----------
            fname : string
                function name

            fparameters : dictionary
                parameters for the function

            returns
            ------
            whatever the fname function returns or raises a ValueError
            '''
            res = self.connector.loc.actual.exec_nw_eval(
                self.node, self.uuid, fname, fparameters)
            if res.get('error'):
                raise ValueError('NM Eval returned {}'.format(res.get('error')))
                # return None
            return res.get('result')

        def create_virtual_interface(self,intf_id, descriptor):
            '''
            Creates a virtual network interface

            paramters
            ---------
            intf_id : string
                UUID of the virtual interface
            descriptor : dictionary
                descriptor of the virtual interface

            returns
            ---------
            dictionary
            '''
            return self.call_nw_plugin_function('create_virtual_interface',{'intf_id':intf_id,'descriptor':descriptor})

        def delete_virtual_interface(self, intf_id):
            '''
            Deletes the given virtual interface

            parameters
            ---------
            intf_id : string


            returns
            -------
            dictionary
            '''
            return self.call_nw_plugin_function('delete_virtual_interface',{'intf_id':intf_id})

        def create_virtual_bridge(self, name, uuid):
            '''
        Creates a virtual bridge

            parameters
            -----------
            name : string
                name of the virtual bridge to be created


            returns
            -------
            dictionary
            '''
            return self.call_nw_plugin_function('create_virtual_bridge',{'name':name,'uuid':uuid})

        def delete_virtual_bridge(self, br_uuid):
            '''
            Deletes a virtual bride

            parameters
            ----------
            br_uuid : string
                bridge UUID

            returns
            -------
            dictionary
            '''
            return self.call_nw_plugin_function('delete_virtual_bridge',{'br_uuid':br_uuid})

        def create_bridges_if_not_exist(self, expected_bridges):
            '''
            Creates the bridges missing after checking the manifest file

            parameters
            ----------
            expected_bridges : string list
                names of expected bridges

            returns
            -------
            string list

            '''
            return self.call_nw_plugin_function('create_bridges_if_not_exist',{'expected_bridges':expected_bridges})

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
                {'int':string, 'ext':string}
            '''
            return self.call_nw_plugin_function('connect_interface_to_connection_point',{'intf_id':intf_id,'cp_id':cp_id})

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
                {'int':string, 'ext':string}
            '''
            return self.call_nw_plugin_function('disconnect_interface',{'intf_id':intf_id})

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
                {'int':string, 'ext':string}
            '''
            return self.call_nw_plugin_function('connect_cp_to_vnetwork',{'vnet_id':vnet_id,'cp_id':cp_id})

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
                {'int':string, 'ext':string}
            '''
            return self.call_nw_plugin_function('disconnect_cp',{'cp_id':cp_id})

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
            '''
            return self.call_nw_plugin_function('delete_port',{'cp_id':cp_id})

        def get_address(self, mac_address):
            '''
            Gets the IP address associated to the interface with the given MAC address

            parameters
            ----------
            mac_address : string
                the MAC address of the interface

            returns
            -------
            string
            '''
            return self.call_nw_plugin_function('get_address',{'mac_address':mac_address})

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
            return self.call_nw_plugin_function('add_router_port',{'router_id':router_id,'port_type':port_type,'vnet_id':vnet_id,'ip_address':ip_address})

        def remove_port_from_router(self, router_id, vnet_id):
            '''
            Removes a port from the given router

            ßparameters
            ----------
            router_id : string
                UUID of the virtual router
            vnet_id : string
                network to be disconnected

            returns
            -------
            dictionary

            '''
            return self.call_nw_plugin_function('remove_port_from_router',{'router_id':router_id,'vnet_id':vnet_id})

        def create_floating_ip(self):
            '''
            Creates a floating IP

            returns
            -------
            dictionary
            '''
            return self.call_nw_plugin_function('create_floating_ip',{})

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

            '''
            return self.call_nw_plugin_function('delete_floating_ip',{'ip_id':ip_id})

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
            '''
            return self.call_nw_plugin_function('assign_floating_ip',{'ip_id':ip_id,'cp_id':cp_id})

        def remove_floating_ip(self, ip_id, cp_id):
            '''
            Retains the given floating IP from the given connection point

            parameters
            ----------
            ip_id : string
                UUID of the floating IP
            cp_id : string
                UUID of the connection point

            returns
            -------
            dictionary
            '''
            return self.call_nw_plugin_function('remove_floating_ip',{'ip_id':ip_id,'cp_id':cp_id})

        def get_overlay_face(self):
            '''
            Gets the configured interface for overlay networks

            returns
            -------
            string
            '''
            return self.call_nw_plugin_function('get_overlay_face',{})

        def get_vlan_face(self):
            '''
            Gets the configured interface for VLAN networks

            returns
            -------
            string
            '''
            return self.call_nw_plugin_function('get_vlan_face',{})


    class Agent(object):
        '''
        Class: OS

        This class encapsulates the comunication with Agent using YAKS Evals
        '''
        def __init__(self, connector, node):
            self.connector =  connector
            self.node =  node

        def call_agent_function(self, fname, fparameters):
            '''
            Calls an Eval registered within the Agent

            parameters
            ----------
            fname : string
                function name

            fparameters : dictionary
                parameters for the function

            returns
            ------
            whatever the fname function returns or raises a ValueError
            '''
            res = self.connector.loc.actual.exec_agent_eval(
                self.node, fname, fparameters)
            if res.get('error'):
                raise ValueError('Agent Eval returned {}'.format(res.get('error')))
                # return None
            return res.get('result')

        def get_image_info(self, imageid):
            '''
            Gets information about the given image

            parameters
            ----------
            imageid : string
                UUID of the image

            returns
            -------
            dictionary
            '''
            return self.call_agent_function('get_image_info', {'image_uuid': imageid})

        def get_fdu_info(self, nodeid, fduid, instanceid):
            '''
            Gets information about the given FDU instance

            parameters
            ----------
            nodeid : string
                UUID of the node
            fduid : string
                UUID of the FDU
            instanceid : string
                UUID of the instance

            returns
            -------
            dictionary

            '''
            return self.call_agent_function('get_node_fdu_info', {'fdu_uuid':fduid,'instance_uuid':instanceid,'node_uuid':nodeid})

        def get_network_info(self, uuid):
            '''
            Gets information about the given virtual network

            parameters
            ----------
            uuid : string
                UUID of the virtual network

            returns
            -------
            dictionary

            '''
            return self.call_agent_function('get_network_info',  {'uuid': uuid})

        def get_port_info(self, cp_uuid):
            '''
            Gets information about a given connection point

            parameters
            ----------
            cp_uuid : string
                UUID of the connection point

            returns
            -------
            dictionary
            '''
            return self.call_agent_function('get_port_info',  {'cp_uuid': cp_uuid})

        def get_node_mgmt_address(self, nodeid):
            '''
            Gets management IP address for the given node

            parameters
            ----------
            nodeid : string
                UUID of the node

            returns
            -------
            string
            '''
            self.call_agent_function('get_node_mgmt_address', {'node_uuid': nodeid})


    def __init__(self, version, plugin_uuid=None):
        self.version = version
        self.connector = None
        self.node = None
        self.nm = None
        self.os = None
        self.agent = None
        if uuid is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = plugin_uuid

    def get_nm_plugin(self):
        '''
        Retrives the network manager plugin from YAKS

        returns
        -------
        NM
        '''
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        nms = [x for x in pls if x.get('type') == 'network']
        if len(nms) == 0:
            raise RuntimeError('No network_manager present in the node!!')
        nm = nms[0]
        self.nm = Plugin.NM(nm['uuid'], self.connector, self.node)
        return nm

    def get_os_plugin(self):
        '''
        Retrives the operating system plugin from YAKS

        returns
        -------
        OS
        '''
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        os = [x for x in pls if x.get('type') == 'os']
        if len(os) == 0:
            raise RuntimeError('No os plugin present in the node!!')
        os = os[0]
        self.os = Plugin.OS(os['uuid'], self.connector, self.node)
        return os

    def get_agent(self):
        '''
        Retrives the agent from YAKS

        returns
        -------
        Agent
        '''
        self.agent = Plugin.Agent( self.connector, self.node)
        return self.agent

    def get_local_mgmt_address(self):
        '''
        Gets local management IP address

        returns
        -------
        string
        '''
        return self.os.local_mgmt_address()

    def get_version(self):
        '''
        Gets plugin version

        returns
        -------
        string
        '''
        return self.version

