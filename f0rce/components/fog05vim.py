# Copyright (c) 2014,2019 Contributors to the Eclipse Foundation
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
# Contributors: Luca Cominardi, University Carlos III of Madrid.

import f0rce
import json
import random
import re
import threading
import traceback
import ykon
from fog05 import FIMAPI as fog05api
from uuid import uuid4,UUID




def fog05_node(info, plugins, status):
    if not all(k in info for k in ('uuid','name')):
        return None
    # Create a node
    n = f0rce.Node(uuid = UUID(info['uuid']), name = info['name'])
    # Parse the node info
    if 'accelerator' in info:
        prop = f0rce.property.Acceleration()
        for a in info['accelerator']:
            acc = f0rce.property.Accelerator(type = a['type'])
            prop.add_accelerator(prop)
        n.set_acceleration(prop)

    if 'cpu' in info:
        prop = f0rce.property.CPU()
        for t in info['cpu']:
            core = f0rce.property.Core(
                    id = len(prop.core),
                    arch = t['arch'],
                    freq = t['frequency'],
                    model = t['model'])
            prop.add_core(core)
        n.set_cpu(prop)

    if 'disks' in info:
        prop = f0rce.property.Storage()
        for t in info['disks']:
            disk = f0rce.property.Disk(
                    device = t['local_address'],
                    size = t['dimension'],
                    mountpoint = t['mount_point'],
                    filesystem = t['filesystem'])
            prop.add_disk(disk)
        n.set_storage(prop)

    if 'io' in info:
        prop = f0rce.property.IO()
        for i in info['io']:
            iodev = f0rce.property.IOdevice(type = i['type'])
            prop.add_device(iodev)
        n.set_io(prop)

    if 'network' in info:
        prop = f0rce.property.Network()
        for t in info['network']:
            intf = f0rce.property.Interface(
                    name = t['intf_name'],
                    type = f0rce.enum.InterfaceType.PHYSICAL)
            intf.mac.set_address(t['intf_mac_address'])
            if re.match('.*bridge.*', t['type'], re.IGNORECASE):
                intf.mac.set_type(f0rce.enum.InterfaceMACType.BRIDGED)
            elif re.match('.*ethernet.*', t['type'], re.IGNORECASE):
                intf.mac.set_type(f0rce.enum.InterfaceMACType.PARAVIRT)
            else:
                intf.mac.set_type(f0rce.enum.InterfaceMACType.UNKNOWN)
            intf.mac.set_speed(t['intf_speed'])
            #        available = t['available'],
            ipv4 = f0rce.property.IPv4(
                    address = t['inft_configuration']['ipv4_address'],
                    netmask = t['inft_configuration']['ipv4_netmask'],
                    default = t['default_gw'])
            intf.add_ipv4(ipv4)
            ipv6 = f0rce.property.IPv6(
                    address = t['inft_configuration']['ipv6_address'],
                    netmask = t['inft_configuration']['ipv6_netmask'],
                    default = t['default_gw'])
            intf.add_ipv6(ipv6)
            prop.add_intf(intf)
        n.set_network(prop)

    if 'ram' in info:
        prop = f0rce.property.RAM(size = info['ram']['size'])
        n.set_ram(prop)

    # Parse the node plugins
    execution = f0rce.property.Execution()
    for p in plugins:
        if p['type'] == 'os':
            prop = f0rce.property.OS(
                    name = p['name'],
                    status = p['status'],
                    version = p['version'])
            n.set_os(prop)
        elif p['type'] == 'runtime':
            runtime = f0rce.property.Runtime(
                    name = p['name'],
                    status = p['status'],
                    version = p['version'])
            execution.add_runtime(runtime)
    n.set_execution(execution)

    return n


