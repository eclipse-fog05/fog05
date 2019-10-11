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

        This class encapsulates the command for Node interaction

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            url = '{}/node/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


        def info(self, node_uuid):
            url = '{}/node/info/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def status(self, node_uuid):
            url = '{}/node/status/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def plugins(self, node_uuid):
            url = '{}/node/plugins/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

    class Plugin(object):
        '''
        This class encapsulates the commands for Plugin interaction

        '''
        def __init__(self, base_url):
            self.base_url = base_url

        def info(self, node_uuid, pluginid):
            url = '{}/plugin/info/{}/{}'.format(self.base_url, pluginid, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class Network(object):
        '''

        This class encapsulates the command for Network element interaction

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add_network(self, manifest):
            url = '{}/network/add'.format(self.base_url)
            data = requests.post(url, data=json.dumps(manifest)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def remove_network(self, net_uuid):
            url = '{}/network/remove/{}'.format(self.base_url, net_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def add_connection_point(self, cp_descriptor):
            url = '{}/connection_point/add'.format(self.base_url)
            data = requests.post(url, data=json.dumps(cp_descriptor)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def delete_connection_point(self, cp_uuid):
            url = '{}/connection_point/remove/{}'.format(self.base_url, cp_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            url = '{}/network/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class FDU(object):
        '''

        This class encapsulates the api for interaction with entities

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def onboard(self, descriptor):
            url = '{}/fdu/onboard'.format(self.base_url)
            data = requests.post(url, data=json.dumps(descriptor)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def offload(self, fdu_uuid):
            url = '{}/fdu/offload/{}'.format(self.base_url, fdu_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def define(self, fduid, node_uuid):
            url = '{}/fdu/define/{}/{}'.format(self.base_url, fduid, node_uuid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def undefine(self, instanceid):
            url = '{}/fdu/undefine/{}'.format(self.base_url, instanceid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res = json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def configure(self, instanceid):
            url = '{}/fdu/configure/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res = json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def clean(self, instanceid):
            url = '{}/fdu/clean/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def start(self, instanceid):
            url = '{}/fdu/start/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def stop(self, instanceid):
            url = '{}/fdu/stop/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def pause(self, instanceid):
            url = '{}/fdu/pause/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def resume(self, instanceid):
            url = '{}/fdu/resume/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def migrate(self, instanceid, destination_node_uuid):
            url = '{}/fdu/migrate/{}/{}'.format(self.base_url, instanceid, destination_node_uuid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def instantiate(self, fduid, nodeid):
            url = '{}/fdu/instantiate/{}/{}'.format(self.base_url, fduid, nodeid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res =  json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def terminate(self, instanceid):
            url = '{}/fdu/terminate/{}'.format(self.base_url, instanceid)
            data = requests.post(url).content
            if isinstance(data,bytes):
                data = data.decode()
            res = json.loads(data)
            if 'error' in res:
                raise ValueError(res['error'])
            return res['result']

        def get_nodes(self, fdu_uuid, node_uuid):
            url = '{}/fdu/get_nodes/{}'.format(self.base_url, fdu_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list_node(self, node_uuid):
            url = '{}/fdu/list_node/{}'.format(self.base_url, node_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def instance_list(self, fduid):
            url = '{}/fdu/instance_list/{}'.format(self.base_url, fduid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def info(self, fdu_uuid):
            url = '{}/fdu/info/{}'.format(self.base_url, fdu_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def instance_info(self, instanceid):
            url = '{}/fdu/instance_info/{}'.format(self.base_url, instanceid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            url = '{}/fdu/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class Image(object):
        '''

        This class encapsulates the action on images


        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor, image_path):
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
            url = '{}/image/{}'.format(self.base_url, image_uuid)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def remove(self, image_uuid):
            url = '{}/image/{}'.format(self.base_url, image_uuid)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            url = '{}/image/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)


    class Flavor(object):
        '''
          This class encapsulates the action on flavors

        '''

        def __init__(self, base_url):
            self.base_url = base_url

        def add(self, descriptor):
            url = '{}/flavor/add'.format(self.base_url)
            data = requests.post(url, data=json.dumps(descriptor)).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def get(self, flavor_id):
            url = '{}/flavor/{}'.format(self.base_url, flavor_id)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def remove(self, flavor_id):
            url = '{}/flavor/{}'.format(self.base_url, flavor_id)
            data = requests.delete(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)

        def list(self):
            url = '{}/flavor/list'.format(self.base_url)
            data = requests.get(url).content
            if isinstance(data,bytes):
                data = data.decode()
            return json.loads(data)
