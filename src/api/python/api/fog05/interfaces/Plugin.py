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


    class OS(object):
        def __init__(self,uuid, connector, node):
            self.uuid = uuid
            self.connector =  connector
            self.node =  node

        def call_os_plugin_function(self, fname, fparameters):
            res = self.connector.loc.actual.exec_os_eval(
                self.node, fname, fparameters)
            if res.get('error'):
                raise ValueError('OS Eval returned {}'.format(res.get('error')))
                # return None
            return res.get('result')

        def dir_exists(self, dir_path):
            return self.call_os_plugin_function('dir_exists',{'dir_path':dir_path})

        def create_dir(self, dir_path):
            return self.call_os_plugin_function('create_dir',{'dir_path':dir_path})

        def download_file(self, url, file_path):
            return self.call_os_plugin_function('download_file',{'url':url,'file_path':file_path})

        def execute_command(self, command, blocking=False, external=False):
            return self.call_os_plugin_function('execute_command',{'command':command,'blocking':blocking,'external':external})

        def remove_dir(self, dir_path):
            return self.call_os_plugin_function('remove_dir',{'dir_path':dir_path})

        def create_file(self, file_path):
            return self.call_os_plugin_function('create_file',{'file_path':file_path})

        def remove_file(self, file_path):
            return self.call_os_plugin_function('remove_file',{'file_path':file_path})

        def store_file(self, content, file_path, filename):
            content = binascii.hexlify(base64.b64encode(bytes(content,'utf-8'))).decode()
            return self.call_os_plugin_function('store_file',{'content':content,'file_path':file_path,'filename':filename})

        def read_file(self, file_path, root=False):
            return self.call_os_plugin_function('read_file',{'file_path':file_path,'root':root})

        def file_exists(self, file_path):
            return self.call_os_plugin_function('file_exists',{'file_path':file_path})

        def send_sig_int(self, pid):
            return self.call_os_plugin_function('send_sig_int',{'pid':pid})

        def check_if_pid_exists(self, pid):
            return self.call_os_plugin_function('check_if_pid_exists',{'pid':pid})

        def send_sig_kill(self, pid):
            return self.call_os_plugin_function('send_sig_kill',{'pid':pid})

        def get_intf_type(self, name):
            return self.call_os_plugin_function('get_intf_type',{'name':name})

        def set_interface_unaviable(self, intf_name):
            return self.call_os_plugin_function('set_interface_unaviable',{'intf_name':intf_name})

        def set_interface_available(self, intf_name):
            return self.call_os_plugin_function('set_interface_available',{'intf_name':intf_name})

        def get_network_informations(self):
            return self.call_os_plugin_function('set_interface_available',{})

        def checksum(self, file_path):
            return self.call_os_plugin_function('checksum',{'file_path':file_path})

        def local_mgmt_address(self):
            return self.call_os_plugin_function('local_mgmt_address',{})

    class NM(object):
        def __init__(self, uuid, connector, node):
            self.uuid = uuid
            self.connector =  connector
            self.node =  node

        def call_nw_plugin_function(self, fname, fparameters):
            res = self.connector.loc.actual.exec_nw_eval(
                self.node, self.uuid, fname, fparameters)
            if res.get('error'):
                raise ValueError('NM Eval returned {}'.format(res.get('error')))
                # return None
            return res.get('result')

        def create_virtual_interface(self,intf_id, descriptor):
            return self.call_nw_plugin_function('create_virtual_interface',{'intf_id':intf_id,'descriptor':descriptor})

        def delete_virtual_interface(self, intf_id):
            return self.call_nw_plugin_function('delete_virtual_interface',{'intf_id':intf_id})

        def create_virtual_bridge(self, name, uuid):
            return self.call_nw_plugin_function('create_virtual_bridge',{'name':name,'uuid':uuid})

        def delete_virtual_bridge(self, br_uuid):
            return self.call_nw_plugin_function('delete_virtual_bridge',{'br_uuid':br_uuid})

        def create_bridges_if_not_exist(self, expected_bridges):
            return self.call_nw_plugin_function('create_bridges_if_not_exist',{'expected_bridges':expected_bridges})

        def connect_interface_to_connection_point(self, intf_id, cp_id):
            return self.call_nw_plugin_function('connect_interface_to_connection_point',{'intf_id':intf_id,'cp_id':cp_id})

        def disconnect_interface(self, intf_id):
            return self.call_nw_plugin_function('disconnect_interface',{'intf_id':intf_id})

        def connect_cp_to_vnetwork(self, cp_id, vnet_id):
            return self.call_nw_plugin_function('connect_cp_to_vnetwork',{'vnet_id':vnet_id,'cp_id':cp_id})

        def disconnect_cp(self, cp_id):
            return self.call_nw_plugin_function('disconnect_cp',{'cp_id':cp_id})

        def delete_port(self, cp_id):
            return self.call_nw_plugin_function('delete_port',{'cp_id':cp_id})

        def get_address(self, mac_address):
            return self.call_nw_plugin_function('get_address',{'mac_address':mac_address})

        def add_port_to_router(self, router_id, port_type, vnet_id=None, ip_address=None):
            return self.call_nw_plugin_function('add_port_to_router',{'router_id':router_id,'port_type':port_type,'vnet_id':vnet_id,'ip_address':ip_address})

        def remove_port_from_router(self, router_id, vnet_id):
            return self.call_nw_plugin_function('remove_port_from_router',{'router_id':router_id,'vnet_id':vnet_id})

        def create_floating_ip(self):
            return self.call_nw_plugin_function('create_floating_ip',{})

        def delete_floating_ip(self, ip_id):
            return self.call_nw_plugin_function('delete_floating_ip',{'ip_id':ip_id})

        def assign_floating_ip(self, ip_id, cp_id):
            return self.call_nw_plugin_function('assign_floating_ip',{'ip_id':ip_id,'cp_id':cp_id})

        def remove_floating_ip(self, ip_id, cp_id):
            return self.call_nw_plugin_function('remove_floating_ip',{'ip_id':ip_id,'cp_id':cp_id})

        def get_overlay_face(self):
            return self.call_nw_plugin_function('get_overlay_face',{})

        def get_vlan_face(self):
            return self.call_nw_plugin_function('get_vlan_face',{})


    class Agent(object):
        def __init__(self, connector, node):
            self.connector =  connector
            self.node =  node

        def call_agent_function(self, fname, fparameters):
            res = self.connector.loc.actual.exec_agent_eval(
                self.node, fname, fparameters)
            if res.get('error'):
                raise ValueError('Agent Eval returned {}'.format(res.get('error')))
                # return None
            return res.get('result')

        def get_image_info(self, imageid):
            return self.call_agent_function('get_image_info', {'image_uuid': imageid})

        def get_fdu_info(self, nodeid, fduid, instanceid):
            return self.call_agent_function('get_node_fdu_info', {'fdu_uuid':fduid,'instance_uuid':instanceid,'node_uuid':nodeid})

        def get_network_info(self, uuid):
            return self.call_agent_function('get_network_info',  {'uuid': uuid})

        def get_port_info(self, cp_uuid):
            return self.call_agent_function('get_port_info',  {'cp_uuid': cp_uuid})

        def get_node_mgmt_address(self, nodeid):
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
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        nms = [x for x in pls if x.get('type') == 'network']
        if len(nms) == 0:
            raise RuntimeError('No network_manager present in the node!!')
        nm = nms[0]
        self.nm = Plugin.NM(nm['uuid'], self.connector, self.node)
        return nm

    def get_os_plugin(self):
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        os = [x for x in pls if x.get('type') == 'os']
        if len(os) == 0:
            raise RuntimeError('No os plugin present in the node!!')
        os = os[0]
        self.os = Plugin.OS(os['uuid'], self.connector, self.node)
        return os

    def get_agent(self):
        self.os = Plugin.Agent( self.connector, self.node)
        return self.agent

    def get_local_mgmt_address(self):
        return self.os.local_mgmt_address()

    def get_version(self):
        return self.version

    def react_to_cache(self, key, value, version):
        raise NotImplementedError