def fog05_link(ndict, ldict):
    # Check if the link is between two valid nodes
    src_node = None
    dst_node = None
    for n in ndict.values():
        if n.name == ldict['src']['node']['name']:
            src_node = n
        elif n.name == ldict['dst']['node']['name']:
            dst_node = n

    if src_node is None or dst_node is None:
        return None

    # Check if the link is between two valid interfaces
    src_intf = None
    dst_intf = None
    if ldict['src']['port']['name'] in src_node.network.intf.keys():
        src_intf = src_node.network.intf[ldict['src']['port']['name']]
    if ldict['dst']['port']['name'] in dst_node.network.intf.keys():
        dst_intf = dst_node.network.intf[ldict['dst']['port']['name']]

    if src_intf is None or dst_intf is None:
        return None

    # Create the link uuid since it is not provided by fog05
    r = random.Random()
    src_intf_seed = 0
    for i in range(0, len(src_intf.name)):
        src_intf_seed = ord(src_intf.name[i])*(10**i)
    dst_intf_seed = 0
    for i in range(0, len(dst_intf.name)):
        dst_intf_seed = ord(dst_intf.name[i])*(10**i)
    r.seed(
            src_node.uuid.int ^ src_intf_seed ^ \
            dst_node.uuid.int ^ dst_intf_seed ^ \
            (src_node.uuid.int - dst_node.uuid.int)
        )
    uuid = UUID(int = r.getrandbits(128))

    link = f0rce.Link(
            uuid = uuid,
            src_node_uuid = src_node.uuid,
            src_intf_name = src_intf.name,
            dst_node_uuid = dst_node.uuid,
            dst_intf_name = dst_intf.name)
    return link


def fog05_entity(fdict):
    e = f0rce.Entity(UUID(fdict['uuid']), fdict['name'])
    cr = fdict['computation_requirements']
    for i in range(0, int(cr['cpu_min_count'])):
        core = f0rce.property.Core(id = len(e.requirement.cpu.core), arch = cr['cpu_arch'], freq = cr['cpu_min_freq'])
        e.requirement.cpu.add_core(core)
    e.requirement.disk.set_size(cr['storage_size_gb'])
    e.requirement.ram.set_size(cr['ram_size_mb'])
    e.requirement.runtime.set_name(fdict['hypervisor'])
    for a in fdict['io_ports']:
        pass
    for e in fdict['depends_on']:
        e.requirement.add_entity(UUID(e))

    ir = fdict['image']
    e.configuration.image.set_uri(ir['uri'])
    e.configuration.image.set_format(ir['format'])
    e.configuration.image.set_checksum(ir['checksum'])

    e.configuration.migration.set_type(fdict['migration_kind'])

    for i in fdict['interfaces']:
        intf = f0rce.property.Interface(
                name = i['name'],
                type = f0rce.enum.InterfaceType.VIRTUAL)
        intf.mac.set_address(i['mac_address'])
        intf.mac.set_bus(i['virtual_interface']['vpci'])
        intf.mac.set_speed(i['virtual_interface']['bandwidth'])
        intf.mac.set_type(f0rce.enum.InterfaceMACType[i['virtual_interface']['intf_type']])
        e.configuration.network.add_intf(intf)

    return e


def fog05_instance(node, idict):
    if 'network' not in idict['hypervisor_info']:
        return None
    if not isinstance(idict['hypervisor_info']['network'], dict):
        return None

    uuid = UUID(int = int(UUID(idict['fdu_uuid'])) ^ int(UUID(node)))
    instance = f0rce.Instance(
            uuid = uuid,
            entity = UUID(idict['fdu_uuid']),
            node = UUID(node))
    if idict['status'] == 'RUN':
        instance.set_state(f0rce.enum.InstanceState.RUNNING)
    else:
        instance.set_state(f0rce.enum.InstanceState.UNKNOWN)

    for k,v in idict['hypervisor_info']['network'].items():
        interface = f0rce.property.Interface(name = k)
        interface.mac.set_address(v['hwaddr'])
        interface.mac.set_mtu(v['mtu'])
        for a in v['addresses']:
            if a['family'] == 'inet':
                ipv4 = f0rce.property.IPv4(
                        address = a['address'],
                        netmask = a['netmask'])
                interface.add_ipv4(ipv4)
            elif a['family'] == 'inet':
                ipv6 = f0rce.property.IPv6(
                        address = a['address'],
                        netmask = a['netmask'])
                interface.add_ipv6(ipv6)
        instance.network.add_intf(interface)

    return instance


