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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Initial implementation and API

from jsonschema import validate, ValidationError
from fog05 import Schemas
#from dstore import Store
from enum import Enum
import re
import uuid
import json
import fnmatch
import time
from yaks import api
from .store import Store


class FOSStore(object):
    """
    Helper class to interact with the Store
    """

    def __init__(self, server, aroot, droot, sroot, home):
        '''

        Initialize the Store with root and home

        :param server: the address of the YAKS server
        :param aroot: actual store root
        :param droot: desired store root
        :param home: store home also used to generate store id
        '''

        self.y = api.YAKS(server)

        self.aroot = aroot  # '//dfos/{}'
        self.ahome = '{}/{}'.format(aroot, home)

        self.droot = droot  # '//dfos/{}'
        self.dhome = '{}/{}'.format(droot, home)

        self.sroot = sroot
        self.shome = '{}/{}'.format(sroot, home)

        self.actual = Store(self.y, self.aroot, self.ahome, 1024)
        self.desired = Store(self.y, self.droot, self.dhome, 1024)
        self.system = Store(self.y,  self.sroot, self.shome, 1024)

    def close(self):
        '''
        Close the store

        :return: None
        '''
        self.actual.close()
        self.desired.close()
        self.system.close()


class API(object):
    '''
        This class allow the interaction with fog05 using simple Python3 API
        Need the distributed store
    '''

    def __init__(self, sysid=0, store_id="python-api", endpoint='127.0.0.1'):

        self.a_root = '//afos/{}'.format(sysid)
        self.d_root = '//dfos/{}'.format(sysid)
        self.s_root = '//sfos/{}'.format(sysid)
        self.store = FOSStore(endpoint, self.a_root, self.d_root, self.s_root, store_id)
        self.endpoint = endpoint
        self.manifest = self.Manifest(self.store)
        self.node = self.Node(self.store)
        self.plugin = self.Plugin(self.store)
        self.network = self.Network(self.store)
        self.entity = self.Entity(self.store)
        self.image = self.Image(self.store)
        self.flavor = self.Flavor(self.store)
        self.onboard = self.add
        self.offload = self.remove

    def close(self):
        self.store.close()

    def add(self, manifest):
        manifest.update({'status': 'define'})
        nodes = self.node.list()

        for n in nodes:
            u = n[0]
            uri = "{}/{}/onboard/{}".format(self.d_root, u, manifest.get('uuid'))
            value = json.dumps(manifest)
            self.store.desired.put(uri, value)

        instances_uuids = {}
        networks_uuid = []

        try:
            validate(manifest, Schemas.entity_schema)
        except ValidationError as ve:
            print(ve.message)
            exit(-1)
        nws = manifest.get('networks')
        # print('networks: {}'.format(nws))
        for n in nws:
            if n.get('nodes') is None:
                print('I will create network in all nodes')
                for node in nodes:
                    res = self.network.add(manifest=n, node_uuid=node[0])
                    if not res:
                        raise Exception('Error on define network {} -> {} on {}  (RES={})'.format(n.get('uuid'), manifest.get('uuid'), node[0], res))
            else:
                net_nodes = n.get('nodes')
                print('I will create network on {}'.format(net_nodes))
                for netn in net_nodes:
                    res = self.network.add(manifest=n, node_uuid=netn)
                    if not res:
                        raise Exception('Error on define network {} -> {} on {}  (RES={})'.format(n.get('uuid'), manifest.get('uuid'), netn, res))

            networks_uuid.append(n.get('uuid'))
        c_list = self.resolve_dependencies(manifest.get('components'))
        for c in c_list:
            search = [x for x in manifest.get("components") if x.get('name') == c]
            if len(search) > 0:
                component = search[0]
                # print('Onboarding: {}'.format(component))
                mf = component.get('manifest')
                res = self.entity.define(manifest=mf, node_uuid=component.get('node'), wait=True)
                # print(res)
                if not res:
                    raise Exception('Error on define entity {} -> {} on {}   (RES={})'.format(manifest.get('uuid'), mf.get('uuid'), component.get('node'), res))
                c_i_uuid = '{}'.format(uuid.uuid4())
                res = self.entity.configure(mf.get('uuid'), component.get('node'), instance_uuid=c_i_uuid, wait=True)
                # print(res)
                if not res:
                    raise Exception('Error on define entity {} -> {} on {}   (RES={})'.format(manifest.get('uuid'), mf.get('uuid'), component.get('node'), res))
                res = self.entity.run(mf.get('uuid'), component.get('node'), instance_uuid=c_i_uuid, wait=True)
                # print(res)
                if not res:
                    raise Exception('Error on define entity {} -> {} on {}   (RES={})'.format(manifest.get('uuid'), mf.get('uuid'), component.get('node'), res))
                instances_uuids.update({mf.get('uuid'): c_i_uuid})

        return {'entity': {manifest.get('uuid'): instances_uuids}, 'networks': networks_uuid}

    def remove(self, entity_uuid):
        nodes = self.node.list()
        if len(nodes) > 0:
            uri = "{}/*/onboard/{}".format(self.a_root, entity_uuid)
            data = self.store.actual.resolve(uri)
            entities = self.entity.list()  # {node uuid: {entity uuid: [instance list]} list}
            # print('entities {}'.format(entities))
            if data is not None and len(data) > 0:
                data = json.loads(data)
                # print('Data {}'.format(data))
                for c in data.get('components'):
                    # print('C {}'.format(c))
                    eid = c.get('manifest').get('uuid')
                    # print('eid {}'.format(eid))
                    for nid in entities:
                        # print('entities.get(nid) {}'.format(entities.get(nid)))
                        if eid in entities.get(nid):
                            instances = entities.get(nid).get(eid)
                            # print('instances {}'.format(instances))
                            for inst in instances:
                                #print('I should stop {} -> {} -> {}'.format(inst,eid, nid))
                                self.entity.stop(eid, nid, inst, wait=True)
                                # print('I should clean {} -> {} -> {}'.format(inst, eid, nid))
                                self.entity.clean(eid, nid, inst, wait=True)
                            # print('I should undefine {} -> {}'.format(eid, nid))
                            self.entity.undefine(eid, nid, wait=True)
                for n in data.get('networks'):
                    for nid in entities:
                        net_id = n.get('uuid')
                        self.network.remove(net_id, nid)
                for n in nodes:
                    u = n[0]
                    uri = "{}/{}/onboard/{}".format(self.d_root, u, entity_uuid)
                    # print('I should remove {}'.format(uri))
                    self.store.desired.remove(uri)

    def resolve_dependencies(self, components):
        '''
        The return list contains component's name in the order that can be used to deploy
         @TODO: should use less cycle to do this job
        :rtype: list
        :param components: list like [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]

        no_dependable_components -> list like [[{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}], [{'name': 'c3', 'need': []}], [{'name': 'c2', 'need': []}], [{'name': 'c1', 'need': []}], []]
        :return: list like ['c4', 'c5', 'c3', 'c2', 'c1']
        '''
        c = list(components)
        no_dependable_components = []
        for i in range(0, len(components)):
            no_dependable_components.append([x for x in c if len(x.get('need')) == 0])
            # print (no_dependable_components)
            c = [x for x in c if x not in no_dependable_components[i]]
            for y in c:
                n = y.get('need')
                n = [x for x in n if x not in [z.get('name') for z in no_dependable_components[i]]]
                y.update({"need": n})

        order = []
        for i in range(0, len(no_dependable_components)):
            n = [x.get('name') for x in no_dependable_components[i]]
            order.extend(n)
        return order

    class Manifest(object):
        '''
        This class encapsulates API for manifests

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def check(self, manifest, manifest_type):
            '''

            This method allow you to check if a manifest is write in the correct way


            :param manifest: a dictionary rapresenting the JSON manifest
            :param manifest_type: the manifest type from API.Manifest.Type
            :return: boolean
            '''
            if manifest_type == self.Type.ENTITY:
                t = manifest.get('type')
                try:
                    if t == 'vm':
                        validate(manifest.get('entity_data'), Schemas.vm_schema)
                    elif t == 'container':
                        validate(manifest.get('entity_data'), Schemas.container_schema)
                    elif t == 'native':
                        validate(manifest.get('entity_data'), Schemas.native_schema)
                    elif t == 'ros2':
                        validate(manifest.get('entity_data'), Schemas.ros2_schema)
                    elif t == 'usvc':
                        return False
                    else:
                        return False
                except ValidationError as ve:
                    return False
            if manifest_type == self.Type.NETWORK:
                try:
                    validate(manifest, Schemas.network_schema)
                except ValidationError as ve:
                    return False
            if manifest_type == self.Type.ENTITY:
                try:
                    validate(manifest, Schemas.entity_schema)
                except ValidationError as ve:
                    return False

            return True

        class Type(Enum):
            '''
            Manifest types
            '''
            ENTITY = 0
            IMAGE = 1
            FLAVOR = 3
            NETWORK = 4
            PLUGIN = 5

    class Node(object):
        '''

        This class encapsulates the command for Node interaction

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def list(self):
            '''
            Get all nodes in the current system/tenant

            :return: list of tuples (uuid, hostname)
            '''
            nodes = []
            uri = '{}/*'.format(self.store.aroot)
            infos = self.store.actual.resolveAll(uri)
            for i in infos:
                node_info = json.loads(i[1])
                nodes.append((node_info.get('uuid'), node_info.get('name')))
            return nodes

        def info(self, node_uuid):
            """
            Provide all information about a specific node

            :param node_uuid: the uuid of the node you want info
            :return: a dictionary with all information about the node
            """
            if node_uuid is None:
                return None
            uri = '{}/{}'.format(self.store.aroot, node_uuid)
            infos = self.store.actual.resolve(uri)
            if infos is None:
                return None
            return json.loads(infos)

        def plugins(self, node_uuid):
            '''

            Get the list of plugin installed on the specified node

            :param node_uuid: the uuid of the node you want info
            :return: a list of the plugins installed in the node with detailed informations
            '''
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            response = self.store.actual.get(uri)
            if response is not None:
                return json.loads(response).get('plugins')
            else:
                return None

        def search(self, search_dict):
            '''

            Will search for a node that match information provided in the parameter

            :param search_dict: dictionary contains all information to match
            :return: a list of node matching the dictionary
            '''
            pass

    class Plugin(object):
        '''
        This class encapsulates the commands for Plugin interaction

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            '''

            Add a plugin to a node or to all node in the system/tenant

            :param manifest: the dictionary representing the plugin manifest
            :param node_uuid: optional the node in which add the plugin
            :return: boolean
            '''

            manifest.update({'status': 'add'})
            plugins = {"plugins": [manifest]}
            plugins = json.dumps(plugins)
            if node_uuid is None:
                uri = '{}/*/plugins'.format(self.store.droot)
            else:
                uri = '{}/{}/plugins'.format(self.store.droot, node_uuid)

            res = self.store.desired.dput(uri, plugins)
            if res:
                return True
            else:
                return False

        def remove(self, plugin_uuid, node_uuid=None):
            '''

            Will remove a plugin for a node or all nodes

            :param plugin_uuid: the plugin you want to remove
            :param node_uuid: optional the node that will remove the plugin
            :return: boolean
            '''
            pass

        def list(self, node_uuid=None):
            '''

            Same as API.Node.Plugins but can work for all node un the system, return a dictionary with key node uuid and value the plugin list

            :param node_uuid: can be none
            :return: dictionary {node_uuid, plugin list }
            '''
            if node_uuid is not None:

                uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
                response = self.store.actual.get(uri)
                if response is not None:
                    return {node_uuid: json.loads(response).get('plugins')}
                else:
                    return None

            plugins = {}
            uri = '{}/*/plugins'.format(self.store.aroot)
            response = self.store.actual.resolveAll(uri)
            for i in response:
                id = i[0].split('/')[2]
                pl = json.loads(i[1]).get('plugins')
                plugins.update({id: pl})
            return plugins

        def search(self, search_dict, node_uuid=None):
            '''

            Will search for a plugin matching the dictionary in a single node or in all nodes

            :param search_dict: dictionary contains all information to match
            :param node_uuid: optional node uuid in which search
            :return: a dictionary with {node_uuid, plugin uuid list} with matches
            '''
            pass

    class Network(object):
        '''

        This class encapsulates the command for Network element interaction

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def __get_all_node_plugin(self, node_uuid):
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            response = self.store.actual.resolve(uri)
            if response is not None and response != '':
                return json.loads(response).get('plugins')
            else:
                return None

        def add(self, manifest, node_uuid=None):
            '''

            Add a network element to a node o to all nodes


            :param manifest: dictionary representing the manifest of that network element
            :param node_uuid: optional the node uuid in which add the network element
            :return: boolean
            '''

            manifest.update({'status': 'add'})
            json_data = json.dumps(manifest)

            if node_uuid is not None:
                all_plugins = self.__get_all_node_plugin(node_uuid)
                if all_plugins is None:
                    print('Error on receive plugin from node')
                    return False
                nws = [x for x in all_plugins if x.get('type') == 'network']
                if len(nws) == 0:
                    print('No network plugin loaded on node, aborting')
                    return False
                brctl = nws[0].get('uuid')  # will use the first plugin
                uri = '{}/{}/network/{}/networks/{}'.format(self.store.droot, node_uuid, brctl, manifest.get('uuid'))
            else:
                uri = '{}/*/network/*/networks/{}'.format(self.store.droot, manifest.get('uuid'))

            res = self.store.desired.put(uri, json_data)
            if res >= 0:
                return True
            else:
                return False

        def remove(self, net_uuid, node_uuid=None):
            '''

            Remove a network element form one or all nodes

            :param net_uuid: uuid of the network you want to remove
            :param node_uuid: optional node from which remove the network element
            :return: boolean
            '''

            if node_uuid is not None:
                all_plugins = self.__get_all_node_plugin(node_uuid)
                if all_plugins is None:
                    print('Error on receive plugin from node')
                    return False
                nws = [x for x in all_plugins if x.get('type') == 'network']
                if len(nws) == 0:
                    print('No network plugin loaded on node, aborting')
                    return False
                brctl = nws[0]  # will use the first plugin
                uri = '{}/{}/network/{}/networks/{}#status=undefine'.format(self.store.droot, node_uuid, brctl.get('uuid'), net_uuid)
            else:
                uri = '{}/*/network/*/networks/{}#status=undefine'.format(self.store.droot, net_uuid)

            res = self.store.desired.dput(uri)
            if res:
                return True
            else:
                return False

        def list(self, node_uuid=None):
            '''

            List all network element available in the system/teneant or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {network uuid: {network manifest dictionary, pluginid, nodes}}
            '''

            if node_uuid is not None:
                n_list = []
                uri = '{}/{}/network/*/networks/**'.format(self.store.aroot, node_uuid)
                response = self.store.actual.resolveAll(uri)
                for i in response:
                    n_list.append(json.loads(i[1]))
                return {node_uuid: n_list}

            nets = {}
            uri = '{}/*/network/*/networks/**'.format(self.store.aroot)
            response = self.store.actual.resolveAll(uri)
            for i in response:
                nodeid = i[0].split('/')[4]
                pluginid = i[0].split('/')[6]
                netid = i[0].split('/')[-1]
                net = nets.get(netid, None)
                if net is None:
                    net = json.loads(i[1])
                    net.update({'plugin': pluginid,
                                'nodes': [nodeid]})
                    nets.update({netid: net})
                else:
                    net.get('nodes').append(nodeid)

            return nets

        def search(self, search_dict, node_uuid=None):
            '''

            Will search for a network element matching the dictionary in a single node or in all nodes

            :param search_dict: dictionary contains all information to match
            :param node_uuid: optional node uuid in which search
            :return: a dictionary with {node_uuid, network element uuid list} with matches
            '''
            pass

    class Entity(object):
        '''

        This class encapsulates the api for interaction with entities

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def __search_plugin_by_name(self, name, node_uuid):
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            all_plugins = self.store.actual.resolve(uri)
            if all_plugins is None or all_plugins == '':
                print('Cannot get plugin')
                return None
            all_plugins = json.loads(all_plugins).get('plugins')
            search = [x for x in all_plugins if name.upper() in x.get('name').upper()]
            if len(search) == 0:
                return None
            else:
                return search[0]

        def __get_entity_handler_by_uuid(self, node_uuid, entity_uuid):
            uri = '{}/{}/runtime/*/entity/{}'.format(self.store.aroot, node_uuid, entity_uuid)
            all = self.store.actual.resolveAll(uri)
            for i in all:
                k = i[0]
                if fnmatch.fnmatch(k, uri):
                    # print('MATCH {0}'.format(k))
                    # print('Extracting uuid...')
                    regex = uri.replace('/', '\/')
                    regex = regex.replace('*', '(.*)')
                    reobj = re.compile(regex)
                    mobj = reobj.match(k)
                    uuid = mobj.group(1)
                    # print('UUID {0}'.format(uuid))

                    return uuid

        def __get_entity_handler_by_type(self, node_uuid, t):
            handler = None
            handler = self.__search_plugin_by_name(t, node_uuid)
            if handler is None:
                print('type not yet supported')
            return handler

        def __wait_atomic_entity_state_change(self, node_uuid, handler_uuid, entity_uuid, state):
            while True:
                time.sleep(0.5)
                uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.aroot, node_uuid, handler_uuid, entity_uuid)
                data = self.store.actual.get(uri)
                if data is not None:
                    entity_info = json.loads(data)
                    if entity_info is not None and entity_info.get('status') == state:
                        return

        def __wait_atomic_entity_instance_state_change(self, node_uuid, handler_uuid, entity_uuid, instance_uuid, state):
            while True:
                time.sleep(0.5)
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler_uuid, entity_uuid, instance_uuid)
                data = self.store.actual.get(uri)
                if data is not None:
                    entity_info = json.loads(data)
                    if entity_info is not None and entity_info.get('status') == state:
                        return

        def define(self, manifest, node_uuid, wait=False):
            '''

            Defines an atomic entity in a node, this method will check the manifest before sending the definition to the node

            :param manifest: dictionary representing the atomic entity manifest
            :param node_uuid: destination node uuid
            :param wait: if wait that the definition is complete before returning
            :return: boolean
            '''

            manifest.update({'status': 'define'})
            handler = None
            t = manifest.get('type')
            try:
                if t in ['kvm', 'xen']:
                    handler = self.__search_plugin_by_name(t, node_uuid)
                    validate(manifest.get('entity_data'), Schemas.vm_schema)
                elif t in ['container', 'lxd','dock']:
                    handler = self.__search_plugin_by_name(t, node_uuid)
                    validate(manifest.get('entity_data'), Schemas.container_schema)
                elif t == 'native':
                    handler = self.__search_plugin_by_name('native', node_uuid)
                    validate(manifest.get('entity_data'), Schemas.native_schema)
                elif t == 'ros2':
                    handler = self.__search_plugin_by_name('ros2', node_uuid)
                    validate(manifest.get('entity_data'), Schemas.ros2_schema)
                elif t == 'usvc':
                    print('microservice not yet')
                else:
                    print('type not recognized')

                if handler is None or handler == 'None':
                    print('Handler not found!! (Is none)')
                    return False
            except ValidationError as ve:
                print('Validation error: {}'.format(ve.message))
                return False

            if handler.get('uuid') is None:
                print('Handler not found!! (Cannot get handler uuid)')
                return False

            entity_uuid = manifest.get('uuid')
            entity_definition = manifest
            json_data = json.dumps(entity_definition)
            uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.droot, node_uuid, handler.get('uuid'), entity_uuid)

            res = self.store.desired.put(uri, json_data)
            # print('RES is {}'.format(res))
            if res >= 0:
                if wait:
                    self.__wait_atomic_entity_state_change(node_uuid, handler.get('uuid'), entity_uuid, 'defined')
                return True
            else:
                return False

        def undefine(self, entity_uuid, node_uuid, wait=False):
            '''

            This method undefine an atomic entity in a node

            :param entity_uuid: atomic entity you want to undefine
            :param node_uuid: destination node
            :param wait: if wait before returning that the entity is undefined
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}#status=undefine'.format(self.store.droot, node_uuid, handler, entity_uuid)
            res = self.store.desired.dput(uri)
            return True
            # if res >= 0:
            #     return True
            # else:
            #     return False

        def configure(self, entity_uuid, node_uuid, instance_uuid=None, wait=False):
            '''

            Configure an atomic entity, creation of the instance

            :param entity_uuid: entity you want to configure
            :param node_uuid: destination node
            :param instance_uuid: optional if present will use that uuid for the atomic entity instance otherwise will generate a new one
            :param wait: optional wait before returning
            :return: instance uuid or none in case of error
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            if instance_uuid is None:
                instance_uuid = '{}'.format(uuid.uuid4())

            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            # print('RES is {}'.format(res))
            if res >= 0:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'configured')
                return instance_uuid
            else:
                return None

        def clean(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Clean an atomic entity instance, this will destroy the instance

            :param entity_uuid: entity for which you want to clean an instance
            :param node_uuid: destionation node
            :param instance_uuid: instance you want to clean
            :param wait: optional wait before returning
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=clean'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            # if res >= 0:
            #     return True
            # else:
            #     return False
            return True

        def run(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Starting and atomic entity instance

            :param entity_uuid: entity for which you want to run the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to start
            :param wait: optional wait before returning
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            # print('RES is {}'.format(res))
            if res >= 0:
                if wait:
                    state = "run"
                    while True:
                        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                        data = self.store.actual.get(uri)
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None:
                                if entity_info.get('status') == state:
                                    break
                return True
            else:
                return False

        def stop(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Shutting down an atomic entity instance

            :param entity_uuid: entity for which you want to shutdown the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to shutdown
            :param wait: optional wait before returning
            :return: boolean
            '''

            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=stop'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res >= 0:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'stop')
                return True
            else:
                return False

        def pause(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Pause the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to pause the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to pause
            :param wait: optional wait before returning
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=pause'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res >= 0:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'pause')
                return True
            else:
                return False

        def resume(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Resume the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to resume the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to resume
            :param wait: optional wait before returning
            :return: boolean
            '''

            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=resume'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res >= 0:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'run')
                return True
            else:
                return False

        def migrate(self, entity_uuid, instance_uuid, node_uuid, destination_node_uuid, wait=False):
            '''

            Live migrate an atomic entity instance between two nodes

            The migration is issued when this command is sended, there is a little overhead for the copy of the base image and the disk image


            :param entity_uuid: entity for which you want to migrate the instance
            :param instance_uuid: instance you want to migrate
            :param node_uuid: source node for the instance
            :param destination_node_uuid: destination node for the instance
            :param wait: optional wait before returning
            :return: boolean
            '''

            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)

            entity_info = self.store.actual.get(uri)
            if entity_info is None:
                return False

            entity_info = json.loads(entity_info)

            entity_info_src = entity_info.copy()
            entity_info_dst = entity_info.copy()

            entity_info_src.update({"status": "taking_off"})
            entity_info_src.update({"dst": destination_node_uuid})

            entity_info_dst.update({"status": "landing"})
            entity_info_dst.update({"dst": destination_node_uuid})

            destination_handler = self.__get_entity_handler_by_type(destination_node_uuid, entity_info_dst.get('type'))
            if destination_handler is None:
                return False

            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.droot, destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid)

            res = self.store.desired.put(uri, json.dumps(entity_info_dst))
            if res >= 0:
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
                res_dest = self.store.desired.dput(uri, json.dumps(entity_info_src))
                if res_dest:
                    if wait:
                        self.__wait_atomic_entity_instance_state_change(destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid, 'run')
                    return True
                else:
                    print("Error on destination node")
                    return False
            else:
                print("Error on source node")
                return False

        def search(self, search_dict, node_uuid=None):
            pass

        def info(self, entity_uuid):
            uri = '{}/*/runtime/*/entity/{}/instance/**'.format(self.store.aroot, entity_uuid)
            info = self.store.actual.getAll(uri)
            if info is None or len(info) == 0:
                return {}
            i = {}
            for e in info:
                k = e[0]
                v = e[1]
                i_uuid = k.split('/')[-1]
                i.update({i_uuid: v})
            return {entity_uuid: i}

        def instance_info(self, entity_uuid, instance_uuid):
            uri = '{}/*/runtime/*/entity/{}/instance/{}'.format(self.store.aroot, entity_uuid, instance_uuid)
            info = self.store.actual.get(uri)
            if info is None or len(info) == 0:
                return {}
            return json.loads(info)

        def instances(self, entity_uuid):
            uri = '{}/*/runtime/*/entity/{}/instance/**'.format(self.store.aroot, entity_uuid)
            info = self.store.actual.getAll(uri)
            if info is None:
                return None
            i = []
            for e in info:
                i.append(e[0].split('/')[-1])
            return i

        def list(self, node_uuid=None):
            '''

            List all entity element available in the system/teneant or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: {entity uuid: instance list} list}
            '''

            if node_uuid is not None:
                entity_list = {}
                uri = '{}/{}/runtime/*/entity/**'.format(self.store.aroot, node_uuid)
                response = self.store.actual.resolveAll(uri)
                for i in response:
                    rid = i[0]
                    en_uuid = rid.split('/')[8]
                    if en_uuid not in entity_list:
                        entity_list.update({en_uuid: []})
                    if len(rid.split('/')) == 9 and en_uuid in entity_list:
                        pass
                    if len(rid.split('/')) == 11:
                        entity_list.get(en_uuid).append(rid.split('/')[10])

                return {node_uuid: entity_list}

            entities = {}
            uri = '{}/*/runtime/*/entity/**'.format(self.store.aroot)
            response = self.store.actual.resolveAll(uri)
            for i in response:
                node_id = i[0].split('/')[4]
                elist = self.list(node_id)
                entities.update({node_id: elist.get(node_id)})
            return entities

    class Image(object):
        '''

        This class encapsulates the action on images


        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def __search_plugin_by_name(self, name, node_uuid):
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            all_plugins = self.store.actual.resolve(uri)
            if all_plugins is None or all_plugins == '':
                print('Cannot get plugin')
                return None
            all_plugins = json.loads(all_plugins).get('plugins')
            search = [x for x in all_plugins if name.upper() in x.get('name').upper()]
            if len(search) == 0:
                return None
            else:
                return search[0]

        def __get_entity_handler_by_uuid(self, node_uuid, entity_uuid):
            uri = '{}/{}/runtime/*/entity/{}'.format(self.store.aroot, node_uuid, entity_uuid)
            all = self.store.actual.resolveAll(uri)
            for i in all:
                k = i[0]
                if fnmatch.fnmatch(k, uri):
                    # print('MATCH {0}'.format(k))
                    # print('Extracting uuid...')
                    regex = uri.replace('/', '\/')
                    regex = regex.replace('*', '(.*)')
                    reobj = re.compile(regex)
                    mobj = reobj.match(k)
                    uuid = mobj.group(1)
                    # print('UUID {0}'.format(uuid))

                    return uuid

        def __get_entity_handler_by_type(self, node_uuid, t):
            handler = None
            handler = self.__search_plugin_by_name(t, node_uuid)
            if handler is None:
                print('type not yet supported')
            return handler
        
        
        def add(self, manifest, node_uuid=None):
            '''

            Adding an image to a node or to all nodes

            :param manifest: dictionary representing the manifest for the image
            :param node_uuid: optional node in which add the image
            :return: boolean
            '''
            manifest.update({'status': 'add'})
            json_data = json.dumps(manifest)
            if node_uuid is None:
                uri = '{}/*/runtime/*/image/{}'.format(self.store.droot, manifest.get('uuid'))
            else:
                handler = None
                t = manifest.get('type')
                if t in ['kvm', 'xen']:
                    handler = self.__search_plugin_by_name(t, node_uuid)
                elif t in ['container', 'lxd', 'dock']:
                    handler = self.__search_plugin_by_name(t, node_uuid)
                else:
                    print('type not recognized')
                if handler is None or handler == 'None':
                    print('Handler not found!! (Is none)')
                    return False
                if handler.get('uuid') is None:
                    print('Handler not found!! (Cannot get handler uuid)')
                    return False
                uri = '{}/{}/runtime/{}/image/{}'.format(self.store.droot, node_uuid, handler.get('uuid'),manifest.get('uuid'))
            res = self.store.desired.put(uri, json_data)
            if res:
                return True
            else:
                return False

        def remove(self, image_uuid, node_uuid=None):
            '''

            Remove an image for a node or all nodes

            :param image_uuid: image you want to remove
            :param node_uuid: optional node from which remove the image
            :return: boolean
            '''

            if node_uuid is None:
                uri = '{}/*/runtime/*/image/{}#status=undefine'.format(self.store.droot, image_uuid)
            else:
                uri = '{}/{}/runtime/*/image/{}#status=undefine'.format(self.store.droot, node_uuid, image_uuid)
            res = self.store.desired.dput(uri)
            if res:
                return True
            else:
                return False

        def search(self, search_dict, node_uuid=None):
            pass

        def list(self, node_uuid=None):
            '''

            List available entity images

            :param node_uuid: optional node id
            :return: dictionaty {nodeid: {runtimeid: [images list]}}
            '''

            uri = '{}/*/runtime/*/image/**'.format(self.store.aroot)
            if node_uuid:
                uri = '{}/{}/runtime/*/image/**'.format(self.store.aroot, node_uuid)
            data = self.store.actual.getAll(uri)
            images = {}
            for i in data:
                nodeid = i[0].split('/')[4]
                pluginid = i[0].split('/')[6]
                img_data = json.loads(i[1])
                imgs = images.get(nodeid, None)
                if imgs is None:
                    images.update({nodeid: {pluginid: [img_data]}})
                else:
                    if pluginid not in imgs.keys():
                        images.update({nodeid: {pluginid: [img_data]}})
                    else:
                        images.get(nodeid).get(pluginid).append(img_data)
            return images

    class Flavor(object):
        '''
          This class encapsulates the action on flavors

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            '''

            Add a computing flavor to a node or all nodes

            :param manifest: dictionary representing the manifest for the flavor
            :param node_uuid: optional node in which add the flavor
            :return: boolean
            '''
            manifest.update({'status': 'add'})
            json_data = json.dumps(manifest)
            if node_uuid is None:
                uri = '{}/*/runtime/*/flavor/{}'.format(self.store.droot, manifest.get('uuid'))
            else:
                uri = '{}/{}/runtime/*/flavor/{}'.format(self.store.droot, node_uuid, manifest.get('uuid'))
            res = self.store.desired.put(uri, json_data)
            if res:
                return True
            else:
                return False

        def remove(self, flavor_uuid, node_uuid=None):
            '''

            Remove a flavor from all nodes or a specified node

            :param flavor_uuid: flavor to remove
            :param node_uuid: optional node from which remove the flavor
            :return: boolean
            '''
            if node_uuid is None:
                uri = '{}/*/runtime/*/flavor/{}#status=undefine'.format(self.store.droot, flavor_uuid)
            else:
                uri = '{}/{}/runtime/*/flavor/{}#status=undefine'.format(self.store.droot, node_uuid, flavor_uuid)
            res = self.store.desired.dput(uri)
            if res:
                return True
            else:
                return False

        def list(self, node_uuid=None):
            '''

            List available entity flavors

            :param node_uuid: optional node id
            :return: dictionaty {nodeid: {runtimeid: [flavor list]}}
            '''
            uri = '{}/*/runtime/*/flavor/**'.format(self.store.aroot)
            if node_uuid:
                uri = '{}/{}/runtime/*/flavor/**'.format(self.store.aroot, node_uuid)
            data = self.store.actual.getAll(uri)
            flavors = {}
            for i in data:
                nodeid = i[0].split('/')[4]
                pluginid = i[0].split('/')[6]
                flv_data = json.loads(i[1])
                flvs = flavors.get(nodeid, None)
                if flvs is None:
                    flavors.update({nodeid: {pluginid: [flv_data]}})
                else:
                    if pluginid not in flvs.keys():
                        flavors.update({nodeid: {pluginid: [flv_data]}})
                    else:
                        flavors.get(nodeid).get(pluginid).append(flv_data)
            return flavors

        def search(self, search_dict, node_uuid=None):
            pass

    '''
    Methods

    - manifest
        -check
    - node
        - list
        - info
        - plugins
        - search
    - plugin
        - add
        - remove
        - info
        - list
        - search
    - network
        - add
        - remove
        - list
        - search
    - entity
        - add
        - remove
        - define
        - undefine
        - configure
        - clean
        - run
        - stop
        - pause
        - resume
        - migrate
        - search
        - list
    - images
        - add
        - remove 
        - search
        - list
    - flavor
        - list
        - add
        - remove
        - search


    '''
