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
import time
from enum import Enum
from fog05.yaks_connector import Yaks_Connector
from fog05.interfaces import Constants
from fog05.interfaces.FDU import FDU
from fog05.interfaces.InfraFDU import InfraFDU
from mvar import MVar


class FIMAPI(object):
    '''
    Class: FIMAPI

    This class implements the API to interact with Eclipse fog05 FIM

    attributes
    ----------
    descriptor : Descriptor
        Gives access to the descriptor API
    node : Node
        Gives access to the node API
    plugin : Plugin
        Gives access to the plugin API
    network : Network
        Gives access to the descriptor API
    fdu : FDUAPI
        Gives access to the FDU API
    image : Image
        Gives access to the image API
    flavor : Flavor
        Gives access to the flavor API

    '''

    def __init__(self, locator='127.0.0.1:7447',
                 sysid=Constants.default_system_id,
                 tenantid=Constants.default_tenant_id):

        self.connector = Yaks_Connector(locator)
        self.sysid = sysid
        self.tenantid = tenantid
        self.descriptor = self.Descriptor()
        self.node = self.Node(self.connector, self.sysid, self.tenantid)
        self.plugin = self.Plugin(self.connector, self.sysid, self.tenantid)
        self.network = self.Network(self.connector, self.sysid, self.tenantid)
        self.fdu  = self.FDUAPI(self.connector, self.sysid, self.tenantid)
        self.image = self.Image(self.connector, self.sysid, self.tenantid)
        self.flavor = self.Flavor(self.connector, self.sysid, self.tenantid)


    def close(self):
        '''
        Closes the FIMAPI
        '''
        self.connector.close()

    class Descriptor(object):
        '''
        Class: Descriptor

        This class encapsulates API for descriptors
        '''

        def __init__(self):
            pass

        def check(self, descriptor, descriptor_type):
            '''

            Checks the given descriptor

            parameters
            ----------
            descriptor : dictionary
                the descriptor to be checked
            descriptor_type : API.Descriptor.Type
                type of descriptor

            returns
            -------
            bool
            '''
            # if descriptor_type == self.Type.ENTITY:
            #     t = descriptor.get('type')
            #     try:
            #         if t == 'vm':
            #             validate(descriptor.get('entity_data'),
            #                      Schemas.vm_schema)
            #         elif t == 'container':
            #             validate(descriptor.get('entity_data'),
            #                      Schemas.container_schema)
            #         elif t == 'native':
            #             validate(descriptor.get('entity_data'),
            #                      Schemas.native_schema)
            #         elif t == 'ros2':
            #             validate(descriptor.get('entity_data'),
            #                      Schemas.ros2_schema)
            #         elif t == 'usvc':
            #             return False
            #         else:
            #             return False
            #     except ValidationError as ve:
            #         return False
            # if descriptor_type == self.Type.NETWORK:
            #     try:
            #         validate(descriptor, Schemas.network_schema)
            #     except ValidationError as ve:
            #         return False
            # if descriptor_type == self.Type.ENTITY:
            #     try:
            #         validate(descriptor, Schemas.entity_schema)
            #     except ValidationError as ve:
            #         return False

            return True

        class Type(Enum):
            '''
            Descriptor types
            '''
            ENTITY = 0
            IMAGE = 1
            FLAVOR = 3
            NETWORK = 4
            PLUGIN = 5

    class Node(object):
        '''
        Class: Node
        This class encapsulates API for Nodes
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
            Gets all nodes in the current system/tenant

            returns
            -------
            string list

            '''
            nodes = self.connector.glob.actual.get_all_nodes(
                self.sysid, self.tenantid)
            return nodes

        def info(self, node_uuid):
            '''
            Provides all information about the given node

            parameters
            ----------
            node_uuid : string
                UUID of the node

            returns
            -------
            dictionary
            '''
            if node_uuid is None:
                return None
            node_info = self.connector.glob.actual.get_node_info(
                self.sysid, self.tenantid, node_uuid)
            return node_info

        def status(self, node_uuid):
            '''
            Provides all status information about the given node,

            parameters
            ----------
            node_uuid : string
                UUID of the node

            returns
            -------
            dictionary
            '''
            if node_uuid is None:
                return None
            node_status = self.connector.glob.actual.get_node_status(
                self.sysid, self.tenantid, node_uuid)
            return node_status

        def plugins(self, node_uuid):
            '''
            Gets the list of plugins in the given node

            parameters
            ----------
            node_uuid : string
                UUID of the node

            returns
            -------
            string list
            '''
            plugins = self.connector.glob.actual.get_all_plugins_ids(
                self.sysid, self.tenantid, node_uuid)
            return plugins

        def search(self, search_dict):
            '''
            Searches for nodes that satisfies the parameter

            parameters
            ----------
            search_dict : dictionary
                search parameters

            returns
            -------
            string list
            '''
            raise NotImplementedError("Not yet...")

    class Plugin(object):
        '''
        Class: Plugin
        This class encapsulates API for Plugins
        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def add(self, descriptor, node_uuid):
            '''
            Adds the given plugin to the given node

            parameters
            ----------
            descriptor : dictionary
                the plugin descriptor
            node_uuid : string
                UUID of the node

            returns
            -------
            bool
            '''

            # descriptor.update({'status': 'add'})
            # plugins = {'plugins': [descriptor]}
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
            raise NotImplementedError("Not yet...")

        def remove(self, plugin_uuid, node_uuid):
            '''
            Removes the given plugin from the given node

            parameters
            ----------
            plugin_uuid : string
                UUID of the plugin
            node_uuid : string
                UUID of the node

            returns
            -------
            bool
            '''
            raise NotImplementedError("Not yet...")

        def info(self, plugin_uuid, node_uuid):
            '''
            Gets information about the given plugin in the given node

            parameters
            ----------
            plugin_uuid : string
                UUID of the plugin
            node_uuid : string
                UUID of the node

            returns
            -------
            dictionary
            '''
            return self.connector.glob.actual.get_plugin_info(
                self.sysid, self.tenantid, node_uuid, plugin_uuid)

        def search(self, search_dict, node_uuid=None):
            '''
            Searches for plugin that satisfies the parameter

            parameters
            ----------
            search_dict : dictionary
                search parameters
            node_uuid : string
                optional node UUID where search

            returns
            -------
            string list
            '''
            raise NotImplementedError("Not yet...")

    class Network(object):
        '''
        Class: Plugin
        This class encapsulates API for networks
        '''

        def __init__(self, connector=None, sysid=Constants.default_system_id,
                     tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def add_network(self, descriptor):
            '''
            Registers a network in the system catalog

            Needs at least one node in the system!

            parameters
            ----------
            descriptor : dictionary
                network descriptor

            returns
            -------
            bool
            '''

            descriptor.update({'status': 'add'})
            net_id = descriptor.get('uuid')

            self.connector.glob.desired.add_network(
                self.sysid, self.tenantid, net_id, descriptor)

        def remove_network(self, net_uuid):
            '''
            Removes the given network from the system catalog
            Needs at least one node in the system!

            parameters
            ----------
            net_uuid : string
                UUID of network

            returns
            -------
            bool
            '''
            descriptor = self.connector.glob.actual.get_network(
                self.sysid, self.tenantid, net_uuid)
            if descriptor is None:
                return
            descriptor.update({'status': 'remove'})
            self.connector.glob.desired.remove_network(
                self.sysid, self.tenantid, net_uuid)

        def add_network_to_node(self, descriptor, nodeid):
            '''
            Creates the given virtual network in the given node

            parameters
            ----------
            descriptor : dictionary
                network descriptor
            nodeid : string
                UUID of node

            returns
            -------
            dictionary
            '''
            net_id = descriptor.get('uuid')
            net = self.connector.glob.actual.get_node_network(self.sysid, self.tenantid, nodeid, net_id)
            if net is not None:
                return net
            res = self.connector.glob.actual.create_network_in_node(self.sysid, self.tenantid, nodeid, descriptor)
            if res.get('error') is not None:
                raise ValueError('Got Error {}'.format(res['error']))
            return res['result']

        def remove_network_from_node(self, netid, nodeid):
            '''
            Removes the given virtual network from the given node

            parameters
            ----------
            netid : string
                network uuid
            nodeid : string
                UUID of node

            returns
            -------
            dictionary
            '''
            res = self.connector.glob.actual.remove_network_from_node(self.sysid, self.tenantid, nodeid, netid)
            if res.get('error') is not None:
                raise ValueError('Got Error {}'.format(res['error']))
            return res['result']


        def add_connection_point(self, cp_descriptor):
            '''
            Registers a connection point in the system catalog

            Needs at least one node in the system!

            parameters
            ----------
            descriptor : dictionary
                connection descriptor

            returns
            -------
            bool
            '''
            cp_descriptor.update({'status': 'add'})
            cp_id = cp_descriptor.get('uuid')
            self.connector.glob.desired.add_network_port(
                self.sysid, self.tenantid, cp_id, cp_descriptor)

        def delete_connection_point(self, cp_uuid):
            '''
            Removes the given connection point from the system catalog
            Needs at least one node in the system!

            parameters
            ----------
            cp_uuid : string
                UUID of connection point

            returns
            -------
            bool
            '''
            descriptor = self.connector.glob.actual.get_network_port(
                self.sysid, self.tenantid, cp_uuid)
            descriptor.update({'status': 'remove'})
            self.connector.glob.desired.add_network_port(
                self.sysid, self.tenantid, cp_uuid, descriptor)

        def connect_cp_to_network(self, cp_uuid, net_uuid):
            '''
            Connects the given connection point to the given network

            parameters
            ----------
            cp_uuid : string
                UUID of the connection point
            net_uuid : string
                UUID of the virtual network

            returns
            -------
            string
            '''
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
            '''
            Disconnects the given connection point

            parameters
            ----------
            cp_uuid : string
                UUID of connection point

            returns
            -------
            string
            '''
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

        def add_router(self, nodeid, descriptor):
            '''
            Creates the given virtual router in the given node

            parameters
            ----------
            descriptor : dictionary
                descriptor of the router
            nodeid : string
                UUID of the node

            returns
            -------
            dictionary
            '''
            router_id = descriptor.get('uuid')
            self.connector.glob.desired.add_node_network_router(
                self.sysid, self.tenantid, nodeid, router_id, descriptor)
            router_info = self.connector.glob.actual.get_node_network_router(
                self.sysid, self.tenantid, nodeid, router_id)
            while router_info is None:
                    router_info = self.connector.glob.actual.get_node_network_router(
                self.sysid, self.tenantid, nodeid, router_id)
            return router_info


        def remove_router(self, node_id, router_id):
            '''
            Removes the given virtual router in the given node

            parameters
            ----------
            router_id : string
                UUID of the router
            node_id : string
                UUID of the node

            returns
            -------
            dictionary
            '''
            self.connector.glob.desired.remove_node_network_router(
                self.sysid, self.tenantid, node_id, router_id)

        def add_router_port(self, nodeid, router_id, port_type, vnet_id=None, ip_address=None):
            '''
            Adds a port to the given virtual router

            parameters
            ----------
            nodeid : string
                UUID of the node
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
            if port_type.upper() not in ['EXTERNAL', 'INTERNAL']:
                raise ValueError('port_type can be only one of : INTERNAL, EXTERNAL')

            port_type = port_type.upper()
            return self.connector.glob.actual.add_port_to_router(self.sysid, self.tenantid, nodeid, router_id, port_type, vnet_id, ip_address)

        def remove_router_port(self, nodeid, router_id, vnet_id):
            '''
            Removes a port from the given router

            parameters
            ----------
            nodeid : string
                UUID of the node
            router_id : string
                UUID of the virtual router
            vnet_id : string
                network to be disconnected

            returns
            -------
            dictionary

            '''
            return self.connector.glob.actual.remove_port_from_router(self.sysid, self.tenantid, nodeid, router_id, vnet_id)



        def create_floating_ip(self, nodeid):
            '''
            Creates a floating IP in the given node

            parameters
            ----------
            nodeid : string
                UUID of the node

            returns
            -------
            dictionary
            '''
            return self.connector.glob.actual.add_node_floatingip(self.sysid, self.tenantid, nodeid)

        def delete_floating_ip(self, nodeid, ip_id):
            '''
            Deletes the given floating IP from the given node

            parameters
            ----------
            nodeid : string
                UUID of the node
            ip_id : string
                UUID of the floating IP

            returns
            -------
            dictionary

            '''
            return self.connector.glob.actual.remove_node_floatingip(self.sysid, self.tenantid, nodeid, ip_id)


        def assign_floating_ip(self, nodeid, ip_id, cp_id):
            '''
            Assigns the given floating IP to the given conncetion point in the given node

            parameters
            ----------
            nodeid : string
                UUID of the node
            ip_id : string
                UUID of the floating IP
            cp_id : string
                UUID of the connection point

            returns
            -------
            dictionary
            '''
            return self.connector.glob.actual.assign_node_floating_ip(self.sysid, self.tenantid, nodeid, ip_id, cp_id)

        def retain_floating_ip(self, nodeid, ip_id, cp_id):
            '''
            Retains the given floating IP from the given connection point in the given node

            parameters
            ----------
            nodeid : string
                UUID of the node
            ip_id : string
                UUID of the floating IP
            cp_id : string
                UUID of the connection point

            returns
            -------
            dictionary
            '''
            return self.connector.glob.actual.retain_node_floating_ip(self.sysid, self.tenantid, nodeid, ip_id, cp_id)

        def list(self):
            '''
            Gets all networks registered in the system catalog

            returns
            -------
            string list
            '''
            return self.connector.glob.actual.get_all_networks(
                self.sysid, self.tenantid)

        def search(self, search_dict, node_uuid=None):
            '''
            Searches for plugin that satisfies the parameter

            parameters
            ----------
            search_dict : dictionary
                search parameters
            node_uuid : string
                optional node UUID where search

            returns
            -------
            string list
            '''
            raise NotImplementedError("Not yet...")

    class FDUAPI(object):
        '''
        Class: FDUAPI
        This class encapsulates API for FDUs
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
            Waits an FDU instance state to change

            parameters
            ----------
            instanceid : string
                UUID of instance
            state : string
                new state

            returns
            --------
            dictionary

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

        def onboard(self, descriptor):
            '''
            Registers an FDU descriptor in the system catalog
            Needs at least one node in the system!

            parameters
            ----------
            descriptor : FDU
                FDU descriptor

            returns
            -------
            FDU
            '''
            if not isinstance(descriptor, FDU):
                raise ValueError('descriptor should be of type FDU')
            nodes = self.connector.glob.actual.get_all_nodes(self.sysid, self.tenantid)
            if len(nodes) == 0:
                raise SystemError('No nodes in the system!')
            n = random.choice(nodes)

            res = self.connector.glob.actual.onboard_fdu_from_node(self.sysid, self.tenantid, n, descriptor.get_uuid(), descriptor.to_json())
            if res.get('result') is None:
                raise SystemError('Error during onboarding {}'.format(res['error']))
            return FDU(res['result'])


        def offload(self, fdu_uuid):
            '''
            Removes the given FDU from the system catalog
            Needs at least one node in the system!

            parameters
            ----------
            fdu_uuid : string
                UUID of fdu

            returns
            --------
            string
            '''
            res = self.connector.glob.desired.remove_catalog_fdu_info(
                self.sysid, self.tenantid, fdu_uuid)
            # if res.get('result') is None:
            #     raise SystemError('Error during onboarding {}'.format(res['error']))

            return fdu_uuid

        def define(self, fduid, node_uuid, wait=True):
            '''
            Defines the given fdu in the given node

            Instance UUID is system-wide unique

            parameters
            ----------
            fduid : string
                UUID of the FDU
            node_uuid : string
                UUID of the node
            wait : bool
                optional, call will block until FDU is defined
            returns
            -------
            InfraFDU
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


        def undefine(self, instanceid):
            '''
            Undefines the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance


            returns
            -------
            string
            '''
            node = self.connector.glob.actual.get_fdu_instance_node(self.sysid, self.tenantid, instanceid)
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
            Configures the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            wait : bool
                optional, call will block until FDU is configured

            returns
            -------
            string
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
            return instanceid

        def clean(self, instanceid, wait=True):
            '''
            Cleans the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            wait : bool
                optional, call will block until FDU is cleaned

            returns
            -------
            string
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
            return instanceid

        def start(self, instanceid, wait=True):
            '''
            Starts the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            wait : bool
                optional, call will block until FDU is started

            returns
            -------
            string
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
            return instanceid

        def stop(self, instanceid, wait=True):
            '''
            Stops the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            wait : bool
                optional, call will block until FDU is stopeed

            returns
            -------
            string
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
            return instanceid

        def pause(self, instanceid, wait=True):
            '''
            Pauses the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            wait : bool
                optional, call will block until FDU is paused

            returns
            -------
            string
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
            return instanceid

        def resume(self, instanceid, wait=True):
            '''
            Resumes the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            wait : bool
                optional, call will block until FDU is resumed

            returns
            -------
            string
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
            return instanceid

        def migrate(self, instanceid, destination_node_uuid, wait=True):
            '''
            Migrates the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            destination_node_uuid : string
                UUID of destination node
            wait : bool
                optional, call will block until FDU is migrated

            returns
            -------
            string
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
            Instantiates the given fdu in the given node

            This functions calls: define, configure, start

            Instance UUID is system-wide unique

            parameters
            ----------
            fduid : string
                UUID of the FDU
            node_uuid : string
                UUID of the node
            wait : bool
                optional, call will block until FDU is defined

            returns
            -------
            InfraFDU
            '''
            instance_info = self.define(fduid, nodeid)
            time.sleep(0.5)
            instance_id = instance_info.get_uuid()
            self.configure(instance_id)
            time.sleep(0.5)
            self.start(instance_id)
            return instance_info

        def terminate(self, instanceid, wait=True):
            '''
            Terminates the given instance

            This function calls: stop, clean, undefine

            paremeters
            ----------
            instanceid : string
                UUID of instance


            returns
            -------
            string
            '''

            self.stop(instanceid)
            self.clean(instanceid)
            return self.undefine(instanceid)


        def search(self, search_dict, node_uuid=None):
            '''
            Searches for flavors that satisfies the parameter

            parameters
            ----------
            search_dict : dictionary
                search parameters
            node_uuid : string
                optional node UUID where search

            returns
            -------
            string list
            '''
            raise NotImplementedError("Not yet...")

        def info(self, fdu_uuid):
            '''
            Gets information about the given FDU from the catalog

            parameters
            ----------
            fdu_uuid : string
                UUID of the FDU

            returns
            -------
            FDU
            '''
            data = self.connector.glob.actual.get_catalog_fdu_info(self.sysid, self.tenantid, fdu_uuid)
            fdu = FDU(data)
            return fdu

        def instance_info(self, instanceid):
            '''
            Gets information about the given instance

            parameters
            ----------
            instanceid : string
                UUID of the instance

            returns
            -------
            InfraFDU
            '''

            data = self.connector.glob.actual.get_node_fdu_instance(self.sysid, self.tenantid, '*', instanceid)
            fdu = InfraFDU(data)
            return fdu

        def get_nodes(self, fdu_uuid):
            '''
            Gets all the node in which the given FDU is running

            parameters
            ----------
            fdu_uuid : string
                UUID of the FDU

            returns
            -------
            string list

            '''
            return self.connector.glob.actual.get_fdu_nodes(self.sysid, self.tenantid, fdu_uuid)

        def list_node(self, node_uuid):
            '''
            Gets all the FDUs running in the given node

            parameters
            ---------
            node_uuid : string
                UUID of the node

            returns
            -------
            string list
            '''
            return self.connector.glob.actual.get_node_fdus(self.sysid, self.tenantid, node_uuid)


        def instance_list(self, fduid):
            '''
            Gets all the instances of a given FDU

            parameters
            ----------
            fduid : string
                UUID of the FDU

            returns
            -------
            dictionary
                {node_id: [instances list]}
            '''

            infos = self.connector.glob.actual.get_node_fdu_instances(
                self.sysid, self.tenantid, '*', fduid)
            nodes = list(dict.fromkeys(list(map( lambda x: x[0], infos))))
            res = {}
            for n in nodes:
                insts = []
                for ii in infos:
                    if ii[0] == n:
                        insts.append(ii[2])
                res.update({n:insts})
            return res


        def list(self):
            '''
            Gets all the FDUs registered in the catalog

            returns
            -------
            string list
            '''
            return self.connector.glob.actual.get_catalog_all_fdus(self.sysid, self.tenantid)



    class Image(object):
        '''
        Class: Image
        This class encapsulates API for Images
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
            Registers an image in the system catalog
            Needs at least one not in the system

            parameters
            ----------
            descriptor : dictionary
                image descriptor

            returns
            -------
            string
            '''

            img_id = descriptor.get('uuid')
            res = self.connector.glob.desired.add_image(self.sysid,
             self.tenantid,img_id, descriptor)
            return img_id

        def get(self, image_uuid):
            '''
            Gets the information about the given image

            parameters
            ----------
            image_uuid : string
                UUID of image

            returns
            -------
            dictionary
            '''
            return self.connector.glob.desired.get_image(self.sysid,
             self.tenantid,image_uuid)

        def remove(self, image_uuid):
            '''
            Removes the given image from the system catalog
            Needs at least one not in the system

            parameters
            ----------
            image_uuid : string

            returns
            -------
            string
            '''

            ret = self.connector.glob.desired.remove_image(self.sysid,
             self.tenantid, image_uuid)
            return image_uuid

        def search(self, search_dict, node_uuid=None):
            '''
            Searches for images that satisfies the parameter

            parameters
            ----------
            search_dict : dictionary
                search parameters
            node_uuid : string
                optional node UUID where search

            returns
            -------
            string list
            '''
            raise NotImplementedError("Not yet...")

        def list(self):
            '''
            Gets all the images registered in the system catalog

            returns
            -------
            string list
            '''

            return self.connector.glob.actual.get_all_images(self.sysid,
             self.tenantid)

    class Flavor(object):
        '''
        Class: Flavor
        This class encapsulates API for Flavors
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
            Registers a flavor in the system catalog
            Needs at least one node in the system

            parameters
            ----------
            descriptor : dictionary
                flavor descriptor

            returns
            -------
            string
            '''

            flv_id = descriptor.get('uuid')
            res = self.connector.glob.desired.add_flavor(self.sysid,
             self.tenantid,flv_id, descriptor)
            return flv_id

        def get(self, flavor_uuid):
            '''
            Gets information about the given flavor

            parameters
            ----------
            flavor_uuid : string
                UUID of flavor

            returns
            -------
            dictionary

            '''

            return self.connector.glob.desired.get_flavor(self.sysid,
             self.tenantid,flavor_uuid)

        def remove(self, flavor_uuid):
            '''
            Removes the given flavor from the system catalog
            Needs at least one node in the system

            parameters
            ----------

            flavor_uuid : string
                UUID of flavor

            returns
            -------
            string
            '''

            ret = self.connector.glob.desired.remove_flavor(self.sysid,
             self.tenantid, flavor_uuid)
            return flavor_uuid

        def list(self):
            '''
            Gets all the flavors registered in the system catalog

            returns
            -------
            string list
            '''

            return self.connector.glob.actual.get_all_flavors(self.sysid,
             self.tenantid)

        def search(self, search_dict, node_uuid=None):
            '''
            Searches for flavors that satisfies the parameter

            parameters
            ----------
            search_dict : dictionary
                search parameters
            node_uuid : string
                optional node UUID where search

            returns
            -------
            string list
            '''
            raise NotImplementedError("Not yet...")
