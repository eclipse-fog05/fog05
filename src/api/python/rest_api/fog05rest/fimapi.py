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

import requests
import json
import os
import tempfile
import uuid


def save_file(content, filename):
    full_path = os.path.join(tempfile.gettempdir(), filename)
    f = open(full_path, 'w')
    f.write(content)
    f.flush()
    f.close()
    return full_path


class FIMAPI(object):
    '''
    Class: FIMAPI

    This class implements the API to interact with Eclipse fog05 FIM
    '''

    def __init__(self, locator='127.0.0.1:8080',):


        self.base_url = 'http://{}'.format(locator)
        self.node = self.Node(self.base_url)
        self.plugin = self.Plugin(self.base_url)
        self.network = self.Network(self.base_url)
        self.fdu = self.FDUAPI(self.base_url)
        self.image = self.Image(self.base_url)
        self.flavor = self.Flavor(self.base_url)

    def check(self):
        url = '{}'.format(self.base_url)
        data = requests.get(url).content
        if isinstance(data,bytes):
                data = data.decode()
        return json.loads(data)

    def close(self):
        pass


    class Node(object):
        '''
        Class: Node
        This class encapsulates API for Nodes
        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            '''
            Gets all nodes in the current system/tenant

            returns
            -------
            string list

            '''
            url = '{}/node/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


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
            url = '{}/node/info/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/node/status/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/node/plugins/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

    class Plugin(object):
        '''
        Class: Plugin
        This class encapsulates API for Plugins
        '''
        def __init__(self, base_url):
            self.base_url = base_url

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
            url = '{}/plugin/info/{}/{}'.format(self.base_url, pluginid, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class Network(object):
        '''
        Class: Plugin
        This class encapsulates API for networks
        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add_network(self, manifest):
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
            url = '{}/network/add'.format(self.base_url)
            data = requests.post(url, data=json.dumps(manifest)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/network/remove/{}'.format(self.base_url, net_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/connection_point/add'.format(self.base_url)
            data = requests.post(url, data=json.dumps(cp_descriptor)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/connection_point/remove/{}'.format(self.base_url, cp_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            '''
            Gets all networks registered in the system catalog

            returns
            -------
            string list
            '''
            url = '{}/network/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class FDUAPI(object):
        '''
        Class: FDUAPI
        This class encapsulates API for FDUs
        '''

        def __init__(self, base_url):
            self.base_url = base_url

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
            url = '{}/fdu/onboard'.format(self.base_url)
            data = requests.post(url, data=json.dumps(descriptor)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/fdu/offload/{}'.format(self.base_url, fdu_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def define(self, fduid, node_uuid):
            '''
            Defines the given fdu in the given node

            Instance UUID is system-wide unique

            parameters
            ----------
            fduid : string
                UUID of the FDU
            node_uuid : string
                UUID of the node
            returns
            -------
            InfraFDU
            '''
            url = '{}/fdu/define/{}/{}'.format(self.base_url, fduid, node_uuid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/fdu/undefine/{}'.format(self.base_url, instanceid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res = json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def configure(self, instanceid):
            '''
            Configures the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance

            returns
            -------
            string
            '''
            url = '{}/fdu/configure/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res = json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def clean(self, instanceid):
            '''
            Cleans the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance

            returns
            -------
            string
            '''
            url = '{}/fdu/clean/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def start(self, instanceid):
            '''
            Starts the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance

            returns
            -------
            string
            '''
            url = '{}/fdu/start/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def stop(self, instanceid):
            '''
            Stops the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance

            returns
            -------
            string
            '''
            url = '{}/fdu/stop/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def pause(self, instanceid):
            '''
            Pauses the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance

            returns
            -------
            string
            '''
            url = '{}/fdu/pause/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def resume(self, instanceid):
            '''
            Resumes the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance

            returns
            -------
            string
            '''
            url = '{}/fdu/resume/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def migrate(self, instanceid, destination_node_uuid):
            '''
            Migrates the given instance

            paremeters
            ----------
            instanceid : string
                UUID of instance
            destination_node_uuid : string
                UUID of destination node

            returns
            -------
            string
            '''
            url = '{}/fdu/migrate/{}/{}'.format(self.base_url, instanceid, destination_node_uuid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def instantiate(self, fduid, nodeid):
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

            returns
            -------
            InfraFDU
            '''
            url = '{}/fdu/instantiate/{}/{}'.format(self.base_url, fduid, nodeid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def terminate(self, instanceid):
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
            url = '{}/fdu/terminate/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res = json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

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
            url = '{}/fdu/get_nodes/{}'.format(self.base_url, fdu_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/fdu/list_node/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/fdu/instance_list/{}'.format(self.base_url, fduid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/fdu/info/{}'.format(self.base_url, fdu_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/fdu/instance_info/{}'.format(self.base_url, instanceid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            '''
            Gets all the FDUs registered in the catalog

            returns
            -------
            string list
            '''
            url = '{}/fdu/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class Image(object):
        '''
        Class: Image
        This class encapsulates API for Images
        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor, image_path):
            '''
            Registers an image in the system catalog
            Needs at least one not in the system

            parameters
            ----------
            descriptor : dictionary
                image descriptor
            image_path : string
                path to the image file to be uploaded

            returns
            -------
            string
            '''
            img_id = descriptor.get('uuid', None)
            if  img_id is None:
                img_id =  '{}'.format(uuid.uuid4())
                descriptor.update({'uuid':img_id})
            url = '{}/image/add'.format(self.base_url)
            desc_filename = '{}.json'.format(descriptor['uuid'])
            temp_desc_file = save_file(json.dumps(descriptor),desc_filename)
            files = {'descriptor': open(temp_desc_file, 'rb'), 'image': open(image_path, 'rb')}
            data = requests.post(url, files=files).content
            res = json.loads(data)
            os.remove(temp_desc_file)
            if res.get('result') == True:
                return img_id
            return res

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
            url = '{}/image/{}'.format(self.base_url, image_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

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
            url = '{}/image/{}'.format(self.base_url, image_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            '''
            Gets all the images registered in the system catalog

            returns
            -------
            string list
            '''
            url = '{}/image/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class Flavor(object):
        '''
        Class: Flavor
        This class encapsulates API for Flavors
        '''

        def __init__(self, base_url):
            self.base_url = base_url

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
            url = '{}/flavor/add'.format(self.base_url)
            data = requests.post(url, data=json.dumps(descriptor)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def get(self, flavor_id):
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
            url = '{}/flavor/{}'.format(self.base_url, flavor_id)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def remove(self, flavor_id):
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
            url = '{}/flavor/{}'.format(self.base_url, flavor_id)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            '''
            Gets all the flavors registered in the system catalog

            returns
            -------
            string list
            '''
            url = '{}/flavor/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)
