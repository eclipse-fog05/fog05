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


        self.base_url = 'http://{}'.format(locator)
        self.node = self.Node(self.base_url)
        self.plugin = self.Plugin(self.base_url)
        self.network = self.Network(self.base_url)
        self.fdu = self.FDU(self.base_url)
        self.image = self.Image(self.base_url)
        self.flavor = self.Flavor(self.base_url)

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

        def status(self, node_uuid):
            url = '{}/node/status/{}'.format(self.base_url, node_uuid)
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
            url = '{}/network/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=json.dumps(manifest)).content))

        def remove_network(self, net_uuid):
            url = '{}/network/remove/{}'.format(self.base_url, net_uuid)
            return json.loads(str(requests.delete(url).content))

        def add_connection_point(self, cp_descriptor):
            url = '{}/connection_point/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=json.dumps(cp_descriptor)).content))

        def delete_connection_point(self, cp_uuid):
            url = '{}/connection_point/remove/{}'.format(self.base_url, cp_uuid)
            return json.loads(str(requests.delete(url).content))


        def list(self):
            url = '{}/network/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))


    class FDU(object):
        '''

        This class encapsulates the api for interaction with entities

        '''

        def __init__(self, base_url):
            self.base_url = base_url


        def onboard(self, descriptor):
            url = '{}/fdu/onboard'.format(self.base_url)
            return json.loads(str(requests.post(url, data=json.dumps(descriptor)).content))

        def offload(self, fdu_uuid):
            url = '{}/fdu/offload/{}'.format(self.base_url, fdu_uuid)
            return json.loads(str(requests.delete(url).content))

        def define(self, fduid, node_uuid):
            url = '{}/fdu/define/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def undefine(self, fduid, node_uuid):
            url = '{}/fdu/undefine/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.delete(url).content))

        def configure(self, fduid, node_uuid):
            url = '{}/fdu/configure/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def clean(self, fduid, node_uuid):
            url = '{}/fdu/clean/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def run(self, fduid, node_uuid):
            url = '{}/fdu/run/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def stop(self, fduid, node_uuid):
            url = '{}/fdu/stop/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def pause(self, fduid, node_uuid):
            url = '{}/fdu/pause/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def resume(self, fduid, node_uuid):
            url = '{}/fdu/resume/{}/{}'.format(self.base_url, fduid, node_uuid)
            return json.loads(str(requests.post(url).content))

        def migrate(self, fduid, node_uuid, destination_node_uuid):
            pass

        def info(self, fdu_uuid):
            url = '{}/fdu/info/{}'.format(self.base_url, fdu_uuid)
            return json.loads(str(requests.get(url).content))

        def instance_info(self, fdu_uuid, node_uuid):
            url = '{}/fdu/instance_info/{}/{}'.format(self.base_url, fdu_uuid, node_uuid)
            return json.loads(str(requests.get(url).content))

        def list(self):
            url = '{}/fdu/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))


    class Image(object):
        '''

        This class encapsulates the action on images


        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor):
            url = '{}/image/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=json.dumps(descriptor)).content))

        def get(self, image_uuid):
            url = '{}/image/{}'.format(self.base_url, image_uuid)
            return json.loads(str(requests.get(url).content))


        def remove(self, image_uuid):
            url = '{}/image/{}'.format(self.base_url, image_uuid)
            return json.loads(str(requests.delete(url).content))


        def list(self):
            url = '{}/image/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))


    class Flavor(object):
        '''
          This class encapsulates the action on flavors

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor):
            url = '{}/flavor/add'.format(self.base_url)
            return json.loads(str(requests.post(url, data=json.dumps(descriptor)).content))

        def get(self, flavor_id):
            url = '{}/flavor/{}'.format(self.base_url, flavor_id)
            return json.loads(str(requests.get(url).content))

        def remove(self, flavor_id):
            url = '{}/flavor/{}'.format(self.base_url, flavor_id)
            return json.loads(str(requests.delete(url).content))

        def list(self):
            url = '{}/flavor/list'.format(self.base_url)
            return json.loads(str(requests.get(url).content))
