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

import uuid
import random
from fog05.yaks_connector import Yaks_Connector
from fog05.interfaces import Constants

from fog05.interfaces.FDU import FDU
from fog05.interfaces.InfraFDU import InfraFDU
from mvar import MVar
import time

class FIMAPI(object):
    '''
        This class allow the interaction with fog05 FIM
    '''

    def __init__(self, locator='127.0.0.1:7447',
                 sysid=Constants.default_system_id,
                 tenantid=Constants.default_tenant_id):

        self.connector = Yaks_Connector(locator)
        self.sysid = sysid
        self.tenantid = tenantid
        self.manifest = self.Manifest()
        self.node = self.Node(self.connector, self.sysid, self.tenantid)
        self.plugin = self.Plugin(self.connector, self.sysid, self.tenantid)
        self.network = self.Network(self.connector, self.sysid, self.tenantid)
        self.fdu = self.FDUAPI(self.connector, self.sysid, self.tenantid)
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

        def status(self, node_uuid):
            """
            Provide all status information about a specific node,
            including network neighbors

            :param node_uuid: the uuid of the node you want info
            :return: a dictionary with all information about the node
            """
            if node_uuid is None:
                return None
            node_status = self.connector.glob.actual.get_node_status(
                self.sysid, self.tenantid, node_uuid)
            return node_status

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
            if manifest is None:
                return
            manifest.update({'status': 'remove'})
            self.connector.glob.desired.remove_network(
                self.sysid, self.tenantid, net_uuid)

        def add_network_to_node(self, manifest, nodeid):
            net_id = manifest.get('uuid')
            net = self.connector.glob.actual.get_node_network(self.sysid, self.tenantid, nodeid, net_id)
            if net is not None:
                return net
            res = self.connector.glob.actual.create_network_in_node(self.sysid, self.tenantid, nodeid, manifest)
            if res.get('error') is not None:
                raise ValueError('Got Error {}'.format(res['error']))
            return res['result']

        def remove_network_from_node(self, netid, nodeid):
            res = self.connector.glob.actual.remove_network_from_node(self.sysid, self.tenantid, nodeid, netid)
            if res.get('error') is not None:
                raise ValueError('Got Error {}'.format(res['error']))
            return res['result']


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
            ports = self.connector.glob.actual.get_all_nodes_network_ports(self.sysid, self.tenantid)
            node = None
            port_info = None
            for p in ports:
                n, pid = p
                if pid == cp_uuid:
                    port_info = self.connector.glob.actual.get_node_network_port(self. sysid, self.tenantid, n, pid)
                    node = n
            if node is None or port_info is None:
                raise ValueError('Connection point {} not found'.format(cp_uuid))
            res = self.connector.glob.actual.add_node_port_to_network(self.sysid, self.tenantid, node, port_info['uuid'], net_uuid)
            if res.get('result') is not None:
                return cp_uuid
            raise ValueError('Error connecting: {}'.format(res['error']))

        def disconnect_cp(self, cp_uuid):
            ports = self.connector.glob.actual.get_all_nodes_network_ports(self.sysid, self.tenantid)
            node = None
            port_info = None
            for p in ports:
                n, pid = p
                if pid == cp_uuid:
                    port_info = self.connector.glob.actual.get_node_network_port(self. sysid, self.tenantid, n, pid)
                    node = n
            if node is None or port_info is None:
                raise ValueError('Connection point {} not found'.format(cp_uuid))
            res = self.connector.glob.actual.remove_node_port_from_network(self.sysid, self.tenantid, node, port_info['uuid'])
            if res.get('result') is not None:
                return cp_uuid
            raise ValueError('Error connecting: {}'.format(res['error']))

        def add_router(self, nodeid, manifest):
            router_id = manifest.get('uuid')
            self.connector.glob.desired.add_node_network_router(
                self.sysid, self.tenantid, nodeid, router_id, manifest)
            router_info = self.connector.glob.actual.get_node_network_router(
                self.sysid, self.tenantid, nodeid, router_id)
            while router_info is None:
                    router_info = self.connector.glob.actual.get_node_network_router(
                self.sysid, self.tenantid, nodeid, router_id)
            return router_info


        def remove_router(self, node_id, router_id):
            self.connector.glob.desired.remove_node_network_router(
                self.sysid, self.tenantid, node_id, router_id)

        def add_router_port(self, nodeid, router_id, port_type, vnet_id=None, ip_address=None):
            if port_type.upper() not in ['EXTERNAL', 'INTERNAL']:
                raise ValueError("port_type can be only one of : INTERNAL, EXTERNAL")

            port_type = port_type.upper()
            return self.connector.glob.actual.add_port_to_router(self.sysid, self.tenantid, nodeid, router_id, port_type, vnet_id, ip_address)

        def remove_router_port(self, nodeid, router_id, vnet_id):
            return self.connector.glob.actual.remove_port_from_router(self.sysid, self.tenantid, nodeid, router_id, vnet_id)



        def create_floating_ip(self, nodeid):
            return self.connector.glob.actual.add_node_floatingip(self.sysid, self.tenantid, nodeid)

        def delete_floating_ip(self, nodeid, ip_id):
            return self.connector.glob.actual.remove_node_floatingip(self.sysid, self.tenantid, nodeid, ip_id)


        def assign_floating_ip(self, nodeid, ip_id, cp_id):
            return self.connector.glob.actual.assign_node_floating_ip(self.sysid, self.tenantid, nodeid, ip_id, cp_id)

        def retain_floating_ip(self, nodeid, ip_id, cp_id):
            return self.connector.glob.actual.retain_node_floating_ip(self.sysid, self.tenantid, nodeid, ip_id, cp_id)

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

    class FDUAPI(object):
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

        def __wait_node_fdu_state_change(self, instanceid, state):
            '''

            Function used to wait if an instance changest state
             (eg. configured -> run) or goes to error state

            :param node_uuid
            :param fdu_uuid
            :param state the new expected state

            :return dict {'status':<new status>,
                            'fdu_uuid':fdu_uuid}

            '''

            fdu_info = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, '*', instanceid)
            while fdu_info is None:
                    fdu_info = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, '*', instanceid)
            fdu = InfraFDU(fdu_info)
            es = fdu.get_status()
            while es.upper() not in [state, 'ERROR']:
                fdu_info = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, '*', instanceid)
                fdu = InfraFDU(fdu_info)
                es = fdu.get_status()

            if es.upper() == 'ERROR':
                raise ValueError('Unable to change state to {} for FDU Instance: {} Errno: {} Msg: {}'.format(
                    state, instanceid,fdu_info.get('error_code'), fdu_info.get('error_msg')))
            return fdu_info

        def onboard(self, descriptor, wait=True):
            '''

            Onboard the FDU descriptor in the Catalog
            :param descriptor: the fdu descriptor
            :param wait: make the call wait for completio
            :return the fdu uuid

            '''
            if not isinstance(descriptor, FDU):
                raise ValueError("descriptor should be of type FDU")
            nodes = self.connector.glob.actual.get_all_nodes(self.sysid, self.tenantid)
            if len(nodes) == 0:
                raise SystemError("No nodes in the system!")
            n = random.choice(nodes)

            res = self.connector.glob.actual.onboard_fdu_from_node(self.sysid, self.tenantid, n, descriptor.get_uuid(), descriptor.to_json())
            if res.get('result') is None:
                raise SystemError('Error during onboarding {}'.format(res['error']))
            return FDU(res['result'])


        def offload(self, fdu_uuid, wait=True):
            '''

            Offload the FDU descriptor from the Catalog
            :param fdu_uuid: fdu uuid you want to remove
            :param wait: make the call wait for completion
            :return the fdu uuid

            '''
            res = self.connector.glob.desired.remove_catalog_fdu_info(
                self.sysid, self.tenantid, fdu_uuid)
            # if res.get('result') is None:
            #     raise SystemError('Error during onboarding {}'.format(res['error']))

            return fdu_uuid

        def define(self, fduid, node_uuid, wait=True):
            '''

            Defines an FDU instance in a node, this method will check
             the descriptor before sending the definition to the node

            :param fduid: id of the fdu you want to instantiate
            :param node_uuid: destination node uuid
            :param wait: if wait that the definition is complete before
             returning
            :return: instance id
            '''
            desc = self.connector.glob.actual.get_catalog_fdu_info(
                self.sysid, self.tenantid, fduid)
            if desc is None:
                raise ValueError('FDU with this UUID not found in the catalog')

            res = self.connector.glob.actual.define_fdu_in_node(self.sysid, self.tenantid, node_uuid, fduid)
            if res.get('error') is not None:
                raise ValueError('Got Error {}'.format(res['error']))
            if wait:
                self.__wait_node_fdu_state_change(res['result']['uuid'],'DEFINE')
            return InfraFDU(res['result'])


        def undefine(self, instanceid, wait=True):
            '''

            This method undefine an FDU instance from a None

            :param instanceid: FDU instance you want to undefine
            :param wait: if wait before returning that the entity is undefined
            :return: instanceid
            '''
            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')

            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('UNDEFINE')
            fduid = record.get_fdu_id()

            self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            return instanceid

        def configure(self, instanceid, wait=True):
            '''

            Configure an FDU instance

            :param instanceid: FDU instance you want to configure
            :param wait: make the function blocking
            :return: instanceid
            '''
            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')

            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('CONFIGURE')
            fduid = record.get_fdu_id()

            res = self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            if wait:
                self.__wait_node_fdu_state_change(instanceid,  'CONFIGURE')
            return res

        def clean(self, instanceid, wait=True):
            '''

            Clean an FDU instance

            :param instanceid: FDU instance you want to clean
            :param wait: make the function blocking
            :return: instanceid
            '''

            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')

            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('CLEAN')
            fduid = record.get_fdu_id()

            res = self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            if wait:
                self.__wait_node_fdu_state_change(instanceid,  'DEFINE')
            return res

        def start(self, instanceid, wait=True):
            '''

            Start an FDU instance

            :param instanceid: FDU instance you want to start
            :param wait: make the function blocking
            :return: instanceid
            '''

            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')

            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('RUN')
            fduid = record.get_fdu_id()

            res = self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            if wait:
                self.__wait_node_fdu_state_change(instanceid,  'RUN')
            return res

        def stop(self, instanceid, wait=True):
            '''

            Stop an FDU instance

            :param instanceid: FDU instance you want to stop
            :param wait: make the function blocking
            :return: instanceid
            '''

            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')

            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('STOP')
            fduid = record.get_fdu_id()

            res = self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            if wait:
                self.__wait_node_fdu_state_change(instanceid,  'CONFIGURE')
            return res

        def pause(self, instanceid, wait=True):
            '''

            Pause an FDU instance

            :param instanceid: FDU instance you want to pause
            :param wait: make the function blocking
            :return: instanceid
            '''

            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')

            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('PAUSE')
            fduid = record.get_fdu_id()

            res = self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            if wait:
                self.__wait_node_fdu_state_change(instanceid,  'PAUSE')
            return res

        def resume(self, instanceid, wait=True):
            '''

            Resume an FDU instance

            :param instanceid: FDU instance you want to resume
            :param wait: make the function blocking
            :return: instanceid
            '''

            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')


            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            record = InfraFDU(record)

            record.set_status('RESUME')
            fduid = record.get_fdu_id()

            res = self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid, node, fduid, instanceid, record.to_json())
            if wait:
                self.__wait_node_fdu_state_change(instanceid,  'RUN')
            return res

        def migrate(self, instanceid, destination_node_uuid, wait=True):
            '''

            Live migrate an instance between two nodes

            The migration is issued when this command is sended,
             there is a little overhead for the copy of the base image and the disk image


            :param instanceid: fdu you want to migrate
            :param destination_node_uuid: destination node
            :param wait: optional wait before returning
            :return: instanceid
            '''

            node = self.connector.glob.actual.get_fdu_instance_node(
                self.sysid, self.tenantid, instanceid)
            if node is None:
                raise ValueError('Unable to find node for this instanceid')
            record = self.connector.glob.actual.get_node_fdu_instance(
                self.sysid, self.tenantid, node, instanceid)

            src_record = InfraFDU(record)
            dst_record = InfraFDU(record)

            fduid = record.get_fdu_id()

            src_record.set_status('TAKE_OFF')
            dst_record.set_status('LAND')

            src_record.set_migration_properties(node, destination_node_uuid)
            dst_record.set_migration_properties(node, destination_node_uuid)


            self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid,
                                                destination_node_uuid,
                                                fduid, instanceid, dst_record.to_json())
            self.connector.glob.desired.add_node_fdu(self.sysid, self.tenantid,
                                                node, fduid, instanceid, src_record.to_json())

            if wait:
                self.__wait_node_fdu_state_change(instanceid, 'RUN')
            return instanceid


        def instantiate(self, fduid, nodeid, wait=True):
            '''
            Instantiate (define, configure, start) an fdu in a node

            :param fduid: id of the fdu to instantiate
            :param nodeid: node where instantiate
            :return instance uuid
            '''
            instance_info = self.define(fduid, nodeid)
            instance_id = instance_info.get_uuid()
            self.configure(instance_id)
            self.start(instance_id)
            return instance_info

        def terminate(self, instanceid, wait=True):
            '''
            Terminate (stop, clean, undefine) an instance

            :param instanceid: instance you want to terminate
            :return instance uuid
            '''

            self.stop(instanceid)
            self.clean(instanceid)
            return self.undefine(instanceid)


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
            return self.connector.glob.actual.get_catalog_fdu_info(self.sysid, self.tenantid, fdu_uuid)

        def instance_info(self, instanceid):
            '''
            Information about an instance

            :param instanceid: instance id

            :return dict containing the fdu record and hypervisor informations

            '''
            data = self.connector.glob.actual.get_node_fdu_instance(self.sysid, self.tenantid, "*", instanceid)
            fdu = InfraFDU(data)
            return fdu

        def get_nodes(self, fdu_uuid):
            '''

                List of nodes where the fdu is running
                :param fdu_uuid fdu you want to find the nodes
                :return: node_uuid list

            '''
            return self.connector.glob.actual.get_fdu_nodes(self.sysid, self.tenantid, fdu_uuid)

        def list_node(self, node_uuid):
            '''

                List of fdu in the node
                :param node_uuid node you want to list the fdus
                :return: fdu_uuid list

            '''
            return self.connector.glob.actual.get_node_fdus(self.sysid, self.tenantid, node_uuid)


        def instance_list(self, fduid):
            '''
                List of instances for an FDU

                :param fduid
                :return dictionary of {node_id: [instances list]}
            '''
            infos = self.connector.glob.actual.get_node_fdu_instances(
                self.sysid, self.tenantid, "*", fduid)
            nodes = list(dict.fromkeys(list(map( lambda x: x[0], infos))))
            res = {}
            for n in nodes:
                insts = []
                for ii in infos:
                    if ii[0] == n:
                        insts.append(ii[2])
                res.update({n:insts})
            return res


        def list(self, node_uuid='*'):
            '''

            List all entity element available in the system/teneant
             or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: {entity uuid: instance list} list}
            '''
            return self.connector.glob.actual.get_catalog_all_fdus(self.sysid, self.tenantid)


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
            res = self.connector.glob.desired.add_image(self.sysid,
             self.tenantid,img_id, descriptor)
            return img_id

        def get(self, image_uuid):
            return self.connector.glob.desired.get_image(self.sysid,
             self.tenantid,image_uuid)

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
            ret = self.connector.glob.desired.remove_image(self.sysid,
             self.tenantid, image_uuid)
            return image_uuid

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
            res = self.connector.glob.desired.add_flavor(self.sysid,
             self.tenantid,flv_id, descriptor)
            return flv_id

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
             self.tenantid,flavor_uuid)

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
            ret = self.connector.glob.desired.remove_flavor(self.sysid,
             self.tenantid, flavor_uuid)
            return flavor_uuid

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
