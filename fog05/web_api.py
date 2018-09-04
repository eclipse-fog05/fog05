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

from enum import Enum
import uuid
import json
import fnmatch
import time
import requests




class WebAPI(object):
    '''
        This class allow the interaction with fog05 using simple HTTP REST API
        Connect to a server that expose the API
    '''

    def __init__(self, sysid=0, store_id="python-api-rest"):

        self.api = 'http://127.0.0.1:5000'

        self.manifest = self.Manifest(self.api)
        self.node = self.Node(self.api)
        self.plugin = self.Plugin(self.api)
        self.network = self.Network(self.api)
        self.entity = self.Entity(self.api)
        self.image = self.Image(self.api)
        self.flavor = self.Flavor(self.api)

        self.onboard = self.add
        self.offload = self.remove

    def add(self, manifest):
        url = '{}/onboard'.format(self.api)
        data = requests.put(url, data={'manifest': manifest})
        return data.json().get('response')

    def remove(self, entity_uuid):
        url = '{}/offload/{}'.format(self.api, entity_uuid)
        data = requests.delete(url)
        return data.json().get('response')

    class Manifest(object):
        '''
        This class encapsulates API for manifests

        '''
        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def check(self, manifest, manifest_type):
           pass
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

        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def list(self):
            '''
                Get all nodes in the current system/tenant

                :return: list of tuples (uuid, hostname)
            '''

            url = '{}/node/list'.format(self.api)
            data = requests.get(url)
            return data.json().get('response')

        def info(self, node_uuid):
            """
            Provide all information about a specific node

            :param node_uuid: the uuid of the node you want info
            :return: a dictionary with all information about the node
            """
            url = '{}/node/info/{}'.format(self.api,node_uuid)
            data = requests.get(url)
            return data.json().get('response')

        def plugins(self, node_uuid):
            '''

            Get the list of plugin installed on the specified node

            :param node_uuid: the uuid of the node you want info
            :return: a list of the plugins installed in the node with detailed informations
            '''
            url = '{}/node/plugins/{}'.format(self.api, node_uuid)
            data = requests.get(url)
            return data.json().get('response')

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
        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def add(self, manifest, node_uuid=None):
            '''

            Add a plugin to a node or to all node in the system/tenant

            :param manifest: the dictionary representing the plugin manifes
            :param node_uuid: optional the node in which add the plugin
            :return: boolean
            '''
            if node_uuid is None:
                url = '{}/plugin/add'.format(self.api)
            else:
                url = '{}/plugin/add/'.format(self.api, node_uuid)
            data = requests.put(url, data={'manifest': manifest})
            return data.json().get('response')


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
                url = '{}/plugin/list/{}'.format(self.api, node_uuid)
            else:
                url = '{}/plugin/list'.format(self.api)
            data = requests.get(url)
            return data.json().get('response')


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

        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def add(self, manifest, node_uuid=None):
            '''

            Add a network element to a node o to all nodes


            :param manifest: dictionary representing the manifest of that network element
            :param node_uuid: optional the node uuid in which add the network element
            :return: boolean
            '''

            if node_uuid is not None:
                url = '{}/network/add/{}'.format(self.api, node_uuid)
            else:
                url = '{}/network/add'.format(self.api)
            data = requests.put(url, data={'manifest': manifest})
            return data.json().get('response')


        def remove(self, net_uuid, node_uuid=None):
            '''

            Remove a network element form one or all nodes

            :param net_uuid: uuid of the network you want to remove
            :param node_uuid: optional node from which remove the network element
            :return: boolean
            '''

            if node_uuid is not None:
                url = '{}/network/remove/{}/{}'.format(self.api, net_uuid, node_uuid)
            else:
                url = '{}/network/remove/{}'.format(self.api, net_uuid)
            data = requests.delete(url)
            return data.json().get('response')


        def list(self, node_uuid=None):
            '''

            List all network element available in the system/teneant or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: network element list}
            '''

            if node_uuid is not None:
                url = '{}/network/list/{}'.format(self.api, node_uuid)
            else:
                url = '{}/network/list'.format(self.api)
            data = requests.get(url)
            return data.json().get('response')

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

        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def define(self, manifest, node_uuid):
            '''

            Defines an atomic entity in a node, this method will check the manifest before sending the definition to the node

            :param manifest: dictionary representing the atomic entity manifest
            :param node_uuid: destination node uuid
            :return: boolean
            '''
            url = '{}/entity/define/{}'.format(self.api, node_uuid)
            data = requests.put(url, data={'manifest': manifest})
            return data.json().get('response')


        def undefine(self, entity_uuid, node_uuid):
            '''

            This method undefine an atomic entity in a node

            :param entity_uuid: atomic entity you want to undefine
            :param node_uuid: destination node
            :return: boolean
            '''
            url = '{}/entity/undefine/{}/{}'.format(self.api, entity_uuid, node_uuid)
            data = requests.delete(url)
            return data.json().get('response')

        def configure(self, entity_uuid, node_uuid):
            '''

            Configure an atomic entity, creation of the instance

            :param entity_uuid: entity you want to configure
            :param node_uuid: destination node
            :return: intstance uuid or none in case of error
            '''

            url = '{}/entity/configure/{}/{}'.format(self.api, entity_uuid, node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def clean(self, entity_uuid, node_uuid, instance_uuid):
            '''

            Clean an atomic entity instance, this will destroy the instance

            :param entity_uuid: entity for which you want to clean an instance
            :param node_uuid: destionation node
            :param instance_uuid: instance you want to clean
            :return: boolean
            '''
            url = '{}/entity/clean/{}/{}/{}'.format(self.api, entity_uuid, instance_uuid, node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def run(self, entity_uuid, node_uuid, instance_uuid):
            '''

            Starting and atomic entity instance

            :param entity_uuid: entity for which you want to run the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to start
            :return: boolean
            '''
            url = '{}/entity/run/{}/{}/{}'.format(self.api, entity_uuid, instance_uuid, node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def stop(self, entity_uuid, node_uuid, instance_uuid):
            '''

            Shutting down an atomic entity instance

            :param entity_uuid: entity for which you want to shutdown the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to shutdown
            :return: boolean
            '''
            url = '{}/entity/stop/{}/{}/{}'.format(self.api, entity_uuid, instance_uuid, node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def pause(self, entity_uuid, node_uuid, instance_uuid):
            '''

            Pause the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to pause the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to pause
            :return: boolean
            '''

            url = '{}/entity/pause/{}/{}/{}'.format(self.api, entity_uuid, instance_uuid, node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def resume(self, entity_uuid, node_uuid, instance_uuid):
            '''

            resume the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to resume the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to resume
            :return: boolean
            '''

            url = '{}/entity/resume/{}/{}/{}'.format(self.api, entity_uuid, instance_uuid, node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def migrate(self, entity_uuid, instance_uuid, node_uuid, destination_node_uuid):
            '''

            Live migrate an atomic entity instance between two nodes

            The migration is issued when this command is sended, there is a little overhead for the copy of the base image and the disk image


            :param entity_uuid: ntity for which you want to migrate the instance
            :param instance_uuid: instance you want to migrate
            :param node_uuid: source node for the instance
            :param destination_node_uuid: destination node for the instance
            :return: boolean
            '''

            url = '{}/entity/migrate/{}/{}/{}/{}'.format(self.api, entity_uuid, instance_uuid, node_uuid, destination_node_uuid)
            data = requests.patch(url)
            return data.json().get('response')

        def search(self, search_dict, node_uuid=None):
            pass

    class Image(object):
        '''

        This class encapsulates the action on images


        '''
        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def add(self, manifest, node_uuid=None):
            '''

            Adding an image to a node or to all nodes

            :param manifest: dictionary representing the manifest for the image
            :param node_uuid: optional node in which add the image
            :return: boolean
            '''
            if node_uuid is not None:
                url = '{}/image/add/{}'.format(self.api, node_uuid)
            else:
                url = '{}/image/add'.format(self.api)
            data = requests.put(url, data={'manifest': manifest})
            return data.json().get('response')


        def remove(self, image_uuid, node_uuid=None):
            '''

            remove an image for a node or all nodes

            :param image_uuid: image you want to remove
            :param node_uuid: optional node from which remove the image
            :return: boolean
            '''

            if node_uuid is not None:
                url = '{}/image/remove/{}/{}'.format(self.api, image_uuid, node_uuid)
            else:
                url = '{}/image/remove/{}'.format(self.api, image_uuid)
            data = requests.delete(url)
            return data.json().get('response')

        def list(self, node_uuid=None):
            '''

            List all images in the system, or in a specific node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: image element list}
            '''

            if node_uuid is not None:
                url = '{}/image/list/{}'.format(self.api, node_uuid)
            else:
                url = '{}/image/list'.format(self.api)
            data = requests.get(url)
            return data.json().get('response')

        def search(self, search_dict, node_uuid=None):
            pass

    class Flavor(object):
        '''
          This class encapsulates the action on flavors

        '''
        def __init__(self, api=None):
            if api is None:
                raise RuntimeError('api cannot be none in API!')
            self.api = api

        def add(self, manifest, node_uuid=None):
            '''

            Add a computing flavor to a node or all nodes

            :param manifest: dictionary representing the manifest for the flavor
            :param node_uuid: optional node in which add the flavor
            :return: boolean
            '''

            if node_uuid is not None:
                url = '{}/flavor/add/{}'.format(self.api, node_uuid)
            else:
                url = '{}/flavor/add'.format(self.api)
            data = requests.put(url, data={'manifest': manifest})
            return data.json().get('response')

        def remove(self, flavor_uuid, node_uuid=None):
            '''

            Remove a flavor from all nodes or a specified node

            :param flavor_uuid: flavor to remove
            :param node_uuid: optional node from which remove the flavor
            :return: boolean
            '''
            if node_uuid is not None:
                url = '{}/flavor/remove/{}/{}'.format(self.api, flavor_uuid, node_uuid)
            else:
                url = '{}/flavor/remove/{}'.format(self.api, flavor_uuid)
            data = requests.delete(url)
            return data.json().get('response')

        def search(self, search_dict, node_uuid=None):
            pass

        def list(self, node_uuid=None):
            '''

            List all network element available in the system/teneant or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: flavor element list}
            '''

            if node_uuid is not None:
                url = '{}/flavor/list/{}'.format(self.api, node_uuid)
            else:
                url = '{}/flavor/list'.format(self.api)
            data = requests.get(url)
            return data.json().get('response')