def fog05_fdu(entity, instance):
    fdu = {
        'uuid': str(entity.uuid),
        'name': entity.name,
        'computation_requirements': {
            'cpu_arch': list(entity.requirement.cpu.core.values())[0].arch,
            'cpu_min_freq': 0.0,
            'cpu_min_count': len(entity.requirement.cpu.core),
            'ram_size_mb': entity.requirement.ram.size,
            'storage_size_gb': entity.requirement.disk.size,
        },
        'image': {
            'uri': entity.configuration.image.uri,
            'checksum': entity.configuration.image.checksum,
            'format': entity.configuration.image.format
        },
        'hypervisor': entity.requirement.runtime.name,
        'migration_kind': entity.configuration.migration.type,
        'interfaces': [],
        'io_ports': [],
        'connection_points': [],
        'depends_on': []
    }
    for intf in entity.configuration.network.intf.values():
        i = {
            'name': intf.name,
            'is_mgmt': False,
            'if_type': 'EXTERNAL',
            'mac_address': intf.mac.address
#            'cp_id': ''
        }
        for jntf in instance.network.intf.values():
            i['virtual_interface'] = {
                    'intf_type': jntf.mac.type,
                    'vpci': jntf.name,
                    'bandwidth': 10
            }
        fdu['interfaces'].append(i)

    return fdu



