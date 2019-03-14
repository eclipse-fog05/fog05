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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - API v2


# import re
# import uuid
# import json
# import fnmatch
# import time
from fog05.yaks_connector import Yaks_Connector
from fog05.interfaces import Constants
# from jsonschema import validate, ValidationError
# from enum import Enum
# from fog05 import Schemas
from mvar import MVar


class FIMAPIv2(object):
    '''
        This class allow the interaction with fog05 FIM
    '''

    def __init__(self, locator='127.0.0.1:7887',
                 sysid=Constants.default_system_id,
                 tenantid=Constants.default_tenant_id):

        self.connector = Yaks_Connector(locator)
        self.sysid = sysid
        self.tenantid = tenantid
        self.manifest = self.Manifest()
        self.node = self.Node(self.connector, self.sysid, self.tenantid)
        self.plugin = self.Plugin(self.connector, self.sysid, self.tenantid)
        self.network = self.Network(self.connector, self.sysid, self.tenantid)
        self.fdu = self.FDU(self.connector, self.sysid, self.tenantid)
        self.image = self.Image(self.connector, self.sysid, self.tenantid)
        self.flavor = self.Flavor(self.connector, self.sysid, self.tenantid)

    def close(self):
        self.connector.close()

    class Manifest(object):
        '''
        This class encapsulates API for manifests

        '''

        def __init__(self):
            pass

        def check(self, manifest, manifest_type):
            '''

            This method allow you to check a manifest

            :param manifest: a dictionary rapresenting the JSON manifest
            :param manifest_type: the manifest type from API.Manifest.Type
            :return: boolean
            '''
            # if manifest_type == self.Type.ENTITY:
            #     t = manifest.get('type')
            #     try:
            #         if t == 'vm':
            #             validate(manifest.get('entity_data'),
            #                      Schemas.vm_schema)
            #         elif t == 'container':
            #             validate(manifest.get('entity_data'),
            #                      Schemas.container_schema)
            #         elif t == 'native':
            #             validate(manifest.get('entity_data'),
            #                      Schemas.native_schema)
            #         elif t == 'ros2':
            #             validate(manifest.get('entity_data'),
            #                      Schemas.ros2_schema)
            #         elif t == 'usvc':
            #             return False
            #         else:
            #             return False
            #     except ValidationError as ve:
            #         return False
            # if manifest_type == self.Type.NETWORK:
            #     try:
            #         validate(manifest, Schemas.network_schema)
            #     except ValidationError as ve:
            #         return False
            # if manifest_type == self.Type.ENTITY:
            #     try:
            #         validate(manifest, Schemas.entity_schema)
            #     except ValidationError as ve:
            #         return False

            return True

        # class Type(Enum):
        #     '''
        #     Manifest types
        #     '''
        #     ENTITY = 0
        #     IMAGE = 1
        #     FLAVOR = 3
        #     NETWORK = 4
        #     PLUGIN = 5

    class Node(object):
        '''

        This class encapsulates the command for Node interaction

        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def list(self):
            '''
            Get all nodes in the current system/tenant

            :return: list of tuples (uuid, hostname)
            '''
            nodes = self.connector.glob.actual.get_all_nodes(
                self.sysid, self.tenantid)
            return nodes

        def info(self, node_uuid):
            """
            Provide all information about a specific node

            :param node_uuid: the uuid of the node you want info
            :return: a dictionary with all information about the node
            """
            if node_uuid is None:
                return None
            node_info = self.connector.glob.actual.get_node_info(
                self.sysid, self.tenantid, node_uuid)
            return node_info

        def plugins(self, node_uuid):
            '''

            Get the list of plugin installed on the specified node

            :param node_uuid: the uuid of the node you want info
            :return: a list of the plugins installed in the node with
            detailed informations

            '''
            plugins = self.connector.glob.actual.get_all_plugins_ids(
                self.sysid, self.tenantid, node_uuid)
            return plugins

        def search(self, search_dict):
            '''

            Will search for a node that match information provided
             in the parameter

            :param search_dict: dictionary contains all information to match
            :return: a list of node matching the dictionary
            '''
            pass

    class Plugin(object):
        '''
        This class encapsulates the commands for Plugin interaction

        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def add(self, manifest, node_uuid=None):
            '''

            Add a plugin to a node or to all node in the system/tenant

            :param manifest: the dictionary representing the plugin manifest
            :param node_uuid: optional the node in which add the plugin
            :return: boolean
            '''

            # manifest.update({'status': 'add'})
            # plugins = {"plugins": [manifest]}
            # plugins = json.dumps(plugins)
            # if node_uuid is None:
            #     uri = '{}/*/plugins'.format(self.store.droot)
            # else:
            #     uri = '{}/{}/plugins'.format(self.store.droot, node_uuid)

            # res = self.store.desired.dput(uri, plugins)
            # if res:
            #     return True
            # else:
            #     return False
            pass

        def remove(self, plugin_uuid, node_uuid=None):
            '''

            Will remove a plugin for a node or all nodes

            :param plugin_uuid: the plugin you want to remove
            :param node_uuid: optional the node that will remove the plugin
            :return: boolean
            '''
            pass

        def info(self, node_uuid, pluginid):
            '''

            Same as API.Node.Plugins but can work for all node un the system,
            \return a dictionary with key node uuid and value the plugin list

            :param node_uuid: can be none
            :return: dictionary {node_uuid, plugin list }
            '''
            if node_uuid is not None:
                return self.connector.glob.actual.get_plugin_info(
                    self.sysid, self.tenantid, node_uuid, pluginid)
            return None

        def search(self, search_dict, node_uuid=None):
            '''

            Will search for a plugin matching the dictionary in a
             single node or in all nodes

            :param search_dict: dictionary contains all information to match
            :param node_uuid: optional node uuid in which search
            :return: a dictionary with {node_uuid, plugin uuid list} with
             matches
            '''
            pass

    class Network(object):
        '''

        This class encapsulates the command for Network element interaction

        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def __get_all_node_plugin(self, node_uuid):
            pass
            # uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            # response = self.store.actual.resolve(uri)
            # if response is not None and response != '':
            #     return json.loads(response).get('plugins')
            # else:
            #     return None

        def add_network(self, manifest):
            '''

            Add a network element to a node o to all nodes


            :param manifest: dictionary representing the manifest of
             that network element
            :param node_uuid: optional the node uuid in which add
            the network element
            :return: boolean
            '''

            manifest.update({'status': 'add'})
            net_id = manifest.get('uuid')

            self.connector.glob.desired.add_network(
                self.sysid, self.tenantid, net_id, manifest)

        def remove_network(self, net_uuid):
            '''

            Remove a network element form one or all nodes

            :param net_uuid: uuid of the network you want to remove
            :param node_uuid: optional node from which remove
             the network element
            :return: boolean
            '''
            manifest = self.connector.glob.actual.get_network(
                self.sysid, self.tenantid, net_uuid)
            manifest.update({'status': 'remove'})
            self.connector.glob.desired.add_network(
                self.sysid, self.tenantid, net_uuid, manifest)

        def add_connection_point(self, cp_descriptor):
            cp_descriptor.update({'status': 'add'})
            cp_id = cp_descriptor.get('uuid')
            self.connector.glob.desired.add_network_port(
                self.sysid, self.tenantid, cp_id, cp_descriptor)

        def delete_connection_point(self, cp_uuid):
            manifest = self.connector.glob.actual.get_network_port(
                self.sysid, self.tenantid, cp_uuid)
            manifest.update({'status': 'remove'})
            self.connector.glob.desired.add_network_port(
                self.sysid, self.tenantid, cp_uuid, manifest)

        def connect_cp_to_network(self, cp_uuid, net_uuid):
            pass

        def disconnect_cp(self, cp_uuid):
            pass

        def list(self):
            '''

            List all network element available in the system/teneant or in a
             specified node

            :param node_uuid: optional node uuid
            :return: dictionary {network uuid:
             {network manifest dictionary, pluginid, nodes}}
            '''
            return self.connector.glob.actual.get_all_networks(
                self.sysid, self.tenantid)

        def search(self, search_dict, node_uuid=None):
            '''

            Will search for a network element matching the dictionary in a
             single node or in all nodes

            :param search_dict: dictionary contains all information to match
            :param node_uuid: optional node uuid in which search
            :return: a dictionary
            {node_uuid, network element uuid list} with matches
            '''
            pass

    class FDU(object):
        '''

        This class encapsulates the api for interaction with entities

        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def __wait_node_fdu_state_change(self, node_uuid, fdu_uuid, state):
            '''

            Function used to wait if an instance changest state
             (eg. configured -> run) or goes to error state

            :param node_uuid
            :param fdu_uuid
            :param state the new expected state

            :return dict {'status':<new status>,
                            'fdu_uuid':fdu_uuid}

            '''

            local_var = MVar()

            def cb(fdu_info):
                local_var.put(fdu_info)

            subid = self.connector.glob.actual.observe_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid, cb)

            fdu_info = local_var.get()
            es = fdu_info.get('status')
            while es.upper() not in [state, 'ERROR']:
                fdu_info = local_var.get()
                es = fdu_info.get('status')
            self.connector.glob.actual.unsubscribe(subid)
            res = {
                'fdu_uuid': fdu_uuid,
                'status': es
            }
            return res

        def __wait_fdu(self, fdu_uuid):
            '''

            Function used to wait if an instance changest state
             (eg. configured -> run) or goes to error state

            :param node_uuid
            :param fdu_uuid
            :param state the new expected state

            :return dict {'status':<new status>,
                            'fdu_uuid':fdu_uuid}

            '''

            local_var = MVar()

            def cb(fdu_info):
                local_var.put(fdu_info)

            fdu_info = self.connector.glob.actual.get_fdu_info(
                self.sysid, self.tenantid, fdu_uuid)
            while fdu_info is None:
                fdu_info = self.connector.glob.actual.get_fdu_info(
                    self.sysid, self.tenantid, fdu_uuid)
            # while fdu_info is None:
            #     fdu_info = local_var.get()
            res = {
                'fdu_uuid': fdu_uuid
            }
            return res

        def onboard(self, descriptor, wait=False):
            fduid = descriptor.get('uuid')
            res = self.connector.glob.desired.add_fdu_info(
                self.sysid, self.tenantid, fduid, descriptor)
            if wait:
                self.__wait_fdu(fduid)
            return res

        def offload(self, fdu_uuid, wait=False):
            res = self.connector.glob.desired.remove_fdu_info(
                self.sysid, self.tenantid, fdu_uuid)

        def define(self, fduid, node_uuid, wait=False):
            '''

            Defines an atomic entity in a node, this method will check
             the manifest before sending the definition to the node

            :param manifest: dictionary representing the atomic entity manifest
            :param node_uuid: destination node uuid
            :param wait: if wait that the definition is complete before
             returning
            :return: boolean
            '''
            desc = self.connector.glob.actual.get_fdu_info(
                self.sysid, self.tenantid, fduid)
            if desc is None:
                raise ValueError('FDU with this UUID not found in the catalog')

            record = {'fdu_uuid': fduid,
                      'status': 'DEFINE',
                      'interfaces': [],
                      'connection_points': []
                      }
            res = self.connector.glob.desired.add_node_fdu(
                self.sysid, self.tenantid, node_uuid, fduid, record)
            if wait:
                self.__wait_node_fdu_state_change(node_uuid, fduid, 'DEFINE')
            return res

        def undefine(self, fdu_uuid, node_uuid, wait=False):
            '''

            This method undefine an atomic entity in a node

            :param entity_uuid: atomic entity you want to undefine
            :param node_uuid: destination node
            :param wait: if wait before returning that the entity is undefined
            :return: boolean
            '''

            record = self.connector.glob.actual.get_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid
            )
            record.update({'status': 'UNDEFINE'})

            fduid = record.get('fdu_uuid')
            return self.connector.glob.desired.add_node_fdu(
                self.sysid, self.tenantid, node_uuid, fduid, record)

        def configure(self, fdu_uuid, node_uuid, wait=False):
            '''

            Configure an atomic entity, creation of the instance

            :param fdu_uuid: FDU you want to configure
            :param node_uuid: destination node
            :param instance_uuid: optional if present will use that uuid
             for the atomic entity instance otherwise will generate a new one
            :param wait: optional wait before returning
            :return: instance uuid or none in case of error
            '''
            record = self.connector.glob.actual.get_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid
            )
            record.update({'status': 'CONFIGURE'})

            res = self.connector.glob.desired.add_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid, record)
            if wait:
                self.__wait_node_fdu_state_change(
                    node_uuid, fdu_uuid, 'CONFIGURE')
            return res

        def clean(self, fdu_uuid, node_uuid, wait=False):
            '''

            Clean an atomic entity instance, this will destroy the instance

            :param entity_uuid: entity for which you want to clean an instance
            :param node_uuid: destionation node
            :param instance_uuid: instance you want to clean
            :param wait: optional wait before returning
            :return: boolean

            '''

            record = self.connector.glob.actual.get_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid
            )
            record.update({'status': 'CLEAN'})

            res = self.connector.glob.desired.add_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid, record)
            if wait:
                self.__wait_node_fdu_state_change(
                    node_uuid, fdu_uuid, 'DEFINE')
            return res

        def run(self, fdu_uuid, node_uuid, wait=False):
            '''

            Starting and atomic entity instance

            :param fdu_uuid: entity for which you want to run the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to start
            :param wait: optional wait before returning
            :return: boolean
            '''

            record = self.connector.glob.actual.get_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid
            )
            record.update({'status': 'RUN'})

            res = self.connector.glob.desired.add_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid, record)
            if wait:
                self.__wait_node_fdu_state_change(node_uuid, fdu_uuid, 'RUN')
            return res

        def stop(self, fdu_uuid, node_uuid, wait=False):
            '''

            Shutting down an atomic entity instance

            :param entity_uuid: entity for which you want to\ shutdown the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to shutdown
            :param wait: optional wait before returning
            :return: boolean
            '''

            record = self.connector.glob.actual.get_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid
            )
            record.update({'status': 'STOP'})

            res = self.connector.glob.desired.add_node_fdu(
                self.sysid, self.tenantid, node_uuid, fdu_uuid, record)
            if wait:
                self.__wait_node_fdu_state_change(
                    node_uuid, fdu_uuid, 'CONFIGURE')
            return res

        def pause(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Pause the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to pause the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to pause
            :param wait: optional wait before returning
            :return: boolean
            '''

            pass

        def resume(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Resume the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to
             resume the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to resume
            :param wait: optional wait before returning
            :return: boolean
            '''

            pass

        def migrate(self, fduid, node_uuid, destination_node_uuid, wait=False):
            '''

            Live migrate an atomic entity instance between two nodes

            The migration is issued when this command is sended,
             there is a little overhead for the copy of the base image and the disk image


            :param fduid: fdu you want to migrate
            :param node_uuid: source node
            :param destination_node_uuid: destination node
            :param wait: optional wait before returning
            :return: boolean
            '''

            record = self.connector.glob.actual.get_node_fdu(
                self.sysid, self.tenantid, node_uuid, fduid)

            src_record = record.copy()
            dst_record = record.copy()
            migr_properties = {
                'destination':destination_node_uuid,
                'source':node_uuid
            }

            src_record.update({'status': 'TAKE_OFF'})
            dst_record.update({'status':'LAND'})
            src_record.update({'migration_properties':migr_properties})
            dst_record.update({'migration_properties':migr_properties})

            self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid,
                                                destination_node_uuid,
                                                fduid, dst_record)
            self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid,
                                                node_uuid, fduid, src_record)

            if wait:
                self.__wait_node_fdu_state_change(
                    destination_node_uuid, fduid, 'RUN')
            return True


            # handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            # uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)

            # entity_info = self.store.actual.get(uri)
            # if entity_info is None:
            #     return False

            # entity_info = json.loads(entity_info)

            # entity_info_src = entity_info.copy()
            # entity_info_dst = entity_info.copy()

            # entity_info_src.update({"status": "taking_off"})
            # entity_info_src.update({"dst": destination_node_uuid})

            # entity_info_dst.update({"status": "landing"})
            # entity_info_dst.update({"dst": destination_node_uuid})

            # destination_handler = self.__get_entity_handler_by_type(destination_node_uuid, entity_info_dst.get('type'))
            # if destination_handler is None:
            #     return False

            # uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.droot, destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid)

            # res = self.store.desired.put(uri, json.dumps(entity_info_dst))
            # if res >= 0:
            #     uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            #     res_dest = self.store.desired.dput(uri, json.dumps(entity_info_src))
            #     if res_dest:
            #         if wait:
            #             self.__wait_atomic_entity_instance_state_change(destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid, 'run')
            #         return True
            #     else:
            #         print("Error on destination node")
            #         return False
            # else:
            #     print("Error on source node")
            #     return False
            pass

        def search(self, search_dict, node_uuid=None):
            pass

        def info(self, fdu_uuid):
            # uri = '{}/*/runtime/*/entity/{}/instance/**'.format(self.store.aroot, entity_uuid)
            # info = self.store.actual.getAll(uri)
            # if info is None or len(info) == 0:
            #     return {}
            # i = {}
            # for e in info:
            #     k = e[0]
            #     v = e[1]
            #     i_uuid = k.split('/')[-1]
            #     i.update({i_uuid: v})
            # return {entity_uuid: i}
            return self.connector.glob.actual.get_fdu_info(self.sysid, self.tenantid, fdu_uuid)

        def instance_info(self, fdu_uuid, node_uuid):
            return self.connector.glob.actual.get_node_fdu(self.sysid, self.tenantid, node_uuid, fdu_uuid)

        def list(self, node_uuid='*'):
            '''

            List all entity element available in the system/teneant
             or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: {entity uuid: instance list} list}
            '''

            # if node_uuid is not None:
            #     entity_list = {}
            #     uri = '{}/{}/runtime/*/entity/**'.format(self.store.aroot, node_uuid)
            #     response = self.store.actual.resolveAll(uri)
            #     for i in response:
            #         rid = i[0]
            #         en_uuid = rid.split('/')[7]
            #         if en_uuid not in entity_list:
            #             entity_list.update({en_uuid: []})
            #         if len(rid.split('/')) == 8 and en_uuid in entity_list:
            #             pass
            #         if len(rid.split('/')) == 10:
            #             entity_list.get(en_uuid).append(rid.split('/')[9])

            #     return {node_uuid: entity_list}

            # entities = {}
            # uri = '{}/*/runtime/*/entity/**'.format(self.store.aroot)
            # response = self.store.actual.resolveAll(uri)
            # for i in response:
            #     node_id = i[0].split('/')[3]
            #     elist = self.list(node_id)
            #     entities.update({node_id: elist.get(node_id)})
            # return entities
            return self.connector.glob.actual.get_node_fdus(self.sysid, self.tenantid, node_uuid)


    class Image(object):
        '''

        This class encapsulates the action on images


        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def __search_plugin_by_name(self, name, node_uuid):
            # uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            # all_plugins = self.store.actual.resolve(uri)
            # if all_plugins is None or all_plugins == '':
            #     print('Cannot get plugin')
            #     return None
            # all_plugins = json.loads(all_plugins).get('plugins')
            # search = [x for x in all_plugins if name.upper() in x.get('name').upper()]
            # if len(search) == 0:
            #     return None
            # else:
            #     return search[0]
            pass

        def __get_entity_handler_by_uuid(self, node_uuid, entity_uuid):
            # uri = '{}/{}/runtime/*/entity/{}'.format(self.store.aroot, node_uuid, entity_uuid)
            # all = self.store.actual.resolveAll(uri)
            # for i in all:
            #     k = i[0]
            #     if fnmatch.fnmatch(k, uri):
            #         # print('MATCH {0}'.format(k))
            #         # print('Extracting uuid...')
            #         regex = uri.replace('/', '\/')
            #         regex = regex.replace('*', '(.*)')
            #         reobj = re.compile(regex)
            #         mobj = reobj.match(k)
            #         uuid = mobj.group(1)
            #         # print('UUID {0}'.format(uuid))

            #         return uuid
            pass

        def __get_entity_handler_by_type(self, node_uuid, t):
            # handler = None
            # handler = self.__search_plugin_by_name(t, node_uuid)
            # if handler is None:
            #     print('type not yet supported')
            # return handler
            pass

        def add(self, descriptor):
            '''

            Adding an image to a node or to all nodes

            :param manifest: dictionary representing the manifest for the image
            :param node_uuid: optional node in which add the image
            :return: boolean
            '''
            # manifest.update({'status': 'add'})
            # json_data = json.dumps(manifest)
            # if node_uuid is None:
            #     uri = '{}/*/runtime/*/image/{}'.format(
            #         self.store.droot, manifest.get('uuid'))
            # else:
            #     handler = None
            #     t = manifest.get('type')
            #     if t in ['kvm', 'xen']:
            #         handler = self.__search_plugin_by_name(t, node_uuid)
            #     elif t in ['container', 'lxd', 'docker']:
            #         handler = self.__search_plugin_by_name(t, node_uuid)
            #     else:
            #         print('type not recognized')
            #     if handler is None or handler == 'None':
            #         print('Handler not found!! (Is none)')
            #         return False
            #     if handler.get('uuid') is None:
            #         print('Handler not found!! (Cannot get handler uuid)')
            #         return False
            #     uri = '{}/{}/runtime/{}/image/{}'.format(
            #         self.store.droot, node_uuid, handler.get('uuid'), manifest.get('uuid'))
            # res = self.store.desired.put(uri, json_data)
            # if res:
            #     return True
            # else:
            #     return False
            img_id = descriptor.get('uuid')
            return self.connector.glob.desired.add_image(self.sysid,
             self.tenantid,img_id, descriptor)

        def get(self, iamge_uuid):
            return self.connector.glob.desired.get_image(self.sysid,
             self.tenantid,iamge_uuid, descriptor)

        def remove(self, image_uuid):
            '''

            Remove an image for a node or all nodes

            :param image_uuid: image you want to remove
            :param node_uuid: optional node from which remove the image
            :return: boolean
            '''

            # if node_uuid is None:
            #     uri = '{}/*/runtime/*/image/{}#status=undefine'.format(
            #         self.store.droot, image_uuid)
            # else:
            #     uri = '{}/{}/runtime/*/image/{}#status=undefine'.format(
            #         self.store.droot, node_uuid, image_uuid)
            # res = self.store.desired.dput(uri)
            # if res:
            #     return True
            # else:
            #     return False
            return self.connector.glob.desired.remove_image(self.sysid,
             self.tenantid, image_uuid)

        def search(self, search_dict, node_uuid=None):
            pass

        def list(self):
            '''

            List available entity images

            :param node_uuid: optional node id
            :return: dictionaty {nodeid: {runtimeid: [images list]}}
            '''

            # uri = '{}/*/runtime/*/image/**'.format(self.store.aroot)
            # if node_uuid:
            #     uri = '{}/{}/runtime/*/image/**'.format(
            #         self.store.aroot, node_uuid)
            # data = self.store.actual.getAll(uri)
            # images = {}
            # for i in data:
            #     nodeid = i[0].split('/')[3]
            #     pluginid = i[0].split('/')[5]
            #     img_data = json.loads(i[1])
            #     imgs = images.get(nodeid, None)
            #     if imgs is None:
            #         images.update({nodeid: {pluginid: [img_data]}})
            #     else:
            #         if pluginid not in imgs.keys():
            #             images.update({nodeid: {pluginid: [img_data]}})
            #         else:
            #             images.get(nodeid).get(pluginid).append(img_data)
            # return images
            return self.connector.glob.actual.get_all_images(self.sysid,
             self.tenantid)

    class Flavor(object):
        '''
          This class encapsulates the action on flavors

        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def add(self, descriptor):
            '''

            Add a computing flavor to a node or all nodes

            :param manifest: dictionary representing the manifest
             for the flavor
            :param node_uuid: optional node in which add the flavor
            :return: boolean
            '''
            # manifest.update({'status': 'add'})
            # json_data = json.dumps(manifest)
            # if node_uuid is None:
            #     uri = '{}/*/runtime/*/flavor/{}'.format(
            #         self.store.droot, manifest.get('uuid'))
            # else:
            #     uri = '{}/{}/runtime/*/flavor/{}'.format(
            #         self.store.droot, node_uuid, manifest.get('uuid'))
            # res = self.store.desired.put(uri, json_data)
            # if res:
            #     return True
            # else:
            #     return False
            flv_id = descriptor.get('uuid')
            return self.connector.glob.desired.add_flavor(self.sysid,
             self.tenantid,flv_id, descriptor)

        def get(self, flavor_uuid):
            '''

            Add a computing flavor to a node or all nodes

            :param manifest: dictionary representing the manifest
             for the flavor
            :param node_uuid: optional node in which add the flavor
            :return: boolean
            '''
            # manifest.update({'status': 'add'})
            # json_data = json.dumps(manifest)
            # if node_uuid is None:
            #     uri = '{}/*/runtime/*/flavor/{}'.format(
            #         self.store.droot, manifest.get('uuid'))
            # else:
            #     uri = '{}/{}/runtime/*/flavor/{}'.format(
            #         self.store.droot, node_uuid, manifest.get('uuid'))
            # res = self.store.desired.put(uri, json_data)
            # if res:
            #     return True
            # else:
            #     return False
            return self.connector.glob.desired.get_flavor(self.sysid,
             self.tenantid,flavor_uuid, descriptor)

        def remove(self, flavor_uuid):
            '''

            Remove a flavor from all nodes or a specified node

            :param flavor_uuid: flavor to remove
            :param node_uuid: optional node from which remove the flavor
            :return: boolean
            '''
            # if node_uuid is None:
            #     uri = '{}/*/runtime/*/flavor/{}#status=undefine'.format(
            #         self.store.droot, flavor_uuid)
            # else:
            #     uri = '{}/{}/runtime/*/flavor/{}#status=undefine'.format(
            #         self.store.droot, node_uuid, flavor_uuid)
            # res = self.store.desired.dput(uri)
            # if res:
            #     return True
            # else:
            #     return False
            return self.connector.glob.desired.remove_flavor(self.sysid,
             self.tenantid, flavor_uuid)

        def list(self):
            '''

            List available entity flavors

            :param node_uuid: optional node id
            :return: dictionaty {nodeid: {runtimeid: [flavor list]}}
            '''
            # uri = '{}/*/runtime/*/flavor/**'.format(self.store.aroot)
            # if node_uuid:
            #     uri = '{}/{}/runtime/*/flavor/**'.format(
            #         self.store.aroot, node_uuid)
            # data = self.store.actual.getAll(uri)
            # flavors = {}
            # for i in data:
            #     nodeid = i[0].split('/')[3]
            #     pluginid = i[0].split('/')[5]
            #     flv_data = json.loads(i[1])
            #     flvs = flavors.get(nodeid, None)
            #     if flvs is None:
            #         flavors.update({nodeid: {pluginid: [flv_data]}})
            #     else:
            #         if pluginid not in flvs.keys():
            #             flavors.update({nodeid: {pluginid: [flv_data]}})
            #         else:
            #             flavors.get(nodeid).get(pluginid).append(flv_data)
            # return flavors
            return self.connector.glob.actual.get_all_flavors(self.sysid,
             self.tenantid)

        def search(self, search_dict, node_uuid=None):
            pass
