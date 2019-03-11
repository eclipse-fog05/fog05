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

class FIMAPI(object):
    '''
        This class allow the interaction with fog05 FIM
    '''

    def __init__(self, locator='127.0.0.1:8080',):


        self.base_uri = 'http://{}'.format(locator)
        self.node = self.Node(self.base_uri)
        self.plugin = self.Plugin(self.base_uri)
        self.network = self.Network(self.base_uri)
        self.fdu = self.FDU(self.base_uri)
        self.image = self.Image(self.base_uri)
        self.flavor = self.Flavor(self.base_uri)

    def close(self):
        pass


    class Node(object):
        '''

        This class encapsulates the command for Node interaction

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            url = '{}/node/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))

        def info(self, node_uuid):
            url = '{}/node/info/{}'.format(self.base_url, node_uuid)
            return json.loads(str(requests.get(url).content))

        def plugins(self, node_uuid):
            url = '{}/node/plugins/{}'.format(self.base_url, node_uuid)
            return json.loads(str(requests.get(url).content))

    class Plugin(object):
        '''
        This class encapsulates the commands for Plugin interaction

        '''
        def __init__(self, base_url):
            self.base_url = base_url


        def info(self, node_uuid, pluginid):
            url = '{}/plugin/info/{}/{}'.format(self.base_url, pluginid, node_uuid)
            return json.loads(str(requests.get(url).content))


    class Network(object):
        '''

        This class encapsulates the command for Network element interaction

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add_network(self, manifest):
            uri = '{}/network/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=manifest).content))

        def remove_network(self, net_uuid):
            uri = '{}/network/remove/{}'.format(self.base_url, net_uuid)
            return json.loads(str(requests.delete(url).content))

        def add_connection_point(self, cp_descriptor):
            uri = '{}/connection_point/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=cp_descriptor).content))

        def delete_connection_point(self, cp_uuid):
            uri = '{}/connection_point/remove/{}'.format(self.base_url, cp_uuid)
            return json.loads(str(requests.delete(url).content))


        def list(self):
            uri = '{}/network/list'.format(self.base_url)
            return json.loads(str(requests.post(url).content))


    class FDU(object):
        '''

        This class encapsulates the api for interaction with entities

        '''

        def __init__(self, base_url):
            self.base_url = base_url


        def onboard(self, descriptor):
            uri = '{}/fdu/onboard'.format(self.base_url)
            return json.loads(str(requests.post(url, data=manifest).content))

        def offload(self, fdu_uuid):
            uri = '{}/fdu/offload/{}'.format(self.base_url, fdu_uuid)
            return json.loads(str(requests.delete(url).content))

        def define(self, fduid, node_uuid):
            uri = '{}/fdu/define/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def undefine(self, fdu_uuid, node_uuid):
            uri = '{}/fdu/define/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.delete(url).content))

        def configure(self, fdu_uuid, node_uuid):
            uri = '{}/fdu/configure/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def clean(self, fdu_uuid, node_uuid):
            uri = '{}/fdu/clean/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def run(self, fdu_uuid, node_uuid):
            uri = '{}/fdu/run/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def stop(self, fdu_uuid, node_uuid):
            uri = '{}/fdu/stop/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def pause(self, entity_uuid, node_uuid, instance_uuid):
            uri = '{}/fdu/pause/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def resume(self, entity_uuid, node_uuid, instance_uuid):
            uri = '{}/fdu/resume/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def migrate(self, fduid, node_uuid, destination_node_uuid):
            pass

        def info(self, fdu_uuid):
            uri = '{}/fdu/info/{}'.format(self.base_url, fdu_uuid)
            return json.loads(str(requests.get(url).content))

        def instance_info(self, fdu_uuid, node_uuid):
            uri = '{}/fdu/instance_info/{}/{}'.format(self.base_url, fdu_uuid, node_uuid)
            return json.loads(str(requests.get(url).content))

        def list(self):
            uri = '{}/fdu/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))


    class Image(object):
        '''

        This class encapsulates the action on images


        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor):
            uri = '{}/image/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=manifest).content))

        def get(self, image_uuid):
            uri = '{}/image/{}'.format(self.base_url, image_uuid)
            return json.loads(str(requests.get(url).content))


        def remove(self, image_uuid):
            uri = '{}/image/{}'.format(self.base_url, image_uuid)
            return json.loads(str(requests.delete(url).content))


        def list(self):
            uri = '{}/image/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))


    class Flavor(object):
        '''
          This class encapsulates the action on flavors

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor):
            uri = '{}/flavor/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=manifest).content))

        def get(self, flavor_id):
            uri = '{}/flavor/{}'.format(self.base_url, flavor_id)
            return json.loads(str(requests.get(url).content))

        def remove(self, flavor_id):
            uri = '{}/flavor/{}'.format(self.base_url, flavor_id)
            return json.loads(str(requests.delete(url).content))

        def list(self):
            uri = '{}/flavor/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))