class Fog05VIM(f0rce.VIMconnector):
    def __init__(self, endpoint, name, uuid, domain, fog05endpoint):
        super().__init__(endpoint, name, uuid, domain)
        # Store the fog05 yaks endpoint
        self._fog05endpoint = fog05endpoint
        # Connect to fog05 yaks
        self._fapi = None
        # Internal timers
        self.__timer = {}
        self.__interval = 600
        # Add handles
        self.handle.register.append(self.fog05register)
        self.handle.unregister.append(self.fog05unregister)

    # Handles begin
    def fog05register(self):
        # Connect to fog05 YAKS
        self._fapi = fog05api(self._fog05endpoint)
        self.log.info('Connected to fog05: {}'.format(self._fog05endpoint))
        # Start updating the node and links
        self.__timer['update'] = threading.Thread(target = self.__update)
        self.__timer['update'].start()

    def fog05unregister(self):
        # Stop udpate timer
        if 'update' in self.__timer:
            self.__timer['update'].cancel()
            del self.__timer['update']
        # Disconenct from fog05 YAKS
        self._fapi.close()
        self.log.info('Disconnected from fog05: {}'.format(self._fog05endpoint))
    # Handles end

    def __update(self):
        self.update()
        self.__timer['update'] = threading.Timer(self.__interval, self.__update)
        self.__timer['update'].start()

    def update(self):
        self.log.debug('< Status update from fog05')
        # Build the list of nodes from fog05
        ndict = {}
        llist = []
        nlist = self._fapi.node.list()
        for n in nlist:
            # Build the node
            info = self._fapi.node.info(n)
            plugins = []
            plist = self._fapi.node.plugins(n)
            for plugin in plist:
                p = self._fapi.plugin.info(n, plugin)
                plugins.append(p)
            status = self._fapi.node.status(n)
            node = fog05_node(info, plugins, status)
            ndict[str(node.uuid)] = node
            llist.extend(status['neighbors'])

        # Build the list of links from fog05
        ldict = {}
        for l in llist:
            # Build the link
            link = fog05_link(ndict, l)
            if link:
                ldict[str(link.uuid)] = link
            else:
                self.log.error('Invalid link from fog05')

        # Build the list of entities from fog05
        fdict = {}
        flist = self._fapi.fdu.list()
        for fdu in flist:
            try:
                f = self._fapi.fdu.info(fdu)
                fdict[fdu] = fog05_entity(f)
            except ValueError as e:
                self.log.error(e)

        # Build the list of instances from fog05
        idict = {}
        for fdu in fdict.keys():
            for linst in self._fapi.fdu.instance_list(fdu).values():
                for instuuid in linst:
                    info = self._fapi.fdu.instance_info(instuuid)
                    i = fog05_instance(n, info)
                    if i:
                        idict[str(i.uuid)] = i

        # Add or update nodes
        for n in ndict.values():
            if str(n.uuid) in self.O4network.node:
                if self.O4network.node[str(n.uuid)] != n:
                    self.O4network.upd_node(n)
            else:
                self.O4network.add_node(n)
        # Delete nodes
        for n in list(self.O4network.node.values()):
            if str(n.uuid) not in ndict:
                self.O4network.del_node(n)

        # Add or update links
        for l in ldict.values():
            if str(l.uuid) in self.O4network.link:
                if self.O4network.link[str(l.uuid)] != l:
                    self.O4network.upd_link(l)
            else:
                self.O4network.add_link(l)
        # Delete links
        for l in list(self.O4network.link.values()):
            if str(l.uuid) not in ldict:
                self.O4network.del_link(l)

        # Add or update entities
        for f in fdict.values():
            if str(f.uuid) in self.O4stack.entity:
                if self.O4stack.entity[str(f.uuid)] != f:
                    self.O4stack.upd_entity(f)
            else:
                self.O4stack.add_entity(f)
        # Delete entities
        for e in list(self.O4stack.entity.values()):
            if str(e.uuid) not in fdict:
                self.O4stack.del_entity(e)

        # Add or update instances
        for i in idict.values():
            if str(i.uuid) in self.O4stack.instance:
                if self.O4stack.instance[str(i.uuid)] != i:
                    self.O4stack.upd_instance(i)
            else:
                self.O4stack.add_instance(i)
        # Delete instances
        for i in list(self.O4stack.instance.values()):
            if str(i.uuid) not in idict:
                self.O4stack.del_instance(i)

        self.log.debug('> Status update complete')


    def O4onboard(self, entity, instance):
        try:
            if isinstance(entity, str):
                entity = f0rce.entity.build(json.loads(entity))
            elif isinstance(entity, dict):
                entity = f0rce.entity.build(entity)
            elif not isinstance(entity, f0rce.Entity):
                return {"status": "error", "description": "Invalid entity object"}

            if isinstance(instance, str):
                instance = f0rce.instance.build(json.loads(instance))
            elif isinstance(instance, dict):
                instance = f0rce.instance.build(instance)
            elif not isinstance(instance, f0rce.Instance):
                return {"status": "error", "description": "Invalid instance object"}

            self.log.info('Onboard {} on {}'.format(entity.uuid, instance.node))
            fdu = fog05_fdu(entity, instance)
            self.log.critical(fdu)
            res = self._fapi.fdu.onboard(fdu, wait = True)
            self.log.info('Fog05 says: {}'.format(res))
        except Exception as e:
            traceback.print_exc()
        return {"status": "ok", "description": "Onboarded"}


    def O4offload(self, entity, instance):
        assert isinstance(entity, f0rce.Entity)


    def O4instantiate(self, entity, instance):
        try:
            if isinstance(entity, str):
                entity = f0rce.entity.build(json.loads(entity))
            elif isinstance(entity, dict):
                entity = f0rce.entity.build(entity)
            elif not isinstance(entity, f0rce.Entity):
                return {"status": "error", "description": "Invalid entity object"}

            if isinstance(instance, str):
                instance = f0rce.instance.build(json.loads(instance))
            elif isinstance(instance, dict):
                instance = f0rce.instance.build(instance)
            elif not isinstance(instance, f0rce.Instance):
                return {"status": "error", "description": "Invalid instance object"}

            euuid = str(entity.uuid)
            nuuid = str(instance.node).replace('-', '')

            self.log.info('Instantiate {} on {}'.format(euuid, nuuid))
            res = self._fapi.fdu.instantiate(euuid, nuuid, wait = True)
            self.log.info('Fog05 says: {}'.format(res))

            #self.log.info('Define {} on {}'.format(euuid, nuuid))
            #res = self._fapi.fdu.define(euuid, nuuid, wait = True)
            #self.log.info('Fog05 says: {}'.format(res))

            #self.log.info('Configure {} on {}'.format(euuid, nuuid))
            #self._fapi.fdu.configure(euuid, nuuid, wait = True)
            #self.log.info('Fog05 says: {}'.format(res))

            #self.log.info('Run {} on {}'.format(euuid, nuuid))
            #self._fapi.fdu.run(euuid, nuuid, wait = True)
            #self.log.info('Fog05 says: {}'.format(res))
        except Exception as e:
            traceback.print_exc()
        self.log.critical('EXITING')
        return {"status": "ok", "description": "Onboarded"}



    def O4terminate(self, entity, instance):
        assert isinstance(entity, f0rce.Entity)
        assert isinstance(instance, f0rce.Instance)


# Do NOT remove
component = lambda *args, **kwargs: Fog05VIM(*args, **kwargs)
