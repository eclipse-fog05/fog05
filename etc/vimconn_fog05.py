# -*- coding: utf-8 -*-

##
# Copyright 2018 ADLINK Technologies Inc.
# This file is part of ETSI OSM
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact with: nfvlabs@tid.es
##

"""
vimconn_fog05

@GB Should this use the dstore webservice for the comunication with fog05.
This will simplify a lot the interaction between fog05 and openMANO, and should be also seamless

Or we can create an REST HTTP API for fog05 mapped over the Python one


"""
__author__ = "Gabriele Baldoni"
__date__ = "$19-jan-2018 17:11:59$"

import logging
import paramiko
import socket
import StringIO
import yaml
import sys
import vimconn
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import randint
import asyncio
import websockets
from jsonschema import validate, ValidationError
from fog05 import Schemas
import uuid
import json
import fnmatch
import re
import time

# from fog05.DStore import *

# Error variables
HTTP_Bad_Request = 400
HTTP_Unauthorized = 401
HTTP_Not_Found = 404
HTTP_Method_Not_Allowed = 405
HTTP_Request_Timeout = 408
HTTP_Conflict = 409
HTTP_Not_Implemented = 501
HTTP_Service_Unavailable = 503
HTTP_Internal_Server_Error = 500

# staring with status mapping
#     UNDEFINED: "Not in fog05 domain",
#     DEFINED: "image/data loaded by fog05 also 'flavor' defined",
#     CONFIGURED: "Ready to be started, mean instance created at plugin level (outside fog05 domain eg. kvm, lxd...)",
#     RUNNING: "The atomic entity is running",
#     PAUSED: "Suspended",
#     MIGRATING: "the atomic entity is migrating from two fog05 nodes",
#     SCALING: "atmoic entity is scalig",
#     TAKING_OFF: "migration state in source node",
#     LANDING: "migration state in destination node",

atomicEntityStatus2manoFormat = {'RUNNING': 'ACTIVE',
                                 'PAUSED': 'PAUSED',
                                 'STOPPED': 'SUSPENDED',
                                 'CONFIGURED': 'INACTIVE',
                                 'DEFINED': 'BUILD',
                                 'ERROR': 'ERROR', 'DELETED': 'DELETED'  # should add error status? deleted can also defined, depends if referred to entity instance or to entity
                                 }

# no network state machine ant the moment
netStatus2manoFormat = {'ACTIVE': 'ACTIVE', 'PAUSED': 'PAUSED', 'INACTIVE': 'INACTIVE', 'BUILD': 'BUILD', 'ERROR': 'ERROR', 'DELETED': 'DELETED'
                        }


class WSStore(object):
    def __init__(self, sid, root, home, host):
        self.sid = sid
        self.root = root
        self.home = home
        self.host = host
        # self.websocket = websockets.connect('ws://{}:9669'.format(host))

    @asyncio.coroutine
    def create(self):
        cmd = 'create {} {} {} 1024'.format(self.sid, self.root, self.home)
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        response = response.split(' ')
        if response[0] == 'OK':
            return True
        elif response[0] == 'NOK':
            return False
        else:
            print("Wrong response from the server {}".format(''.join(response)))
            return False

    @asyncio.coroutine
    def keys(self):
        cmd = 'gkeys {}'.format(self.sid)
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        response = response.split(' ')
        keys = response[-1].split('|')
        return keys

    @asyncio.coroutine
    def put(self, uri, val):
        cmd = 'put {} {} {}'.format(self.sid, uri, val)
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        response = response.split(' ')

        if response[0] == 'OK':
            return True
        elif response[0] == 'NOK':
            return False
        else:
            print("Wrong response from the server {}".format(''.join(response)))
            return False

    @asyncio.coroutine
    def dput(self, uri, value=None):
        cmd = 'dput {} {}'.format(self.sid, uri)
        if value is not None:
            cmd = str('{} {}'.format(cmd, value))
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        response = response.split(' ')

        if response[0] == 'OK':
            return True
        elif response[0] == 'NOK':
            return False
        else:
            print("Wrong response from the server {}".format(''.join(response)))
            return False

    @asyncio.coroutine
    def get(self, uri):
        cmd = 'get {} {}'.format(self.sid, uri)

        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()

        infos = response.split(uri)[-1]
        if infos in ['', ' ']:
            return None
        infos = infos.replace(' ', '')
        if infos is not None and infos != '':
            return infos
        else:
            return None

    @asyncio.coroutine
    def resolve(self, uri):
        cmd = 'resolve {} {}'.format(self.sid, uri)

        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()

        infos = response.split(uri)[-1]
        if infos in ['', ' ']:
            return None
        infos = infos.replace(' ', '')
        if infos is not None and infos != '':
            return infos
        else:
            return None

    @asyncio.coroutine
    def getAll(self, uri):
        cmd = 'aget {0} {1}'.format(self.sid, uri)
        values = []
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        infos = response.split(uri)[-1].replace(' ', '')
        if infos is not None and infos != '':
            nodes_list = infos.split('|')
            for e in nodes_list:
                i = e.split('@')
                if len(i) > 1:
                    if i[1] is not None and i[1] not in ['', ' ', 'None']:
                        v = []
                        v.append(i[0])
                        v.append(''.join(i[1:]))
                        values.append(tuple(v))

        return tuple(values)

    @asyncio.coroutine
    def resolveAll(self, uri):
        cmd = 'aresolve {0} {1}'.format(self.sid, uri)
        values = []
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        infos = response.split(uri)[-1].replace(' ', '')
        if infos is not None and infos != '':
            nodes_list = infos.split('|')
            for e in nodes_list:
                i = e.split('@')
                if len(i) > 1:
                    if i[1] is not None and i[1] not in ['', ' ', 'None']:
                        v = []
                        v.append(i[0])
                        v.append(''.join(i[1:]))
                        values.append(tuple(v))

        return tuple(values)

    @asyncio.coroutine
    def remove(self, uri):
        cmd = 'remove {} {}'.format(self.sid, uri)
        ws = yield from websockets.connect('ws://{}:9669'.format(self.host))
        yield from ws.send(cmd)
        response = yield from ws.recv()
        response = response.split(' ')
        if response[0] == 'OK':
            return True
        elif response[0] == 'NOK':
            return False
        else:
            print("Wrong response from the server {}".format(''.join(response)))
            return False


class FOSStore(object):
    def __init__(self, aroot, droot, home, host):
        self.aroot = aroot  # '//dfos/<sys-id>'
        self.ahome = str('{}/{}'.format(aroot, home))  # str('//dfos/<sys-id>/{}' % self.uuid)

        self.droot = droot  # '//dfos/<sys-id>'
        self.dhome = str('{}/{}'.format(droot, home))  # str('//dfos/<sys-id>/{}' % self.uuid)

        self.actual = WSStore('a{}'.format(home), self.aroot, self.ahome, host)
        self.desired = WSStore('d{}'.format(home), self.droot, self.dhome, host)

    def close(self):
        pass
        # self.actual.close()
        # self.desidered.close()


