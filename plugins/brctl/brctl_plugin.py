# Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set

import sys
import os
import uuid
import struct
import json
from fog05.interfaces.NetworkPlugin import *
from jinja2 import Environment
import socket


# TODO Plugins should not be aware of the Agent - The Agent is in OCaml no way to access his store, his logger and the OS plugin

class brctl(NetworkPlugin):

    def __init__(self, name, version, agent, plugin_uuid, configuration={}):
        super(brctl, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.interfaces_map = {}
        self.brmap = {}
        self.netmap = {}
        self.configuration = configuration
        self.agent.logger.info('__init__()', ' Hello from bridge-utils Plugin')
        self.BASE_DIR = os.path.join(self.agent.base_path, 'brctl')
        # self.BASE_DIR = '/opt/fos/brctl'
        self.DHCP_DIR = 'dhcp'
        self.HOME = 'network/{}'.format(self.uuid)
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.overlay_interface = None

        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.DHCP_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DHCP_DIR))
        else:
            self.agent.get_os_plugin().create_dir(self.BASE_DIR)
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DHCP_DIR))

        if self.configuration.get('data_subnet'):
            cird = self.configuration.get('data_subnet')

            data = json.loads(self.agent.astore.get(self.agent.ahome))
            for n in data.get('network'):
                intf_cird = self.__ip_mask_to_cird(
                    n.get('inft_configuration').get('ipv4_address'),
                    n.get('inft_configuration').get('ipv4_netmask')
                )
                if cird == intf_cird:
                    self.overlay_interface = n.get('intf_name')

        '''
        should listen on:
        
        - //dfos/<sys-id>/<node-id>/network/<myuuid>/networks/**
        - //dfos/<sys-id>/<node-id>/network/<myuuid>/bridges/**
        - //dfos/<sys-id>/<node-id>/network/<myuuid>/interfaces/**
        
        '''

        uri = '{}/{}/networks/**'.format(self.agent.dhome, self.HOME)
        self.agent.dstore.observe(uri, self.__react_to_cache_networks)
        self.agent.logger.info('startRuntime()', ' bridge-utils Plugin - Observing {}'.format(uri))

    def create_virtual_interface(self, name, uuid):
        # sudo ip link add type veth
        # sudo ip link set dev veth1 addr 00:01:02:aa:bb:cc name vnic0
        # sudo ip link add name vnic0 type veth peer name vnic0-vm

        cmd = '{}{}'.format(name, name)
        self.agent.get_os_plugin().execute_command(cmd)
        intf_uuid = uuid
        self.interfaces_map.update({uuid: name})

        return name, intf_uuid

    def create_virtual_bridge(self, name, uuid):
        cmd = 'sudo brctl addbr {}'.format(name)
        self.agent.get_os_plugin().execute_command(cmd)
        br_uuid = uuid
        self.brmap.update({br_uuid, name})
        return br_uuid, name

    def create_virtual_network(self, network_name, net_uuid, ip_range=None, has_dhcp=False, gateway=None, manifest=None):

        self.agent.logger.info('create_virtual_network()',
                               'Parameters network_name:{} net_uudi:{} ip_range:{} has_dhcp:{} gateway:{} manifest:{}'.format(network_name, net_uuid, ip_range, has_dhcp, gateway, manifest))

        net = self.netmap.get(net_uuid, None)
        if net is not None:
            self.agent.logger.error('create_virtual_network()', '{} network already exists'.format(net_uuid))
            return None

        info = {}
        pi = []

        info.update({'name': network_name})
        info.update({'interfaces': pi})
        info.update({'uuid': net_uuid})
        info.update({'has_dhcp': has_dhcp})
        info.update({'ip_range': ip_range})
        info.update({'gateway': gateway})

        # TODO these information should be loaded from manifest
        info.update({'dns': ''})
        info.update({'dhcp_range': ''})
        info.update({'ip_type': ''})
        info.update({'network_type': 'vxlan'})
        # brcmd = 'sudo brctl addbr {}-net', network_name)
        # net_uuid = uuid
        #
        br_name = 'br-{}'.format(net_uuid.split('-')[0])

        vxlan_file, vxlan_dev, vxlan_id, vxlan_mcast = self.__generate_vxlan_script(net_uuid, manifest)
        shutdown_file = self.__generate_vxlan_shutdown_script(net_uuid)

        shutdown_file = os.path.join(self.BASE_DIR, shutdown_file)

        self.agent.get_os_plugin().execute_command(os.path.join(self.BASE_DIR, vxlan_file), True)

        info.update({'virtual_device': br_name})
        info.update({'vxlan_dev': vxlan_dev})
        info.update({'vxlan_id': vxlan_id})
        info.update({'multicast_address': vxlan_mcast})

        # self.agent.getOSPlugin().executeCommand(brcmd)

        if has_dhcp is True:
            address = self.__cird2block(ip_range)

            ifcmd = 'sudo ifconfig {} {} netmask {}'.format(br_name, address[0], address[3])
            # TODO this should done by the OSPlugin
            # dhcpq_cmd = 'sudo dnsmasq -d  --interface={} --bind-interfaces  --dhcp-range={},'
            #                '{} --listen-address {} > {}/{}/{}.out 2>&1 & echo $! > {}/{}/{}.pid' %
            #                (br_name, address[1], address[2], address[0], self.BASE_DIR, self.DHCP_DIR, br_name,
            #                 self.BASE_DIR,
            #                 self.DHCP_DIR, br_name))
            file_name = '{}_dnsmasq.pid'.format(br_name)
            pid_file_path = os.path.join(self.BASE_DIR, self.DHCP_DIR, file_name)

            dhcp_cmd = self.__generate_dnsmaq_script(br_name, address[1], address[2], address[0], pid_file_path)
            dhcp_cmd = os.path.join(self.BASE_DIR, self.DHCP_DIR, dhcp_cmd)

            self.agent.get_os_plugin().execute_command(ifcmd, True)
            self.agent.get_os_plugin().execute_command(dhcp_cmd)

        self.netmap.update({net_uuid: info})
        uri = 'networks/{}'.format(net_uuid)
        self.__update_actual_store(uri, info)

        self.agent.logger.info('createVirtualNetwork()', 'Created {} Network'.format(net_uuid))

        return network_name, net_uuid

    def allocate_bandwidth(self, intf_uuid, bandwidth):
        raise NotImplemented

    def assign_interface_to_network(self, network_uuid, intf_uuid):
        # brctl addif virbr0 vnet0
        intf = self.interfaces_map.get(intf_uuid, None)
        if intf is None:
            raise InterfaceNotExistingException('{} interface not exists'.format(intf_uuid))
        net = self.netmap.get(network_uuid, None)
        if net is None:
            raise BridgeAssociatedToNetworkException('{} network not exists'.format(network_uuid))

        br_cmd = 'sudo brctl addif {}-net {}'.format(net.get('network_name'), intf)
        self.agent.get_os_plugin().execute_command(br_cmd)

        return True

    def delete_virtual_interface(self, intf_uuid):
        # ip link delete dev ${interface name}
        intf = self.interfaces_map.get(intf_uuid, None)
        if intf is None:
            raise InterfaceNotExistingException('{} interface not exists'.format(intf_uuid))
        rm_cmd = 'sudo ip link delete dev {}'.format(intf)
        self.agent.get_os_plugin().execute_command(rm_cmd)
        self.interfaces_map.pop(intf_uuid)
        return True

    def delete_virtual_bridge(self, br_uuid):

        net = self.netmap.get(br_uuid, None)
        if net is not None:
            raise BridgeAssociatedToNetworkException('{} associated to a network'.format(br_uuid))
        br = self.brmap.get(br_uuid, None)
        if br is None:
            raise BridgeNotExistingException('{} bridge not exists'.format(br_uuid))

        rm_cmd = 'sudo brcrl delbr {}'.format(br)
        self.agent.get_os_plugin().execute_command(rm_cmd)
        self.brmap.pop(br_uuid)
        return True

    def remove_interface_from_network(self, network_uuid, intf_uuid):
        net = self.netmap.get(network_uuid, None)
        if net is None:
            raise BridgeAssociatedToNetworkException('{} network not exists'.format(network_uuid))
        intf = self.brmap.get(intf_uuid, None)
        if intf is None:
            raise InterfaceNotExistingException('{} interface not exists'.format(intf_uuid))
        if intf not in net.get('intf'):
            raise InterfaceNotInNetworkException('{} interface not in this networks'.format(intf_uuid))

        net.get('intf').remove(intf)
        return True

    def delete_virtual_network(self, network_uuid):
        net = self.netmap.get(network_uuid, None)
        if net is None:
            raise BridgeAssociatedToNetworkException('{} network not exists'.format(network_uuid))
        if len(net.get('interfaces')) > 0:
            raise NetworkHasPendingInterfacesException('{} has pending interfaces'.format(network_uuid))

        shutdown_file = self.__generate_vxlan_shutdown_script(network_uuid)
        shutdown_file = os.path.join(self.BASE_DIR, shutdown_file)
        start_file = os.path.join(self.BASE_DIR, '{}.sh'.format(network_uuid.split('-')[0]))
        dnsmasq_file = os.path.join(self.BASE_DIR, self.DHCP_DIR, 'br-{}_dnsmasq.sh'.format(network_uuid.split('-')[0]))

        self.agent.get_os_plugin().execute_command('sudo {}'.format(shutdown_file), True)
        self.agent.get_os_plugin().remove_file(shutdown_file)
        self.agent.get_os_plugin().remove_file(start_file)
        self.agent.get_os_plugin().remove_file(dnsmasq_file)
        self.netmap.pop(network_uuid)
        uri = 'networks/{}'.format(network_uuid)
        self.__pop_actual_store(uri)

        self.agent.logger.info('deleteVirtualNetwork()', 'Deleted {}'.format(network_uuid))

        return True

    def stop_network(self):
        keys = list(self.netmap.keys())
        for k in keys:
            self.delete_virtual_network(k)
        return True

    def get_network_info(self, network_uuid):
        if network_uuid is None:
            return self.netmap
        return self.netmap.get(network_uuid)

    def __pop_actual_store(self, net_uuid):
        uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME, net_uuid)
        self.agent.astore.remove(uri)

    def __update_actual_store(self, uri, value):
        uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME, uri)
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __cird2block(self, cird):
        '''
            Convert cird subnet to first address (for router), dhcp avaiable range, netmask

        :param cird:
        :return:
        '''
        (ip, cidr) = cird.split('/')
        cidr = int(cidr)
        host_bits = 32 - cidr
        netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
        i = struct.unpack('>I', socket.inet_aton(ip))[0]
        start = (i >> host_bits) << host_bits
        end = i | ((1 << host_bits) - 1)

        return socket.inet_ntoa(struct.pack('>I', start + 1)), socket.inet_ntoa(
            struct.pack('>I', start + 2)), socket.inet_ntoa(struct.pack('>I', end - 1)), netmask

    def __get_net_size(self, netmask):
        binary_str = ''
        for octet in netmask:
            binary_str += bin(int(octet))[2:].zfill(8)
        return str(len(binary_str.rstrip('0')))

    def __ip_mask_to_cird(self, ip, mask):

        try:
            socket.inet_aton(ip)
            socket.inet_aton(mask)
        except:
            return "0.0.0.0/0"

        ip = ip.split('.')
        mask = mask.split('.')
        net_start = [str(int(ip[x]) & int(mask[x])) for x in range(0, 4)]
        return '.'.join(net_start) + '/' + self.__get_net_size(mask)

    def __react_to_cache_networks(self, key, value, v):
        self.agent.logger.info('__react_to_cache_networks()', ' BRCTL Plugin - React to to URI: {} Value: {} Version: {}'.format(key, value, v))
        uuid = key.split('/')[-1]
        value = json.loads(value)
        action = value.get('status')
        react_func = self.__react(action)
        if action == 'undefine':
            self.delete_virtual_network(uuid)
        if react_func is not None and action != 'undefine':
            react_func(**value)

    def __parse_manifest_for_add(self, **kwargs):
        net_uuid = kwargs.get('uuid')
        name = kwargs.get('name')
        ip_range = kwargs.get('ip_range')
        has_dhcp = kwargs.get('has_dhcp')
        gw = kwargs.get('gateway')
        manifest = kwargs
        self.create_virtual_network(name, net_uuid, ip_range, has_dhcp, gw, manifest)

    def __parse_manifest_for_remove(self, **kwargs):
        net_uuid = kwargs.get('uuid')
        self.delete_virtual_network(net_uuid)

    def __react(self, action):
        r = {
            'add': self.__parse_manifest_for_add,
            'remove': self.__parse_manifest_for_remove,
        }

        return r.get(action, None)

    def __generate_vxlan_shutdown_script(self, net_uuid):

        template_sh = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'vxlan_destroy.sh'))
        br_name = 'br-{}'.format(net_uuid.split('-')[0])
        vxlan_name = 'vxl-{}'.format(net_uuid.split('-')[0])
        file_name = '{}_dnsmasq.pid'.format(br_name)
        pid_file_path = os.path.join(self.BASE_DIR, self.DHCP_DIR, file_name)
        net_sh = Environment().from_string(template_sh)
        net_sh = net_sh.render(bridge=br_name, vxlan_intf_name=vxlan_name, dnsmasq_pid_file=pid_file_path)

        file_name = '{}_stop.sh'.format(br_name)
        self.agent.get_os_plugin().store_file(net_sh, self.BASE_DIR, file_name)
        chmod_cmd = 'chmod +x {}'.format(os.path.join(self.BASE_DIR, file_name))
        self.agent.get_os_plugin().execute_command(chmod_cmd, True)

        return file_name

    def __generate_dnsmaq_script(self, br_name, start_addr, end_addr, listen_addr, pid_file):
        template_sh = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'dnsmasq.sh'))
        dnsmasq_sh = Environment().from_string(template_sh)
        dnsmasq_sh = dnsmasq_sh.render(bridge_name=br_name, dhcp_start=start_addr, dhcp_end=end_addr, listen_addr=listen_addr, pid_path=pid_file)
        file_name = '{}_dnsmasq.sh'.format(br_name)
        path = os.path.join(self.BASE_DIR, self.DHCP_DIR)
        self.agent.get_os_plugin().store_file(dnsmasq_sh, path, file_name)
        chmod_cmd = 'chmod +x {}'.format(os.path.join(path, file_name))
        self.agent.get_os_plugin().execute_command(chmod_cmd, True)

        return file_name

    def __generate_vxlan_script(self, net_uuid, manifest=None):
        if not self.overlay_interface:
            template_sh = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'vxlan_creation.sh'))
        else:
            template_sh = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'vxlan_creation_intf.sh'))
        net_sh = Environment().from_string(template_sh)
        br_name = 'br-{}'.format(net_uuid.split('-')[0])
        vxlan_name = 'vxl-{}'.format(net_uuid.split('-')[0])

        if manifest is not None:
            if manifest.get('overlay_info') is not None and manifest.get('overlay_info').get('vxlan_id') is not None:
                vxlan_id = manifest.get('overlay_info').get('vxlan_id')
            else:
                vxlan_id = len(self.netmap) + 1
            if manifest.get('overlay_info') is not None and  manifest.get('overlay_info').get('multicast_address') is not None:
                mcast_addr = manifest.get('overlay_info').get('multicast_address')
            else:
                mcast_addr = '239.0.0.{}'.format(vxlan_id)
        else:
            vxlan_id = len(self.netmap) + 1
            mcast_addr = '239.0.0.{}'.format(vxlan_id)

        net_sh = net_sh.render(bridge_name=br_name, vxlan_intf_name=vxlan_name,
                               group_id=vxlan_id, mcast_group_address=mcast_addr, wan=self.overlay_interface)
        self.agent.get_os_plugin().store_file(net_sh, self.BASE_DIR, '{}.sh'.format(net_uuid.split('-')[0]))
        chmod_cmd = 'chmod +x {}'.format(os.path.join(self.BASE_DIR, '{}.sh'.format(net_uuid.split('-')[0])))
        # TODO chmod should be also executed by OSPlugin
        self.agent.get_os_plugin().execute_command(chmod_cmd, True)
        return '{}.sh'.format(net_uuid.split('-')[0]), vxlan_name, vxlan_id, mcast_addr