class vimconnector(vimconn.vimconnector):
    """Implementing the abstract calss
    """

    def __init__(self, uuid, name, tenant_id, tenant_name, url, url_admin=None, user=None, passwd=None, log_level=None,
                 config={}, persitent_info={}):
        """Constructor of VIM
        Params:
            'uuid': id asigned to this VIM
            'name': name assigned to this VIM, can be used for logging
            'tenant_id', 'tenant_name': (only one of them is mandatory) VIM tenant to be used
            'url_admin': (optional), url used for administrative tasks
            'user', 'passwd': credentials of the VIM user
            'log_level': provider if it should use a different log_level than the general one
            'config': dictionary with extra VIM information. This contains a consolidate version of general VIM config
                    at creation and particular VIM config at teh attachment
            'persistent_info': dict where the class can store information that will be available among class
                    destroy/creation cycles. This info is unique per VIM/credential. At first call it will contain an
                    empty dict. Useful to store login/tokens information for speed up communication

        Returns: Raise an exception is some needed parameter is missing, but it must not do any connectivity
            check against the VIM
        """

        """
            url should be the web service url in a way to allow the use of the web service for the interaction with the distributed store.
            TODO: for security reasons should implement access controll to the store 

            inside configuration we can have information on store root and home

        """
        sid = config.get('sid')
        if sid is None:
            raise vimconn.vimconnException("Invalid value '{}' for config:sid. "
                                           "Should provide the store id".format(sid))

        root = config.get('root')
        if root is None:
            raise vimconn.vimconnException("Invalid value '{}' for config:root."
                                           "Should provide the store root".format(root))

        home = config.get('home')
        if home is None:
            raise vimconn.vimconnException("Invalid value '{}' for config:home."
                                           "Should provide the store home".format(home))

        vimconn.vimconnector.__init__(self, uuid, name, tenant_id, tenant_name, url, url_admin, user, passwd, log_level, config)

        self.home = home
        self.root = root
        self.aroot = '//afos/{}'.format(self.root)
        self.droot = '//dfos/{}'.format(self.root)
        self.sid = sid

        if not self.url:
            raise TypeError('url param can not be NoneType')

        self.logger = logging.getLogger('openmano.vim.fog05')

        self.store = FOSStore(self.aroot, self.droot, self.uuid, self.url)
        asyncio.get_event_loop().run_until_complete(self.store.desired.create())
        asyncio.get_event_loop().run_until_complete(self.store.actual.create())

    def __getitem__(self, index):
        if index == 'tenant_id':
            return self.tenant_id
        if index == 'tenant_name':
            return self.tenant_name
        elif index == 'id':
            return self.id
        elif index == 'name':
            return self.name
        elif index == 'user':
            return self.user
        elif index == 'passwd':
            return self.passwd
        elif index == 'url':
            return self.url
        elif index == 'url_admin':
            return self.url_admin
        elif index == "config":
            return self.config
        else:
            raise KeyError("Invalid key '%s'" % str(index))

    def __setitem__(self, index, value):
        if index == 'tenant_id':
            self.tenant_id = value
        if index == 'tenant_name':
            self.tenant_name = value
        elif index == 'id':
            self.id = value
        elif index == 'name':
            self.name = value
        elif index == 'user':
            self.user = value
        elif index == 'passwd':
            self.passwd = value
        elif index == 'url':
            self.url = value
        elif index == 'url_admin':
            self.url_admin = value
        else:
            raise KeyError("Invalid key '%s'" % str(index))

    @staticmethod
    def _create_mimemultipart(content_list):
        """Creates a MIMEmultipart text combining the content_list
        :param content_list: list of text scripts to be combined
        :return: str of the created MIMEmultipart. If the list is empty returns None, if the list contains only one
        element MIMEmultipart is not created and this content is returned
        """
        if not content_list:
            return None
        elif len(content_list) == 1:
            return content_list[0]
        combined_message = MIMEMultipart()
        for content in content_list:
            if content.startswith('#include'):
                format = 'text/x-include-url'
            elif content.startswith('#include-once'):
                format = 'text/x-include-once-url'
            elif content.startswith('#!'):
                format = 'text/x-shellscript'
            elif content.startswith('#cloud-config'):
                format = 'text/cloud-config'
            elif content.startswith('#cloud-config-archive'):
                format = 'text/cloud-config-archive'
            elif content.startswith('#upstart-job'):
                format = 'text/upstart-job'
            elif content.startswith('#part-handler'):
                format = 'text/part-handler'
            elif content.startswith('#cloud-boothook'):
                format = 'text/cloud-boothook'
            else:  # by default
                format = 'text/x-shellscript'
            sub_message = MIMEText(content, format, sys.getdefaultencoding())
            combined_message.attach(sub_message)
        return combined_message.as_string()

    def _create_user_data(self, cloud_config):
        """
        Creates a script user database on cloud_config info
        :param cloud_config: dictionary with
            'key-pairs': (optional) list of strings with the public key to be inserted to the default user
            'users': (optional) list of users to be inserted, each item is a dict with:
                'name': (mandatory) user name,
                'key-pairs': (optional) list of strings with the public key to be inserted to the user
            'user-data': (optional) can be a string with the text script to be passed directly to cloud-init,
                or a list of strings, each one contains a script to be passed, usually with a MIMEmultipart file
            'config-files': (optional). List of files to be transferred. Each item is a dict with:
                'dest': (mandatory) string with the destination absolute path
                'encoding': (optional, by default text). Can be one of:
                    'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                'content' (mandatory): string with the content of the file
                'permissions': (optional) string with file permissions, typically octal notation '0644'
                'owner': (optional) file owner, string with the format 'owner:group'
            'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk)
        :return: config_drive, userdata. The first is a boolean or None, the second a string or None
        """
        config_drive = None
        userdata = None
        userdata_list = []
        if isinstance(cloud_config, dict):
            if cloud_config.get("user-data"):
                if isinstance(cloud_config["user-data"], str):
                    userdata_list.append(cloud_config["user-data"])
                else:
                    for u in cloud_config["user-data"]:
                        userdata_list.append(u)
            if cloud_config.get("boot-data-drive") != None:
                config_drive = cloud_config["boot-data-drive"]
            if cloud_config.get("config-files") or cloud_config.get("users") or cloud_config.get("key-pairs"):
                userdata_dict = {}
                # default user
                if cloud_config.get("key-pairs"):
                    userdata_dict["ssh-authorized-keys"] = cloud_config["key-pairs"]
                    userdata_dict["users"] = [{"default": None, "ssh-authorized-keys": cloud_config["key-pairs"]}]
                if cloud_config.get("users"):
                    if "users" not in userdata_dict:
                        userdata_dict["users"] = ["default"]
                    for user in cloud_config["users"]:
                        user_info = {
                            "name": user["name"],
                            "sudo": "ALL = (ALL)NOPASSWD:ALL"
                        }
                        if "user-info" in user:
                            user_info["gecos"] = user["user-info"]
                        if user.get("key-pairs"):
                            user_info["ssh-authorized-keys"] = user["key-pairs"]
                        userdata_dict["users"].append(user_info)

                if cloud_config.get("config-files"):
                    userdata_dict["write_files"] = []
                    for file in cloud_config["config-files"]:
                        file_info = {
                            "path": file["dest"],
                            "content": file["content"]
                        }
                        if file.get("encoding"):
                            file_info["encoding"] = file["encoding"]
                        if file.get("permissions"):
                            file_info["permissions"] = file["permissions"]
                        if file.get("owner"):
                            file_info["owner"] = file["owner"]
                        userdata_dict["write_files"].append(file_info)
                userdata_list.append("#cloud-config\n" + yaml.safe_dump(userdata_dict, indent=4,
                                                                        default_flow_style=False))
            userdata = self._create_mimemultipart(userdata_list)
            self.logger.debug("userdata: %s", userdata)
        elif isinstance(cloud_config, str):
            userdata = cloud_config
        return config_drive, userdata

    @asyncio.coroutine
    def __get_all_node_plugin(self, node_uuid):
        uri = '{}/{}/plugins'.format(self.aroot, node_uuid)
        response = yield from self.store.actual.get(uri)
        if response is not None and response != '':
            return json.loads(response).get('plugins')
        else:
            return None

    @asyncio.coroutine
    def __send_add_network(self, node_uuid, manifest):

        manifest.update({'status': 'add'})
        all_plugins = yield from self.__get_all_node_plugin(node_uuid)
        if all_plugins is None:
            print('Error on receive plugin from node')
            return
        nws = [x for x in all_plugins if x.get('type') == 'network']
        if len(nws) == 0:
            print('No network plugin loaded on node, aborting')
            return
        brctl = nws[0]  # will use the first plugin

        json_data = json.dumps(manifest).replace(' ', '')
        uri = '{}/{}/network/{}/networks/{}'.format(self.droot, node_uuid, brctl.get('uuid'), manifest.get('uuid'))

        res = yield from self.store.desired.put(uri, json_data)

        return res

    @asyncio.coroutine
    def __send_remove_network(self, node_uuid, net_id):

        all_plugins = yield from self.__get_all_node_plugin(node_uuid)
        if all_plugins is None:
            print('Error on receive plugin from node')
            return
        nws = [x for x in all_plugins if x.get('type') == 'network']
        # print('locating brctl plugin')
        search = [x for x in nws if 'brctl' in x.get('name')]
        # print(search)
        if len(search) == 0:
            print('Plugin was not loaded')
            return
        else:
            brctl = search[0]

        uri = '{}/{}/network/{}/networks/{}'.format(self.droot, node_uuid, brctl.get('uuid'), net_id)
        res = yield from self.store.desired.remove(uri)
        return res

    @asyncio.coroutine
    def __get_nodes(self):
        uri = '{}/*/'.format(self.aroot)
        n = []
        infos = yield from self.store.actual.resolveAll(uri)
        if infos is not None and infos != '' and len(infos) > 0:
            for e in infos:
                node_info = json.loads(e[1])
                n.append(node_info.get('uuid'))
        return n

    @asyncio.coroutine
    def __get_networks(self):
        uri = '{}/*/network/*/networks/*/'.format(self.aroot)
        nws = []
        nw_list = yield from self.store.actual.resolveAll(uri)
        if nw_list is not None and len(nw_list) > 0:
            for e in nw_list:
                nws.append(json.loads(e[1]))
        return nws

    @asyncio.coroutine
    def __get_network(self, net_uuid):
        # TODO should return only one network
        uri = '{}/*/network/*/networks/{}/'.format(self.aroot, net_uuid)
        nws = []
        nw_list = yield from self.store.actual.resolveAll(uri)
        if nw_list is not None and len(nw_list) > 0:
            for e in nw_list:
                nws.append(json.loads(e[1]))
            return nws[0]
        return None

    @asyncio.coroutine
    def __get_flavors(self):
        uri = '{}/*/runtime/*/flavor/*/'.format(self.aroot)
        fls = []
        fl_list = yield from self.store.actual.resolveAll(uri)
        if fl_list is not None and len(fl_list) > 0:
            for f in fl_list:
                fls.append(json.loads(f[1]))
        return fls

    @asyncio.coroutine
    def __get_flavor(self, flavor_uuid):
        uri = '{}/*/runtime/*/flavor/{}'.format(self.aroot, flavor_uuid)
        fls = []
        fl_list = yield from self.store.actual.resolveAll(uri)
        if fl_list is not None and len(fl_list) > 0:
            for f in fl_list:
                fls.append(json.loads(f[1]))
            return fls[0]
        if fl_list is None:
            return None

    @asyncio.coroutine
    def __send_add_flavor(self, manifest):
        manifest.update({'status': 'add'})
        json_data = json.dumps(manifest).replace(' ', '')
        uri = '{}/*/runtime/*/flavor/{}'.format(self.droot, manifest.get('uuid'))
        res = yield from self.store.desired.put(uri, json_data)
        return res

    @asyncio.coroutine
    def __send_add_flavor_node(self, node_uuid, manifest):
        manifest.update({'status': 'add'})
        json_data = json.dumps(manifest).replace(' ', '')

        all_plugins = yield from self.__get_all_node_plugin(node_uuid)
        if all_plugins is None:
            print('Error on receive plugin from node')
            return
        rts = [x for x in all_plugins if x.get('type') == 'runtime' and x.get('name') in ['KVMLibvirt', 'XENLibvirt']]
        for r in rts:
            uri = '{}/{}/runtime/{}/flavor/{}'.format(self.droot, node_uuid, r.get('uuid'), manifest.get('uuid'))
            yield from self.store.desired.put(uri, json_data)
        # TODO fix this
        return True

    @asyncio.coroutine
    def __send_remove_flavor_node(self, node_uuid, flavor_id):
        all_plugins = yield from self.__get_all_node_plugin(node_uuid)
        if all_plugins is None:
            print('Error on receive plugin from node')
            return
        rts = [x for x in all_plugins if x.get('type') == 'runtime' and x.get('name') in ['KVMLibvirt', 'XENLibvirt']]
        for r in rts:
            uri = '{}/{}/runtime/{}/flavor/{}'.format(self.droot, node_uuid, r.get('uuid'), flavor_id)
            yield from self.store.desired.remove(uri)
        # TODO fix this
        return True

    @asyncio.coroutine
    def __send_add_image(self, manifest):
        manifest.update({'status': 'add'})
        json_data = json.dumps(manifest).replace(' ', '')
        uri = '{}/*/runtime/*/image/{}'.format(self.droot, manifest.get('uuid'))
        res = yield from self.store.desired.put(uri, json_data)
        return res

    @asyncio.coroutine
    def __send_add_image_node(self, node_uuid, manifest):
        manifest.update({'status': 'add'})
        json_data = json.dumps(manifest).replace(' ', '')

        all_plugins = yield from self.__get_all_node_plugin(node_uuid)
        if all_plugins is None:
            print('Error on receive plugin from node')
            return
        rts = [x for x in all_plugins if x.get('type') == 'runtime' and x.get('name') in ['KVMLibvirt', 'XENLibvirt']]
        for r in rts:
            uri = '{}/{}/runtime/{}/image/{}'.format(self.droot, node_uuid, r.get('uuid'), manifest.get('uuid'))
            yield from self.store.desired.put(uri, json_data)
        # TODO fix this
        return True

    @asyncio.coroutine
    def __get_images(self):
        uri = '{}/*/runtime/*/image/*/'.format(self.aroot)
        imgs = []
        img_list = yield from self.store.actual.resolveAll(uri)
        if img_list is not None and len(img_list) > 0:
            for i in img_list:
                imgs.append(json.loads(i[1]))
        return imgs

    @asyncio.coroutine
    def __get_image(self, image_uuid):
        uri = '{}/*/runtime/*/image/{}'.format(self.aroot, image_uuid)
        imgs = []
        img_list = yield from self.store.actual.resolveAll(uri)
        if img_list is not None and len(img_list) > 0:
            for i in img_list:
                imgs.append(json.loads(i[1]))
            return imgs[0]
        if img_list is None:
            return None

    @asyncio.coroutine
    def __send_remove_image(self, image_uuid):
        uri = '{}/*/runtime/*/image/{}'.format(self.droot, image_uuid)
        res = self.store.actual.remove(uri)
        return res

    @asyncio.coroutine
    def __send_remove_image_node(self, node_uuid, image_uuid):
        all_plugins = yield from self.__get_all_node_plugin(node_uuid)
        if all_plugins is None:
            print('Error on receive plugin from node')
            return
        rts = [x for x in all_plugins if x.get('type') == 'runtime' and x.get('name') in ['KVMLibvirt', 'XENLibvirt']]
        for r in rts:
            uri = '{}/{}/runtime/{}/image/{}'.format(self.droot, node_uuid, r.get('uuid'), image_uuid)
            yield from self.store.desired.remove(uri)
        # TODO fix this
        return True

    @asyncio.coroutine
    def __get_instance(self, instance_uuid):
        uri = '{}/*/runtime/*/entity/*/{}'.format(self.aroot, instance_uuid)
        instances = []
        i_list = yield from self.store.actual.resolveAll(uri)
        if i_list is not None and len(i_list) > 0:
            for f in i_list:
                instances.append(json.loads(f[1]))
        return instances

    @asyncio.coroutine
    def __get_instances(self):
        uri = '{}/*/runtime/*/entity/*/*'.format(self.aroot)
        instances = []
        i_list = yield from self.store.actual.resolveAll(uri)
        if i_list is not None and len(i_list) > 0:
            for f in i_list:
                instances.append(json.loads(f[1]))
            return instances[0]
        if i_list is None:
            return None

    def __get_node(self, elegible_nodes):
        i = randint(0, len(elegible_nodes))
        return elegible_nodes[i]

    def __get_eligible_nodes(self, nodes, entity_manifest):
        eligible = []

        nw_eligible = []
        ac_eligible = []
        io_eligible = []

        constraints = entity_manifest.get("constraints", None)
        if constraints is None:
            return nodes

        o_s = constraints.get('os')
        if o_s is not None:
            nodes = [x for x in nodes if x.get('os') == o_s]

        arch = constraints.get("arch")
        if arch is not None:
            nodes = [x for x in nodes if x.get('hardware_specifications').get('cpu')[0].get('arch') == arch]

        for node in nodes:
            nw_constraints = constraints.get('networks', None)
            node_nw = node.get('network', None)
            if nw_constraints is not None and node_nw is not None:
                for nw_c in nw_constraints:
                    t = nw_c.get('type')
                    n = nw_c.get('number')
                    nws = [x for x in node_nw if x.get('type') == t and x.get('available') is True]
                    if len(nws) >= n:
                        nw_eligible.append(node.get('uuid'))
            io_constraints = constraints.get('i/o', None)
            node_io = node.get('io', None)
            if io_constraints is not None and node_io is not None:
                for io_c in io_constraints:
                    t = io_c.get('type')
                    n = io_c.get('number')
                    ios = [x for x in node_io if x.get('io_type') == t and x.get('available') is True]
                    if len(ios) >= n:
                        io_eligible.append(node.get('uuid'))
            ac_constraints = constraints.get('accelerators', None)
            node_ac = node.get('accelerator', None)
            if ac_constraints is not None and node_ac is not None:
                node_ac = [x.get('supported_library') for x in node_ac and x.get('available') is True]
                node_sl = []
                for sl in node_ac:
                    node_sl.extend(sl)
                for ac_c in ac_constraints:
                    t = ac_c.get('type')
                    # n = ac_c.get('number')
                    if t in node_sl:
                        ac_eligible.append(node.get('uuid'))
                        # ios = [x for x in node_ac if x.get('type') == t]
                        # if len(ios) >= n:
                        #    ac_elegibles.append(n.get('uuid'))

        if constraints.get('networks', None) is not None and constraints.get('i/o', None) is None and constraints.get(
                'accelerators', None) is None:
            eligible.extend(nw_eligible)
        elif constraints.get('i/o', None) is not None and constraints.get('networks', None) is None and constraints.get(
                'accelerators', None) is None:
            eligible.extend(io_eligible)
        elif constraints.get('accelerators', None) is not None and constraints.get('networks',
                                                                                   None) is None and constraints.get(
            'i/o', None) is None:
            eligible.extend(ac_eligible)
        elif constraints.get('networks', None) is not None and constraints.get('i/o',
                                                                               None) is not None and constraints.get(
            'accelerators', None) is not None:
            eligible = list((set(nw_eligible) & set(io_eligible)) & set(ac_eligible))
        elif constraints.get('networks', None) is not None and constraints.get('i/o',
                                                                               None) is not None and constraints.get(
            'accelerators', None) is None:
            eligible = list(set(nw_eligible) & set(io_eligible))
        elif constraints.get('networks', None) is None and constraints.get('i/o', None) is not None and constraints.get(
                'accelerators', None) is not None:
            eligible = list(set(ac_eligible) & set(io_eligible))
        elif constraints.get('networks', None) is not None and constraints.get('i/o', None) is None and constraints.get(
                'accelerators', None) is not None:
            eligible = list(set(nw_eligible) & set(ac_eligible))
        eligible = list(set(eligible))
        return eligible

    @asyncio.coroutine
    def __search_plugin_by_name(self, name, node_uuid):
        uri = '{}/{}/plugins'.format(self.aroot, node_uuid)
        all_plugins = yield from self.store.actual.get(uri)
        # cmd = 'get {0} {1}'.format(self.asid, uri)
        # with self.websocket as ws:
        #     await ws.send(cmd)
        #     response = await ws.recv()
        # all_plugins = response.split(uri)[-1].replace(' ','')
        if all_plugins is None or all_plugins == '':
            print('Cannot get plugin')
            return None
        all_plugins = json.loads(all_plugins).get('plugins')
        search = [x for x in all_plugins if name.upper() in x.get('name').upper()]
        if len(search) == 0:
            return None
        else:
            return search[0]

    @asyncio.coroutine
    def __get_entity_handler_by_uuid(self, node_uuid, entity_uuid):
        uri = '{}/{}/runtime/*/entity/{}'.format(self.aroot, node_uuid, entity_uuid)
        all = yield from self.store.actual.resolveAll(uri)
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

    @asyncio.coroutine
    def __get_entity_handler_by_type(self, node_uuid, t):
        handler = None

        handler = yield from self.__search_plugin_by_name(t, node_uuid)
        if handler is None:
            print('type not yet supported')
        return handler

    @asyncio.coroutine
    def __send_define_entity(self, node_uuid, manifest):
        manifest.update({'status': 'define'})
        handler = None
        t = manifest.get('type')

        try:
            if t in ['kvm', 'xen']:
                handler = yield from self.__search_plugin_by_name(t, node_uuid)
                validate(manifest.get('entity_data'), Schemas.vm_schema)
            elif t in ['container', 'lxd']:
                handler = yield from self.__search_plugin_by_name(t, node_uuid)
                validate(manifest.get('entity_data'), Schemas.container_schema)
            elif t == 'native':
                handler = yield from self.__search_plugin_by_name('native', node_uuid)
                validate(manifest.get('entity_data'), Schemas.native_schema)
            elif t == 'ros2':
                handler = yield from self.__search_plugin_by_name('ros2', node_uuid)
                validate(manifest.get('entity_data'), Schemas.ros2_schema)
            elif t == 'usvc':
                print('microservice not yet')
            else:
                print('type not recognized')

            if handler is None:
                print('error on plugin for this type of entity')
                self.exit(-1)
        except ValidationError as ve:
            self.logger.error('Manifest error {}', format(ve.message))
            return False

        entity_uuid = manifest.get('uuid')
        entity_definition = manifest
        json_data = json.dumps(entity_definition).replace(' ', '')
        uri = '{}/{}/runtime/{}/entity/{}'.format(self.droot, node_uuid, handler.get('uuid'), entity_uuid)

        res = yield from self.store.desired.put(uri, json_data)
        if res:
            while True:
                time.sleep(1)
                uri = '{}/{}/runtime/{}/entity/{}'.format(self.aroot, node_uuid, handler.get('uuid'), entity_uuid)
                data = yield from self.store.actual.get(uri)
                entity_info = None
                if data is not None:
                    entity_info = json.loads(data)
                if entity_info is not None and entity_info.get('status') == 'defined':
                    break
            return True
        else:
            return False

    @asyncio.coroutine
    def __send_undefine_entity(self, node_uuid, entity_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}'.format(self.droot, node_uuid, handler, entity_uuid)

        res = yield from self.store.desired.remove(uri)
        if res:
            return True
        else:
            return False

    @asyncio.coroutine
    def __send_configure_entity(self, node_uuid, entity_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)
        res = yield from self.store.desired.dput(uri)
        if res:
            while True:
                time.sleep(1)
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                data = yield from self.store.actual.get(uri)
                entity_info = None
                if data is not None:
                    entity_info = json.loads(data)
                if entity_info is not None and entity_info.get('status') == 'configured':
                    break
            return True
        else:
            return False

    @asyncio.coroutine
    def __send_clean_entity(self, node_uuid, entity_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, node_uuid, handler, entity_uuid, instance_uuid)
        res = yield from self.store.desired.remove(uri)
        if res:
            return True
        else:
            return False

    @asyncio.coroutine
    def __send_run_entity(self, node_uuid, entity_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)

        res = yield from self.store.desired.dput(uri)
        if res:
            while True:
                time.sleep(1)
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                data = yield from self.store.actual.get(uri)
                entity_info = None
                if data is not None:
                    entity_info = json.loads(data)
                if entity_info is not None and entity_info.get('status') == 'run':
                    break
            return True
        else:
            return False

    @asyncio.coroutine
    def __send_stop_entity(self, node_uuid, entity_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=stop'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)
        res = yield from self.store.desired.dput(uri)
        if res:
            while True:
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                data = yield from self.store.actual.get(uri)
                entity_info = None
                if data is not None:
                    entity_info = json.loads(data)
                if entity_info is not None and entity_info.get('status') == 'stop':
                    break
            return True
        else:
            return False

    @asyncio.coroutine
    def __sent_migrate_entity(self, node_uuid, entity_uuid, destination_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)

        entity_info = yield from self.store.actual.get(uri)
        if entity_info is None:
            print("Error on getting instance info")
            self.exit(-1)

        entity_info = json.loads(entity_info)

        entity_info_src = entity_info.copy()
        entity_info_dst = entity_info.copy()

        entity_info_src.update({"status": "taking_off"})
        entity_info_src.update({"dst": destination_uuid})

        entity_info_dst.update({"status": "landing"})
        entity_info_dst.update({"dst": destination_uuid})

        destination_handler = yield from self.__get_entity_handler_by_type(destination_uuid, entity_info_dst.get('type'))
        if destination_handler is None:
            self.logger.error("Error Destination node can't handle this type of entity {0}".format(entity_info_dst.get('type')))
            return False

        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.droot, destination_uuid, destination_handler.get(
            'uuid'), entity_uuid, instance_uuid)
        res = yield from self.store.desired.put(uri, json.dumps(entity_info_dst).replace(' ', ''))
        if res:
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res_dest = yield from self.store.desired.dput(uri, json.dumps(entity_info_src).replace(' ', ''))
            if res_dest:
                while True:
                    time.sleep(1)
                    uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, destination_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid)
                    data = yield from self.store.actual.get(uri)
                    entity_info = None
                    if data is not None:
                        entity_info = json.loads(data)
                    if entity_info is not None and entity_info.get("status") == "run":
                        break
                return True
            else:
                return False
        else:
            return False

    @asyncio.coroutine
    def __send_pause_entity(self, node_uuid, entity_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=pause'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)
        res = yield from self.store.desired.dput(uri)
        if res:
            while True:
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                data = yield from self.store.actual.get(uri)
                entity_info = None
                if data is not None:
                    entity_info = json.loads(data)
                if entity_info is not None and entity_info.get('status') == 'pause':
                    break
            return True
        else:
            return False

    @asyncio.coroutine
    def __send_resume_entity(self, node_uuid, entity_uuid, instance_uuid):
        handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
        uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=resume'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)
        res = yield from self.store.desired.dput(uri)
        if res:
            while True:
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                data = yield from self.store.actual.get(uri)
                entity_info = None
                if data is not None:
                    entity_info = json.loads(data)
                if entity_info is not None and entity_info.get('status') == 'run':
                    break
            return True
        else:
            return False

    def check_vim_connectivity(self):
        """Checks VIM can be reached and user credentials are ok.
        Returns None if success or raised vimconnConnectionException, vimconnAuthException, ...
        """
        k = None

        try:
            k = yield from self.store.actual.keys()
        except Exception as e:
            self.logger.error('Error {}'.format(e))
            raise vimconnConnectionException

        return None

    def new_tenant(self, tenant_name, tenant_description):
        """Adds a new tenant to VIM with this name and description, this is done using admin_url if provided
        "tenant_name": string max lenght 64
        "tenant_description": string max length 256
        returns the tenant identifier or raise exception
        """

        # TODO tenant are projects in openstack ->
        # A group of users; used to isolate access to Compute resources. An alternative term for a project.
        # Projects represent the base unit of “ownership” in OpenStack,
        # in that all resources in OpenStack should be owned by a specific project.
        # In OpenStack Identity, a project must be owned by a specific domain.
        #
        # in fog05 we can map tenant as the system-id?
        # or have a root like //afos/<sys-id>/<tenant-id>/<node-id>?
        # but a node can be part of different tenant
        raise vimconnNotImplemented("Should have implemented this")

    def delete_tenant(self, tenant_id, ):
        """Delete a tenant from VIM
        tenant_id: returned VIM tenant_id on "new_tenant"
        Returns None on success. Raises and exception of failure. If tenant is not found raises vimconnNotFoundException
        """
        raise vimconnNotImplemented("Should have implemented this")

    def get_tenant_list(self, filter_dict={}):
        """Obtain tenants of VIM
        filter_dict dictionary that can contain the following keys:
            name: filter by tenant name
            id: filter by tenant uuid/id
            <other VIM specific>
        Returns the tenant list of dictionaries, and empty list if no tenant match all the filers:
            [{'name':'<name>, 'id':'<id>, ...}, ...]
        """
        raise vimconnNotImplemented("Should have implemented this")

    def new_network(self, net_name, net_type, ip_profile=None, shared=False, vlan=None):
        """Adds a tenant network to VIM
        Params:
            'net_name': name of the network
            'net_type': one of:
                'bridge': overlay isolated network
                'data':   underlay E-LAN network for Passthrough and SRIOV interfaces
                'ptp':    underlay E-LINE network for Passthrough and SRIOV interfaces.
            'ip_profile': is a dict containing the IP parameters of the network (Currently only IPv4 is implemented)
                'ip-version': can be one of ["IPv4","IPv6"]
                'subnet-address': ip_prefix_schema, that is X.X.X.X/Y
                'gateway-address': (Optional) ip_schema, that is X.X.X.X
                'dns-address': (Optional) ip_schema,
                'dhcp': (Optional) dict containing
                    'enabled': {"type": "boolean"},
                    'start-address': ip_schema, first IP to grant
                    'count': number of IPs to grant.
            'shared': if this network can be seen/use by other tenants/organization
            'vlan': in case of a data or ptp net_type, the intended vlan tag to be used for the network
        Returns the network identifier on success or raises and exception on failure
        """

        # TODO on fog05 -> support dhcp as used on OSM
        self.logger.debug("Adding a new network to VIM name '{}', type '{}'".format(net_name, net_type))

        net_uuid = str(uuid.uuid4())
        manifest = {}
        manifest.update({'status': 'add'})
        manifest.update({'uuid': net_uuid})

        if net_type != 'bridge':
            raise vimconn.vimconnConflictException("Currently only bridge networking is supported!!")

        if ip_profile is not None:
            manifest.update({"ip_type": ip_profile.get('ip-version')})
            manifest.update({"ip_range": ip_profile.get('subnet-address')})
            manifest.update({"gateway": ip_profile.get('gateway-address')})
            manifest.update({"dns": ip_profile.get('dns-address')})
            dhcp_info = ip_profile.get('dhcp', None)
            if dhcp_info is not None:
                if dhcp_info.get('enable'):
                    manifest.update({"has_dhcp": True})
                    # TODO compute dhcp_range -> start-address|start-address+count

        # compute vxlan id and vxlan mcast address

        self.logger.debug("Network manifest created {}".format(manifest))
        nodes = yield from self.__get_nodes()
        self.logger.debug("fog05 Nodes: {}".format(nodes))
        if len(nodes) == 0:
            raise vimconn.vimconnUnexpectedResponse("No fog05 nodes found!!")

        for n in nodes:
            self.logger.debug("Adding network to: {}".format(n))
            res = yield from self.__send_add_network(n, manifest)
            if res:
                self.logger.debug("Added network to: {}".format(n))
            else:
                self.logger.debug("Error on adding network to: {}".format(n))

        return net_uuid

    def get_network_list(self, filter_dict={}):
        """Obtain tenant networks of VIM
        Params:
            'filter_dict' (optional) contains entries to return only networks that matches ALL entries:
                name: string  => returns only networks with this name
                id:   string  => returns networks with this VIM id, this imply returns one network at most
                shared: boolean >= returns only networks that are (or are not) shared
                tenant_id: sting => returns only networks that belong to this tenant/project
                ,#(not used yet) admin_state_up: boolean => returns only networks that are (or are not) in admin state active
                #(not used yet) status: 'ACTIVE','ERROR',... => filter networks that are on this status
        Returns the network list of dictionaries. each dictionary contains:
            'id': (mandatory) VIM network id
            'name': (mandatory) VIM network name
            'status': (mandatory) can be 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'network_type': (optional) can be 'vxlan', 'vlan' or 'flat'
            'segmentation_id': (optional) in case network_type is vlan or vxlan this field contains the segmentation id
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no network map the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """

        # TODO remove 'duplicated' networks, because the same network as to be defined in all nodes to provide connectivity
        nws = yield from self.__get_networks()
        nets = []
        for n in nws:
            network_info = {}
            network_info.update({'id': n.get('uuid')})
            network_info.update({'name': n.get('name')})
            network_info.update({'status': "ACTIVE"})
            network_info.update({'network_type': n.get('network_type')})
            network_info.update({'segmentation_id': n.get('vxlan_id')})
            nets.append(network_info)

        return nets

    def get_network(self, net_id):
        """Obtain network details from the 'net_id' VIM network
        Return a dict that contains:
            'id': (mandatory) VIM network id, that is, net_id
            'name': (mandatory) VIM network name
            'status': (mandatory) can be 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        Raises an exception upon error or when network is not found
        """

        n = yield from self.__get_network(net_id)
        network_info = {}
        network_info.update({'id': n.get('uuid')})
        network_info.update({'name': n.get('name')})
        network_info.update({'status': "ACTIVE"})
        network_info.update({'network_type': n.get('network_type')})
        network_info.update({'segmentation_id': n.get('vxlan_id')})
        return network_info

    def delete_network(self, net_id):
        """Deletes a tenant network from VIM
        Returns the network identifier or raises an exception upon error or when network is not found
        """

        nodes = yield from self.__get_nodes()
        if len(nodes) == 0:
            raise vimconn.vimconnUnexpectedResponse("No fog05 nodes found!!")
        for n in nodes:
            res = self.__send_remove_network(n, net_id)
            if res:
                self.logger.debug("Deletted network from: {}".format(n))
            else:
                self.logger.debug("Error on deletting network from: {}".format(n))

        return net_id

    def refresh_nets_status(self, net_list):
        """Get the status of the networks
        Params:
            'net_list': a list with the VIM network id to be get the status
        Returns a dictionary with:
            'net_id':         #VIM id of this network
                status:     #Mandatory. Text with one of:
                    #  DELETED (not found at vim)
                    #  VIM_ERROR (Cannot connect to VIM, authentication problems, VIM response error, ...)
                    #  OTHER (Vim reported other status not understood)
                    #  ERROR (VIM indicates an ERROR status)
                    #  ACTIVE, INACTIVE, DOWN (admin down),
                    #  BUILD (on building process)
                error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR
                vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)
            'net_id2': ...
        """
        infos = {}
        for net_id in net_list:
            net_info = yield from self.__get_network(net_id)
            d = {}
            if net_info is not None:
                d.update({'status': 'ACTIVE'})
                d.update({'vim_info': json.dumps(net_info)})
            else:
                d.update({'status': 'DELETED'})
            infos.update({net_id: d})

        return infos

    def get_flavor(self, flavor_id):
        """Obtain flavor details from the VIM
        Returns the flavor dict details {'id':<>, 'name':<>, other vim specific }
        Raises an exception upon error or if not found
        """

        self.logger.debug("Getting flavor '%s'", flavor_id)
        f = yield from self.__get_flavor(flavor_id)
        if f is None:
            raise vimconn.vimconnNotFoundException("Flavor {} not found".format(flavor_id))
        id = f.get('uuid')
        f.pop('uuid')
        f.update({'id': id})
        return f

    def get_flavor_id_from_data(self, flavor_dict):
        """Obtain flavor id that match the flavor description
        Params:
            'flavor_dict': dictionary that contains:
                'disk': main hard disk in GB
                'ram': meomry in MB
                'vcpus': number of virtual cpus
                #TODO: complete parameters for EPA
        Returns the flavor_id or raises a vimconnNotFoundException
        """

        f_id = None
        f_target = (flavor_dict.get("ram"), flavor_dict.get("vcpus"), flavor_dict.get("disk"))
        numas = flavor_dict.get("extended", {}).get("numas")
        if numas:
            # TODO
            raise vimconn.vimconnNotFoundException("Flavor with EPA still not implemted")
        flvs = yield from self.__get_flavors()
        for f in flvs:
            f_data = (f.get("memory"), f.get("cpu"), f.get("disk_size"))
            if f_data == f_target:
                return f.get('uuid')
        if f_id is None:
            raise vimconn.vimconnNotFoundException("Cannot find any flavor matching '{}'".format(flavor_dict))

    def new_flavor(self, flavor_data):
        """Adds a tenant flavor to VIM
            flavor_data contains a dictionary with information, keys:
                name: flavor name
                ram: memory (cloud type) in MBytes
                vpcus: cpus (cloud type)
                extended: EPA parameters
                  - numas: #items requested in same NUMA
                        memory: number of 1G huge pages memory
                        paired-threads|cores|threads: number of paired hyperthreads, complete cores OR individual threads
                        interfaces: # passthrough(PT) or SRIOV interfaces attached to this numa
                          - name: interface name
                            dedicated: yes|no|yes:sriov;  for PT, SRIOV or only one SRIOV for the physical NIC
                            bandwidth: X Gbps; requested guarantee bandwidth
                            vpci: requested virtual PCI address
                disk: disk size
                is_public:
                 #TODO to concrete
        Returns the flavor identifier"""
        numas = flavor_data.get("extended", {}).get("numas")
        if numas:
            raise vimconn.vimconnNotFoundException("Flavor with EPA still not implemted")

        f_manifest = {}
        uuid = str(uuid.uuid4())
        f_manifest.update({'uuid': uuid})
        f_manifest.update({'memory': flavor_data.get('ram')})
        f_manifest.update({'cpu': flavor_data.get('vcpus')})
        f_manifest.update({'disk_size': flavor_data.get('disk')})

        # if yield from self.__send_add_flavor(f)
        #    return uuid

        nodes = yield from self.__get_nodes()
        self.logger.debug("fog05 Nodes: {}".format(nodes))
        if len(nodes) == 0:
            raise vimconn.vimconnUnexpectedResponse("No fog05 nodes found!!")

        for n in nodes:
            res = yield from self.__send_add_flavor_node(n, f_manifest)
            if res:
                self.logger.debug("Added flavor to: {}".format(n))
            else:
                self.logger.debug("Error on adding flavor to: {}".format(n))

        return uuid
        # raise vimconnNotImplemented( "Should have implemented this" )

    def delete_flavor(self, flavor_id):
        """Deletes a tenant flavor from VIM identify by its id
        Returns the used id or raise an exception"""
        nodes = yield from self.__get_nodes()
        self.logger.debug("fog05 Nodes: {}".format(nodes))
        if len(nodes) == 0:
            raise vimconn.vimconnUnexpectedResponse("No fog05 nodes found!!")

        for n in nodes:
            res = self.__send_remove_flavor_node(n, flavor_id)
            if res:
                self.logger.debug("Removed flavor from: {}".format(n))
            else:
                self.logger.debug("Error on removing flavor from: {}".format(n))
        return uuid

    def new_image(self, image_dict):
        """ Adds a tenant image to VIM
        Returns the image id or raises an exception if failed
        image_dict
            name: name
            disk_format: qcow2, vhd, vmdk, raw (by default), ...
            location: path or URI
            public: "yes" or "no"
            metadata: metadata of the image
        """
        # TODO writing image information to //dfos/<sys-id>/<node-id>/runtime/<r id>/image/<image_id>
        self.logger.debug('Adding new image {}'.format(image_dict))
        if "disk_format" in image_dict:
            disk_format = image_dict.get("disk_format")
        else:  # autodiscover based on extension
            if image_dict.get('location')[-6:] == ".qcow2":
                disk_format = "qcow2"
            elif image_dict.get('location')[-4:] == ".vhd":
                disk_format = "vhd"
            elif image_dict.get('location')[-5:] == ".vmdk":
                disk_format = "vmdk"
            elif image_dict.get('location')[-4:] == ".vdi":
                disk_format = "vdi"
            elif image_dict.get('location')[-4:] == ".iso":
                disk_format = "iso"
            elif image_dict.get('location')[-4:] == ".aki":
                disk_format = "aki"
            elif image_dict.get('location')[-4:] == ".ari":
                disk_format = "ari"
            elif image_dict.get('location')[-4:] == ".ami":
                disk_format = "ami"
            else:
                disk_format = "raw"

        self.logger.debug("new_image: '{}' loading from '{}'".format(image_dict.get('name'), image_dict.get('location')))

        image_manifest = {}
        uuid = '{}'.format(uuid.uuid4())
        # {uuid, name, base_image, format}
        image_manifest.update({'uuid': uuid})
        image_manifest.update({'name': image_dict.get('name')})
        image_manifest.update({'format': disk_format})
        if image_dict.get('location')[0:4] == "http":
            # in this case it is easy just put location as base_image
            image_manifest.update({'base_image': image_dict.get('location')})
        else:
            # the image is a local file
            # should be able to upload the image some where and the use the url to put the image in the node
            # the webservice provide a ftp server to upload?
            raise vimconnNotSupportedException("Image from local file not yet supported '{}'".format(image_dict))

        res = self.__send_add_image(image_manifest)
        if res:
            return uuid
        else:
            raise vimconnUnexpectedResponse("Error on adding new image '{}'".format(image_dict))

    def delete_image(self, image_id):
        """Deletes a tenant image from VIM
        Returns the image_id if image is deleted or raises an exception on error"""

        res = self.__send_remove_image(image_id)
        if res:
            return image_id
        else:
            raise vimconnUnexpectedResponse("Error on removing image '{}'".format(image_dict))

    def get_image_id_from_path(self, path):
        """Get the image id from image path in the VIM database.
           Returns the image_id or raises a vimconnNotFoundException
        """
        imgs = self.__get_images()
        for i in imgs:
            if i.get('base_image') == path:
                return i.get('uuid')

    def get_image_list(self, filter_dict={}):
        """Obtain tenant images from VIM
        Filter_dict can be:
            name: image name
            id: image uuid
            checksum: image checksum
            location: image path
        Returns the image list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        """

        f_name = filter_dict.get('name')
        f_id = filter_dict.get('id')
        f_location = filter_dict.get('location')

        self.logger.debug("Getting image list from VIM filter: '{}'".format(filter_dict))
        img_list = []
        imgs = self.__get_images()
        for i in imgs:
            i_osm = {}
            if f_name is not None and f_id is None and f_location is None:
                if i.get('name') == f_name:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
            elif f_name is None and f_id is not None and f_location is None:
                if i.get('uuid') == f_id:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
            elif f_name is None and f_id is None and f_location is not None:
                if i.get('base_image') == f_location:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
            elif f_name is not None and f_id is not None and f_location is not None:
                if i.get('name') == f_name and i.get('uuid') == f_id:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
            elif f_name is not None and f_id is None and f_location is not not None:
                if i.get('name') == f_name and i.get('base_image') == f_location:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
            elif f_name is None and f_id is not None and f_location is not not None:
                if i.get('base_image') == f_location and i.get('uuid') == f_id:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
            elif f_name is not None and f_id is not None and f_location is not not None:
                if i.get('base_image') == f_location and i.get('name') == f_name and i.get('uuid') == f_id:
                    i_osm.update({'id': i.get('uuid')})
                    i_osm.update({'name': i.get('name')})
                    i_osm.update({'location': i.get('base_image')})
                    i_osm.update({'path': i.get('path')})
                    i_osm.update({'format': i.get('format')})
                    img_list.append(i_osm)
        return img_list

    def new_vminstance(self, name, description, start, image_id, flavor_id, net_list, cloud_config=None, disk_list=None,
                       availability_zone_index=None, availability_zone_list=None):
        """Adds a VM instance to VIM
        Params:
            'start': (boolean) indicates if VM must start or created in pause mode.
            'image_id','flavor_id': image and flavor VIM id to use for the VM
            'net_list': list of interfaces, each one is a dictionary with:
                'name': (optional) name for the interface.
                'net_id': VIM network id where this interface must be connect to. Mandatory for type==virtual
                'vpci': (optional) virtual vPCI address to assign at the VM. Can be ignored depending on VIM capabilities
                'model': (optional and only have sense for type==virtual) interface model: virtio, e2000, ...
                'mac_address': (optional) mac address to assign to this interface
                #TODO: CHECK if an optional 'vlan' parameter is needed for VIMs when type if VF and net_id is not provided,
                    the VLAN tag to be used. In case net_id is provided, the internal network vlan is used for tagging VF
                'type': (mandatory) can be one of:
                    'virtual', in this case always connected to a network of type 'net_type=bridge'
                     'PCI-PASSTHROUGH' or 'PF' (passthrough): depending on VIM capabilities it can be connected to a data/ptp network ot it
                           can created unconnected
                     'SR-IOV' or 'VF' (SRIOV with VLAN tag): same as PF for network connectivity.
                     'VFnotShared'(SRIOV without VLAN tag) same as PF for network connectivity. VF where no other VFs
                            are allocated on the same physical NIC
                'bw': (optional) only for PF/VF/VFnotShared. Minimal Bandwidth required for the interface in GBPS
                'port_security': (optional) If False it must avoid any traffic filtering at this interface. If missing
                                or True, it must apply the default VIM behaviour
                After execution the method will add the key:
                'vim_id': must be filled/added by this method with the VIM identifier generated by the VIM for this
                        interface. 'net_list' is modified
            'cloud_config': (optional) dictionary with:
                'key-pairs': (optional) list of strings with the public key to be inserted to the default user
                'users': (optional) list of users to be inserted, each item is a dict with:
                    'name': (mandatory) user name,
                    'key-pairs': (optional) list of strings with the public key to be inserted to the user
                'user-data': (optional) can be a string with the text script to be passed directly to cloud-init,
                    or a list of strings, each one contains a script to be passed, usually with a MIMEmultipart file
                'config-files': (optional). List of files to be transferred. Each item is a dict with:
                    'dest': (mandatory) string with the destination absolute path
                    'encoding': (optional, by default text). Can be one of:
                        'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                    'content' (mandatory): string with the content of the file
                    'permissions': (optional) string with file permissions, typically octal notation '0644'
                    'owner': (optional) file owner, string with the format 'owner:group'
                'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk)
            'disk_list': (optional) list with additional disks to the VM. Each item is a dict with:
                'image_id': (optional). VIM id of an existing image. If not provided an empty disk must be mounted
                'size': (mandatory) string with the size of the disk in GB
            availability_zone_index: Index of availability_zone_list to use for this this VM. None if not AV required
            availability_zone_list: list of availability zones given by user in the VNFD descriptor.  Ignore if
                availability_zone_index is None
        Returns a tuple with the instance identifier and created_items or raises an exception on error
            created_items can be None or a dictionary where this method can include key-values that will be passed to
            the method delete_vminstance and action_vminstance. Can be used to store created ports, volumes, etc.
            Format is vimconnector dependent, but do not use nested dictionaries and a value of None should be the same
            as not present.
        """
        self.logger.debug("Creating an entity (vm) on fog05: '{}'".format(name))

        vm_ae_uuid = '{}'.format(uuid.uuid4())
        vm_i_uuid = '{}'.format(uuid.uuid4())

        vm_manifest = {}
        vm_manifest.update({'uuid': vm_ae_uuid})
        vm_manifest.update({'name': name})
        vm_manifest.update({'flavor_id': flavor_id})
        vm_manifest.update({'base_image': image_id})
        networks = []
        for n in net_list:
            if n.get('type') == 'virtual':
                net = {}
                name = n.get('name', None)
                if name is not None:
                    net.update({'name': name})
                net.update({'network_uuid': n.get('net_id')})
                mac = n.get('mac_address', None)
                if mac is not None:
                    net.update({'mac_address': mac})
            else:
                self.logger.error("This VM has a network that is not supported at the moment: '{}'".format(n.get('name')))
                raise vimconnNotImplemented("Only virtual networks are allowed at this moment")
        if cloud_config is not None:
            user_data = cloud_config.get('user-data')
            if user_data is not None:
                vm_manifest.update({'user-data': user_data})
            keys = cloud_config.get('key-pairs')
            if keys is not None:
                vm_manifest.update({'ssh-key': keys[0]})  # TODO should add all keys

        manifest = {}
        manifest.update({'uuid': vm_ae_uuid})
        manifest.update({'name': '{}_ae'.format(name)})
        manifest.update({'type': 'kvm'})
        manifest.update({'version': 1})

        if availability_zone_index is not None:
            node_uuid = availability_zone_index
        else:
            node_uuid = self.__get_node(self.__get_eligible_nodes(self.__get_nodes(), manifest))

        res = self.__send_define_entity(node_uuid, manifest)
        if res:
            res = self.__send_configure_entity(node_uuid, vm_ae_uuid, vm_i_uuid)
            if res:
                if start:
                    res = self.__send_run_entity(node_uuid, vm_ae_uuid, vm_i_uuid)
                    if res:
                        created_items = {'entity_uuid': vm_ae_uuid}
                        return (vm_i_uuid, created_items)
                else:
                    created_items = {'entity_uuid': vm_ae_uuid, 'node_uuid': node_uuid}
                    return (vm_i_uuid, created_items)

    def get_vminstance(self, vm_id):
        """Returns the VM instance information from VIM"""

        data = self.__get_instance(vm_id)
        return data

    def delete_vminstance(self, vm_id, created_items=None):
        """
        Removes a VM instance from VIM and each associate elements
        :param vm_id: VIM identifier of the VM, provided by method new_vminstance
        :param created_items: dictionary with extra items to be deleted. provided by method new_vminstance and/or method
            action_vminstance
        :return: None or the same vm_id. Raises an exception on fail
        """

        self.__send_stop_entity(created_items.get('node_uuid'), created_items.get('entity_uuid'), vm_id)
        self.__send_clean_entity(created_items.get('node_uuid'), created_items.get('entity_uuid'), vm_id)
        self.__send_undefine_entity(created_items.get('node_uuid'), created_items.get('entity_uuid'))
        return vm_id

    def refresh_vms_status(self, vm_list):
        """Get the status of the virtual machines and their interfaces/ports
           Params: the list of VM identifiers
           Returns a dictionary with:
                vm_id:          #VIM id of this Virtual Machine
                    status:     #Mandatory. Text with one of:
                                #  DELETED (not found at vim)
                                #  VIM_ERROR (Cannot connect to VIM, VIM response error, ...)
                                #  OTHER (Vim reported other status not understood)
                                #  ERROR (VIM indicates an ERROR status)
                                #  ACTIVE, PAUSED, SUSPENDED, INACTIVE (not running),
                                #  BUILD (on building process), ERROR
                                #  ACTIVE:NoMgmtIP (Active but any of its interface has an IP address
                                #
                    error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR
                    vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)
                    interfaces: list with interface info. Each item a dictionary with:
                        vim_info:         #Text with plain information obtained from vim (yaml.safe_dump)
                        mac_address:      #Text format XX:XX:XX:XX:XX:XX
                        vim_net_id:       #network id where this interface is connected, if provided at creation
                        vim_interface_id: #interface/port VIM id
                        ip_address:       #null, or text with IPv4, IPv6 address
                        compute_node:     #identification of compute node where PF,VF interface is allocated
                        pci:              #PCI address of the NIC that hosts the PF,VF
                        vlan:             #physical VLAN used for VF
        """
        infos = {}
        for vm in vm_list:
            info = {}
            data = self.get_vminstance(vm)
            if data is None:
                info.update({'status': 'DELETED'})
            else:
                info.update({'status': atomicEntityStatus2manoFormat.get(data.get('status').upper(), 'OTHER')})
                info.update({'vim_info': json.dumps(data)})
                vm_data = data.get('entity_data')
                intfs = []
                for n in vm_data.get('networks'):
                    i = {}
                    i.update({'vim_info': json.dumps(n)})
                    i.update({'mac_address': n.get('mac_address')})
                    i.update({'vim_net_id': n.get('network_uuid')})
                    i.update({'vim_interface_id': n.get('inft_name')})
                info.update({'interfaces': intfs})
            infos.update({vm: info})

    def action_vminstance(self, vm_id, action_dict, created_items={}):
        """
        Send and action over a VM instance. Returns created_items if the action was successfully sent to the VIM.
        created_items is a dictionary with items that
        :param vm_id: VIM identifier of the VM, provided by method new_vminstance
        :param action_dict: dictionary with the action to perform
        :param created_items: provided by method new_vminstance is a dictionary with key-values that will be passed to
            the method delete_vminstance. Can be used to store created ports, volumes, etc. Format is vimconnector
            dependent, but do not use nested dictionaries and a value of None should be the same as not present. This
            method can modify this value
        :return: None, or a console dict
        """
        raise vimconnNotImplemented("Should have implemented this")

    def get_vminstance_console(self, vm_id, console_type="vnc"):
        """
        Get a console for the virtual machine
        Params:
            vm_id: uuid of the VM
            console_type, can be:
                "novnc" (by default), "xvpvnc" for VNC types,
                "rdp-html5" for RDP types, "spice-html5" for SPICE types
        Returns dict with the console parameters:
                protocol: ssh, ftp, http, https, ...
                server:   usually ip address
                port:     the http, ssh, ... port
                suffix:   extra text, e.g. the http path and query string
        """
        raise vimconnNotImplemented("Should have implemented this")

    def new_classification(self, name, ctype, definition):
        """Creates a traffic classification in the VIM
        Params:
            'name': name of this classification
            'ctype': type of this classification
            'definition': definition of this classification (type-dependent free-form text)
        Returns the VIM's classification ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_classification(self, classification_id):
        """Obtain classification details of the VIM's classification with ID='classification_id'
        Return a dict that contains:
            'id': VIM's classification ID (same as classification_id)
            'name': VIM's classification name
            'type': type of this classification
            'definition': definition of the classification
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when classification is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_classification_list(self, filter_dict={}):
        """Obtain classifications from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the classifications on and only return those that match ALL:
                id:   string => returns classifications with this VIM's classification ID, which implies a return of one classification at most
                name: string => returns only classifications with this name
                type: string => returns classifications of this type
                definition: string => returns classifications that have this definition
                tenant_id: string => returns only classifications that belong to this tenant/project
        Returns a list of classification dictionaries, each dictionary contains:
            'id': (mandatory) VIM's classification ID
            'name': (mandatory) VIM's classification name
            'type': type of this classification
            'definition': definition of the classification
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no classification matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_classification(self, classification_id):
        """Deletes a classification from the VIM
        Returns the classification ID (classification_id) or raises an exception upon error or when classification is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def new_sfi(self, name, ingress_ports, egress_ports, sfc_encap=True):
        """Creates a service function instance in the VIM
        Params:
            'name': name of this service function instance
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            'sfc_encap': boolean stating whether this specific instance supports IETF SFC Encapsulation
        Returns the VIM's service function instance ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfi(self, sfi_id):
        """Obtain service function instance details of the VIM's service function instance with ID='sfi_id'
        Return a dict that contains:
            'id': VIM's sfi ID (same as sfi_id)
            'name': VIM's sfi name
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when service function instance is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfi_list(self, filter_dict={}):
        """Obtain service function instances from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfis on and only return those that match ALL:
                id:   string  => returns sfis with this VIM's sfi ID, which implies a return of one sfi at most
                name: string  => returns only service function instances with this name
                tenant_id: string => returns only service function instances that belong to this tenant/project
        Returns a list of service function instance dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sfi ID
            'name': (mandatory) VIM's sfi name
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sfi matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_sfi(self, sfi_id):
        """Deletes a service function instance from the VIM
        Returns the service function instance ID (sfi_id) or raises an exception upon error or when sfi is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def new_sf(self, name, sfis, sfc_encap=True):
        """Creates (an abstract) service function in the VIM
        Params:
            'name': name of this service function
            'sfis': set of service function instances of this (abstract) service function
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
        Returns the VIM's service function ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sf(self, sf_id):
        """Obtain service function details of the VIM's service function with ID='sf_id'
        Return a dict that contains:
            'id': VIM's sf ID (same as sf_id)
            'name': VIM's sf name
            'sfis': VIM's sf's set of VIM's service function instance IDs
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when sf is not found
        """

    def get_sf_list(self, filter_dict={}):
        """Obtain service functions from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfs on and only return those that match ALL:
                id:   string  => returns sfs with this VIM's sf ID, which implies a return of one sf at most
                name: string  => returns only service functions with this name
                tenant_id: string => returns only service functions that belong to this tenant/project
        Returns a list of service function dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sf ID
            'name': (mandatory) VIM's sf name
            'sfis': VIM's sf's set of VIM's service function instance IDs
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sf matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_sf(self, sf_id):
        """Deletes (an abstract) service function from the VIM
        Returns the service function ID (sf_id) or raises an exception upon error or when sf is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def new_sfp(self, name, classifications, sfs, sfc_encap=True, spi=None):
        """Creates a service function path
        Params:
            'name': name of this service function path
            'classifications': set of traffic classifications that should be matched on to get into this sfp
            'sfs': list of every service function that constitutes this path , from first to last
            'sfc_encap': whether this is an SFC-Encapsulated chain (i.e using NSH), True by default
            'spi': (optional) the Service Function Path identifier (SPI: Service Path Identifier) for this path
        Returns the VIM's sfp ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfp(self, sfp_id):
        """Obtain service function path details of the VIM's sfp with ID='sfp_id'
        Return a dict that contains:
            'id': VIM's sfp ID (same as sfp_id)
            'name': VIM's sfp name
            'classifications': VIM's sfp's list of VIM's classification IDs
            'sfs': VIM's sfp's list of VIM's service function IDs
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when sfp is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def get_sfp_list(self, filter_dict={}):
        """Obtain service function paths from VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfps on, and only return those that match ALL:
                id:   string  => returns sfps with this VIM's sfp ID , which implies a return of one sfp at most
                name: string  => returns only sfps with this name
                tenant_id: string => returns only sfps that belong to this tenant/project
        Returns a list of service function path dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sfp ID
            'name': (mandatory) VIM's sfp name
            'classifications': VIM's sfp's list of VIM's classification IDs
            'sfs': VIM's sfp's list of VIM's service function IDs
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sfp matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def delete_sfp(self, sfp_id):
        """Deletes a service function path from the VIM
        Returns the sfp ID (sfp_id) or raises an exception upon error or when sf is not found
        """
        raise vimconnNotImplemented("SFC support not implemented")

    def inject_user_key(self, ip_addr=None, user=None, key=None, ro_key=None, password=None):
        """
        Inject a ssh public key in a VM
        Params:
            ip_addr: ip address of the VM
            user: username (default-user) to enter in the VM
            key: public key to be injected in the VM
            ro_key: private key of the RO, used to enter in the VM if the password is not provided
            password: password of the user to enter in the VM
        The function doesn't return a value:
        """
        if not ip_addr or not user:
            raise vimconnNotSupportedException("All parameters should be different from 'None'")
        elif not ro_key and not password:
            raise vimconnNotSupportedException("All parameters should be different from 'None'")
        else:
            commands = {'mkdir -p ~/.ssh/', 'echo "%s" >> ~/.ssh/authorized_keys' % key,
                        'chmod 644 ~/.ssh/authorized_keys', 'chmod 700 ~/.ssh/'}
            client = paramiko.SSHClient()
            try:
                if ro_key:
                    pkey = paramiko.RSAKey.from_private_key(StringIO.StringIO(ro_key))
                else:
                    pkey = None
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip_addr, username=user, password=password, pkey=pkey, timeout=10)
                for command in commands:
                    (i, o, e) = client.exec_command(command, timeout=10)
                    returncode = o.channel.recv_exit_status()
                    output = o.read()
                    outerror = e.read()
                    if returncode != 0:
                        text = "run_command='{}' Error='{}'".format(command, outerror)
                        raise vimconnUnexpectedResponse("Cannot inject ssh key in VM: '{}'".format(text))
                        return
            except (socket.error, paramiko.AuthenticationException, paramiko.SSHException) as message:
                raise vimconnUnexpectedResponse(
                    "Cannot inject ssh key in VM: '{}' - {}".format(ip_addr, str(message)))
                return

    # NOT USED METHODS in current version

    def host_vim2gui(self, host, server_dict):
        """Transform host dictionary from VIM format to GUI format,
        and append to the server_dict
        """
        raise vimconnNotImplemented("Should have implemented this")

    def get_hosts_info(self):
        """Get the information of deployed hosts
        Returns the hosts content"""
        raise vimconnNotImplemented("Should have implemented this")

    def get_hosts(self, vim_tenant):
        """Get the hosts and deployed instances
        Returns the hosts content"""
        raise vimconnNotImplemented("Should have implemented this")

    def get_processor_rankings(self):
        """Get the processor rankings in the VIM database"""
        raise vimconnNotImplemented("Should have implemented this")

    def new_host(self, host_data):
        """Adds a new host to VIM"""
        """Returns status code of the VIM response"""
        raise vimconnNotImplemented("Should have implemented this")

    def new_external_port(self, port_data):
        """Adds a external port to VIM"""
        """Returns the port identifier"""
        raise vimconnNotImplemented("Should have implemented this")

    def new_external_network(self, net_name, net_type):
        """Adds a external network to VIM (shared)"""
        """Returns the network identifier"""
        raise vimconnNotImplemented("Should have implemented this")

    def connect_port_network(self, port_id, network_id, admin=False):
        """Connects a external port to a network"""
        """Returns status code of the VIM response"""
        raise vimconnNotImplemented("Should have implemented this")

    def new_vminstancefromJSON(self, vm_data):
        """Adds a VM instance to VIM"""
        """Returns the instance identifier"""
        raise vimconnNotImplemented("Should have implemented this")

