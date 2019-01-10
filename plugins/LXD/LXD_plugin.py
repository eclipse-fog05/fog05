# Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set


import sys
import os
import uuid
from packaging import version
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from LXDEntity import LXDEntity
from LXDEntityInstance import LXDEntityInstance
from jinja2 import Environment
import json
import random
import time
import re
from pylxd import Client
from pylxd.exceptions import LXDAPIException
import threading

from mvar import MVar


# TODO Plugins should not be aware of the Agent - The Agent is in OCaml no way to access his store, his logger and the OS plugin


class LXD(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(LXD, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from LXD Plugin')
        self.BASE_DIR = '/opt/fos/lxd'
        self.DISK_DIR = 'disks'
        self.IMAGE_DIR = 'images'
        self.LOG_DIR = 'logs'
        self.HOME = 'runtime/{}/entity'.format(self.uuid)
        self.HOME_ENTITY = 'runtime/{}/entity'.format(self.uuid)
        self.HOME_IMAGE = 'runtime/{}/image'.format(self.uuid)
        self.HOME_FLAVOR = 'runtime/{}/flavor'.format(self.uuid)
        self.ERRORS = 'runtime/{}/errors'.format(self.uuid)
        self.INSTANCE = 'instance'
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.conn = None
        self.images = {}
        self.flavors = {}
        self.mon_th = {}
        self.start_runtime()

    def start_runtime(self):
        self.agent.logger.info(
            'startRuntime()', ' LXD Plugin - Connecting to LXD')
        self.conn = Client()
        self.agent.logger.info(
            'startRuntime()', '[ DONE ] LXD Plugin - Connecting to LXD')
        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME)
        self.agent.logger.info(
            'startRuntime()', ' LXD Plugin - Observing {} for entity'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_entity)

        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_FLAVOR)
        self.agent.logger.info(
            'startRuntime()', ' LXD Plugin - Observing {} for flavor'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_flavor)

        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_IMAGE)
        self.agent.logger.info(
            'startRuntime()', ' LXD Plugin - Observing {} for image'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_image)

        '''check if dirs exists if not exists create'''
        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists('{}/{}'.format(self.BASE_DIR, self.DISK_DIR)):
                self.agent.get_os_plugin().create_dir(
                    '{}/{}'.format(self.BASE_DIR, self.DISK_DIR))
            if not self.agent.get_os_plugin().dir_exists('{}/{}'.format(self.BASE_DIR, self.IMAGE_DIR)):
                self.agent.get_os_plugin().create_dir(
                    '{}/{}'.format(self.BASE_DIR, self.IMAGE_DIR))
            if not self.agent.get_os_plugin().dir_exists('{}/{}'.format(self.BASE_DIR, self.LOG_DIR)):
                self.agent.get_os_plugin().create_dir(
                    '{}/{}'.format(self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.get_os_plugin().create_dir('{}'.format(self.BASE_DIR))
            self.agent.get_os_plugin().create_dir(
                '{}/{}'.format(self.BASE_DIR, self.DISK_DIR))
            self.agent.get_os_plugin().create_dir(
                '{}/{}'.format(self.BASE_DIR, self.IMAGE_DIR))
            self.agent.get_os_plugin().create_dir(
                '{}/{}'.format(self.BASE_DIR, self.LOG_DIR))

        return self.uuid

    def stop_runtime(self):
        self.agent.logger.info(
            'stopRuntime()', 'LXD Plugin - Destroying {} running domains'.format(len(self.current_entities)))
        keys = list(self.current_entities.keys())
        for k in keys:
            self.agent.logger.info('stopRuntime()', 'Stopping {}'.format(k))
            entity = self.current_entities.get(k)
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(k, i)
            # if entity.get_state() == State.PAUSED:
            #     self.resume_entity(k)
            #     self.stop_entity(k)
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            # elif entity.get_state() == State.RUNNING:
            #     self.stop_entity(k)
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            # elif entity.get_state() == State.CONFIGURED:
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            if entity.get_state() == State.DEFINED:
                self.undefine_entity(k)
        keys = list(self.images.keys())
        for k in keys:
            self.agent.logger.info(
                'stopRuntime()', 'Removing Image {}'.format(k))
            try:
                img = self.conn.images.get_by_alias(k)
                img.delete()
            except LXDAPIException as e:
                self.agent.logger.error('stopRuntime()', 'Error {}'.format(e))
                pass

        self.conn = None
        self.agent.logger.info(
            'stopRuntime()', '[ DONE ] LXD Plugin - Bye Bye')

    def get_entities(self):
        return self.current_entities

    def define_entity(self, *args, **kwargs):
        '''
        Try defining vm
        generating xml from templates/vm.xml with jinja2
        '''
        self.agent.logger.info(
            'defineEntity()', ' LXD Plugin - Defining a Container')
        if len(args) > 0:
            entity_uuid = args[4]
            '''
                The plugin should never enter here!!!
            '''
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            entity = LXDEntity(entity_uuid, kwargs.get('name'), kwargs.get('networks'), kwargs.get('base_image'),
                               kwargs.get(
                                   'user-data'), kwargs.get('ssh-key'), kwargs.get('storage'),
                               kwargs.get('profiles'))
        else:
            return None

        if self.is_uuid(entity.image_url):
            img_info = self.images.get(entity.image_url, None)
            if img_info is None:
                self.agent.logger.error(
                    'define_entity()', '[ ERRO ] LXD Plugin - Cannot find image {}'.format(entity.image_url))
                self.__write_error_entity(entity_uuid, 'Image not found!')

        else:
            if entity.image_url.startswith('http'):
                image_name = os.path.join(
                    self.BASE_DIR, self.IMAGE_DIR, entity.image_url.split('/')[-1])
                self.agent.get_os_plugin().download_file(entity.image_url, image_name)
            elif entity.image_url.startswith('file://'):
                image_name = os.path.join(
                    self.BASE_DIR, self.IMAGE_DIR, entity.image_url.split('/')[-1])
                cmd = 'cp {} {}'.format(
                    entity.image_url[len('file://'):], image_name)
                self.agent.get_os_plugin().execute_command(cmd, True)
            self.agent.logger.info('defineEntity()', '[ INFO ] LXD Plugin - Loading image data from: {}'.format(
                os.path.join(self.BASE_DIR, self.IMAGE_DIR, image_name)))
            image_data = self.agent.get_os_plugin().read_binary_file(
                os.path.join(self.BASE_DIR, self.IMAGE_DIR, image_name))
            self.agent.logger.info('defineEntity()', '[ DONE ] LXD Plugin - Loading image data from: {}'.format(
                os.path.join(self.BASE_DIR, self.IMAGE_DIR, image_name)))
            img_info = {}
            try:
                self.agent.logger.info(
                    'defineEntity()', '[ INFO ] LXD Plugin - Creating image with alias {}'.format(entity_uuid))
                try:
                    img = self.conn.images.create(
                        image_data, public=True, wait=True)
                    img.add_alias(entity_uuid, description=entity.name)
                except LXDAPIException as e:
                    if '{}'.format(e) == 'Image with same fingerprint already exists':
                        self.agent.logger.info(
                    'defineEntity()', '[ INFO ] LXD Plugin - Image with same fingerprint already exists')
                        pass

                self.agent.logger.info(
                    'defineEntity()', '[ DONE ] LXD Plugin - Created image with alias {}'.format(entity_uuid))
                img_info = {}
                img_info.update({'uuid': entity_uuid})
                img_info.update({'name': '{}_img'.format(entity.name)})
                img_info.update({'base_image': image_name})
                img_info.update({'type': 'lxd'})
                img_info.update({'format': '.'.join(image_name.split('.')[-2:])})
                entity.image = img_info
                self.images.update({entity_uuid: img_info})
                uri = '{}/{}'.format(self.HOME_IMAGE, entity_uuid)
                self.__update_actual_store(uri, img_info)

            except LXDAPIException as e:
                self.agent.logger.error('define_entity()', 'Error {}'.format(e))
                self.current_entities.update({entity_uuid: entity})
                uri = '{}/{}/{}'.format(self.agent.dhome,self.HOME, entity_uuid)
                lxd_info = json.loads(self.agent.dstore.get(uri))
                lxd_info.update({'status': 'error'})
                lxd_info.update({'error': '{}'.format(e)})
                self.__update_actual_store(entity_uuid, lxd_info)
                self.agent.logger.info('defineEntity()', '[ ERRO ] LXD Plugin - Container uuid: {}'.format(entity_uuid))
                return entity_uuid

        entity.image = img_info
        entity.set_state(State.DEFINED)
        if kwargs.get('devices'):
            entity.devices = json.loads(kwargs.get('devices'))
        self.current_entities.update({entity_uuid: entity})

        uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME, entity_uuid)
        lxd_info = json.loads(self.agent.dstore.get(uri))
        e_data = lxd_info.get('entity_data')
        e_data.update({'base_image': img_info.get('uuid')})
        lxd_info.update({'status': 'defined'})
        lxd_info.update({'entity_data': e_data})
        self.__update_actual_store(entity_uuid, lxd_info)
        self.agent.logger.info('defineEntity()', '[ DONE ] LXD Plugin - Container uuid: {}'.format(entity_uuid))
        return entity_uuid

    def undefine_entity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' LXD Plugin - Undefine a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)

            # try:
            #
            #     img = self.conn.images.get_by_alias(entity_uuid)
            #     img.delete()
            # except LXDAPIException as e:
            #     self.agent.logger.error('undefine_entity()', 'Error {}'.format(e))
            #     pass

            self.current_entities.pop(entity_uuid, None)
            # self.agent.get_os_plugin().remove_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image.get('base_image')))
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] LXD Plugin - Undefine a Container uuid {}'.format(entity_uuid))
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' LXD Plugin - Configure a Container uuid {} '.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:

            ''' 
                See if is possible to:
                - Put rootfs and images inside a custom path
            '''

            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print('This instance already existis!!')
            else:
                id = len(entity.instances)
                name = '{0}{1}'.format(entity.name, id)

                instance = LXDEntityInstance(instance_uuid, name, entity.networks, entity.image,
                                             entity.user_file, entity.ssh_key, entity.storage, entity.profiles,
                                             entity_uuid)

                instance.devices = entity.devices

                self.agent.logger.info('configureEntity()', '[ INFO ] LXD Plugin - Creating profile...')
                try:
                    # img = self.conn.images.create(image_data, public=True, wait=True)
                    # img.add_alias(entity_uuid, description=entity.name)

                    '''
                    Should explore how to setup correctly the networking, seems that you can't decide the interface you 
                    want to attach to the container
                    Below there is a try using a profile customized for network
                    '''

                    custom_profile_for_instance = self.conn.profiles.create(instance_uuid)

                    # WAN=$(awk '$2 == 00000000 { print $1 }' /proc/net/route)
                    # eno1
                    if instance.user_file is not None and instance.user_file != '':
                        user_data = self.__generate_custom_profile_userdata_configuration(instance.user_file)
                        custom_profile_for_instance.config = user_data

                    conf = {'environment.FOSUUID': instance_uuid,
                            'environment.FOSENTITYUUID': entity_uuid,
                            'environment.FOSNODEUUID': self.agent.get_os_plugin().get_uuid()
                            }
                    dev = self.__generate_custom_profile_devices_configuration(instance)
                    if instance.devices:
                        for d in instance.devices:
                            dev.update(d)
                    self.agent.logger.info('__generate_custom_profile_devices_configuration()', 'LXD Plugin - Devices {}'.format(dev))
                    custom_profile_for_instance.config = conf
                    custom_profile_for_instance.devices = dev
                    custom_profile_for_instance.save()

                except LXDAPIException as e:
                    self.agent.logger.error('configureEntity()', 'Error {}'.format(e))
                    pass
                self.agent.logger.info('configureEntity()', '[ DONE ] LXD Plugin - Creating profile...')
                if instance.profiles is None:
                    instance.profiles = list()

                instance.profiles.append(instance_uuid)

                self.agent.logger.info('configureEntity()', '[ INFO ] LXD Plugin - Generating container configuration...')
                config = self.__generate_container_dict(instance)
                self.agent.logger.info('configureEntity()', '[ DONE ] LXD Plugin - Generating container configuration...')

                self.agent.logger.info('configureEntity()', '[ INFO ] LXD Plugin - Creating Container...')
                self.conn.containers.create(config, wait=True)
                self.agent.logger.info('configureEntity()', '[ DONE ] LXD Plugin - Creating Container...')

                instance.on_configured(config)
                entity.add_instance(instance)

                self.current_entities.update({entity_uuid: entity})

                uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid)
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'configured'})
                container_info.update({'name': name})
                e_data = container_info.get('entity_data')
                e_data.update({'name': name})
                container_info.update({'entity_data': e_data})

                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.agent.logger.info('configureEntity()', '[ DONE ] LXD Plugin - Configure a Container uuid {}'.format(instance_uuid))
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('clean_entity()', ' LXD Plugin - Clean a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('clean_entity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('clean_entity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()', 'LXD Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                            'LXD Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state',
                                                             'Instance {} is not in CONFIGURED state'.format(instance_uuid))
                else:

                    try:
                        self.agent.logger.info('clean_entity()', '{}'.format(instance))
                        c = self.conn.containers.get(instance.name)
                        c.delete()

                        time.sleep(2)
                        profile = self.conn.profiles.get(instance_uuid)
                        profile.sync()
                        while True:
                            if len(profile.used_by) == 0:
                                break
                            profile.sync()
                            time.sleep(1)
                        profile.delete()

                    except Exception as e:
                        self.agent.logger.info('clean_entity()', '[ ERRO ] LXD Plugin - Clean a Container Exception raised {}'.format(e))

                        '''
                        {'wan': {'nictype': 'physical', 'name': 'wan', 'type': 'nic', 'parent': 'veth-af90f'}, 
                        'root': {'type': 'disk', 'pool': 'default', 'path': '/'}, 
                        'mgmt': {'nictype': 'bridged', 'name': 'mgmt', 'type': 'nic', 'parent': 'br-45873fb0'}}

                        '''

                    instance.on_clean()
                    entity.remove_instance(instance)
                    self.current_entities.update({entity_uuid: entity})

                    # uri = '{}/{}/{}' % (self.agent.dhome, self.HOME, entity_uuid))
                    # container_info = json.loads(self.agent.dstore.get(uri))
                    # container_info.update({'status': 'cleaned'})
                    # self.__update_actual_store(entity_uuid, container_info)
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('clean_entity()', '[ DONE ] LXD Plugin - Clean a Container uuid {} '.format(instance_uuid))

            return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('run_entity()', ' LXD Plugin - Starting a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('run_entity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('run_entity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() == State.RUNNING:
                self.agent.logger.error('run_entity()',
                                        'LXD Plugin - Instance already running')
                return True
            if instance.get_state() != State.CONFIGURED:
                self.agent.logger.error('clean_entity()',
                                        'LXD Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state',
                                                         'Instance {} is not in CONFIGURED state'.format(instance_uuid))
            else:
                uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'starting'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.current_entities.update({entity_uuid: entity})

                c = self.conn.containers.get(instance.name)
                c.start()
                while c.status != 'Running':
                    try:
                        c.sync()
                    except Exception as e:
                        self.agent.logger.info('run_entity()', '[ ERR ] LXD Plugin - {}'.format(e))
                        pass

                fm = c.FilesManager(self.conn, c)
                envs = 'export FOSUUID={} \n' \
                       'export FOSENTITYUUID={}\n' \
                       'export FOSNODEUUID={}'\
                    .format(instance_uuid, entity_uuid, self.agent.get_os_plugin().get_uuid())
                fm.put('/etc/profile.d/99-fos', envs, mode="0644")
                instance.on_start()

                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'run'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.current_entities.update({entity_uuid: entity})
                self.agent.logger.info('run_entity()', '[ DONE ] LXD Plugin - Starting a Container uuid {}'.format(instance_uuid))

                mt = threading.Thread(target=self.__monitor_instance, args=(entity_uuid, instance_uuid, instance.name),daemon=True)
                mt.start()
                self.mon_th.update({instance_uuid:mt}) 
                self.agent.logger.info('run_entity()', '[ DONE ] LXD Plugin - Starting a Monitoring of {}'.format(instance_uuid))
            return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' LXD Plugin - Stop a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('stop_entity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in RUNNING state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.RUNNING:
                self.agent.logger.error('clean_entity()',
                                        'LXD Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException('Instance is not in RUNNING state',
                                                         'Instance {} is not in RUNNING state'.format(entity_uuid))
            else:

                c = self.conn.containers.get(instance.name)
                self.mon_th.pop(instance_uuid)
                c.stop(force=False, wait=True)
                c.sync()

                while c.status != 'Stopped':
                    c.sync()



                instance.on_stop()
                self.current_entities.update({entity_uuid: entity})

                uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'stop'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.agent.logger.info('stop_entity()', '[ DONE ] LXD Plugin - Stop a Container uuid {}'.format(entity_uuid))

            return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('pause_entity()', ' LXD Plugin - Pause a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('pause_entity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('pause_entity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'LXD Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()',
                                            'LXD Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in RUNNING state',

                                                             'Instance {} is not in RUNNING state'.format(instance_uuid))
                else:
                    c = self.conn.containers.get(instance.name)
                    c.freeze()

                    instance.on_pause()
                    self.current_entities.update({entity_uuid: entity})
                    uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                    container_info = json.loads(self.agent.astore.get(uri))
                    container_info.update({'status': 'pause'})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                    self.agent.logger.info('pause_entity()', '[ DONE ] LXD Plugin - Pause a Container uuid {}'.format(instance_uuid))
                    return True

    def resume_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('resume_entity()', ' LXD Plugin - Resume a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('resume_entity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('resume_entity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'LXD Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.PAUSED:
                    self.agent.logger.error('clean_entity()',
                                            'LXD Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in PAUSED state',
                                                             'Instance {} is not in PAUSED state'.format(instance_uuid))
                else:
                    c = self.conn.containers.get(instance.name)
                    c.unfreeze()

                    instance.on_resume()
                    self.current_entities.update({entity_uuid: entity})

                    uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                    container_info = json.loads(self.agent.astore.get(uri))
                    container_info.update({'status': 'run'})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                    self.agent.logger.info('resume_entity()', '[ DONE ] LXD Plugin - Resume a Container uuid {}'.format(instance_uuid))
            return True

    def migrate_entity(self, entity_uuid, dst=False, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('migrate_entity()', ' LXD Plugin - Migrate a container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None or entity.get_instance(instance_uuid) is None:
            if dst is True:
                self.agent.logger.info('migrate_entity()', ' LXD Plugin - I\'m the Destination Node')
                self.before_migrate_entity_actions(entity_uuid, True, instance_uuid)

                uri_instance = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                instance_info = json.loads(self.agent.dstore.get(uri_instance))

                while True:
                    try:
                        c = self.conn.containers.get(instance_info.get('name'))
                        if c.status.upper() == 'running'.upper():
                            break
                        else:
                            self.agent.logger.info('migrate_entity()', ' LXD Plugin - Container in this host but not running')
                    except Exception as e:
                        self.agent.logger.info('migrate_entity()', ' LXD Plugin - Container not already in this host')
                    time.sleep(2)

                self.after_migrate_entity_actions(entity_uuid, True, instance_uuid)
                self.agent.logger.info('migrate_entity()', '[ DONE ] LXD Plugin - Migrate a Container uuid {}'.format(entity_uuid))
                return True

            else:
                self.agent.logger.error('migrate_entity()', 'LXD Plugin - Entity not exists')
                raise EntityNotExistingException('Enitity not existing',
                                                 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('migrate_entity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:

            instance = entity.get_instance(instance_uuid)
            if instance.get_state() not in [State.RUNNING, State.TAKING_OFF]:
                self.agent.logger.error('clean_entity()', 'LXD Plugin - Instance state is wrong, or transition not allowed')
                # self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                raise StateTransitionNotAllowedException('Instance is not in RUNNING state', 'Instance {} is not in RUNNING state'.format(entity_uuid))

            self.agent.logger.info('migrate_entity()', ' LXD Plugin - I\'m the Source Node')
            res = self.before_migrate_entity_actions(entity_uuid, instance_uuid=instance_uuid)
            if not res:
                self.agent.logger.error('migrate_entity()', ' LXD Plugin - Error source node before migration, aborting')
                # self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance migration error on source')
                return

            self.before_migrate_entity_actions(entity_uuid, False, instance_uuid)

            uri_instance = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
            instance_info = json.loads(self.agent.dstore.get(uri_instance))
            name = instance_info.get('entity_data').get('name')
            # destination node uuid
            destination_node_uuid = instance_info.get('dst')
            uri = '{}/{}'.format(self.agent.aroot, destination_node_uuid)

            while True:
                dst_node_info = self.agent.astore.get(uri)  # TODO: solve this ASAP
                if dst_node_info is not None:
                    if isinstance(dst_node_info, tuple):
                        dst_node_info = dst_node_info[0]
                    dst_node_info = dst_node_info.replace("'", '"')
                    break

            while True:
                luri = self.agent.ahome
                local_node_info = self.agent.astore.get(luri)  # TODO: solve this ASAP
                if local_node_info is not None:
                    if isinstance(local_node_info, tuple):
                        local_node_info = local_node_info[0]
                    local_node_info = local_node_info.replace("'", '"')
                    break
            # print(dst_node_info)
            dst_node_info = json.loads(dst_node_info)
            local_node_info = json.loads(local_node_info)

            nw = dst_node_info.get('network')
            dst_hostname = dst_node_info.get('name')
            dst_ip = [x for x in nw if x.get('default_gw') is True]
            # TODO: or x.get('inft_configuration').get('ipv6_gateway') for ip_v6
            if len(dst_ip) == 0:
                return False

            nw_local = local_node_info.get('network')
            local_ip = [x for x in nw_local if x.get('default_gw') is True]
            if len(local_ip) == 0:
                return False

            dst_ip = dst_ip[0].get('inft_configuration').get('ipv4_address')  # TODO: as on search should use ipv6
            local_ip = local_ip[0].get('inft_configuration').get('ipv4_address')  # TODO: as on search should use ipv6

            path_cert = os.path.join(self.DIR, 'templates', 'lxd.crt')
            path_key = os.path.join(self.DIR, 'templates', 'lxd.key')

            remote_client = Client(endpoint='https://{}:8443'.format(dst_ip), cert=(path_cert, path_key), verify=False)
            local_client = Client(endpoint='https://{}:8443'.format(local_ip), cert=(path_cert, path_key), verify=False)

            # remote_client = Client(endpoint='https://{}:8443'.format(dst_ip), verify=False)
            # local_client = Client(endpoint='https://{}:8443'.format(local_ip), verify=False)

            remote_client.authenticate('fog')
            local_client.authenticate('fog')

            cont = local_client.containers.get(instance_info.get('name'))

            try:
                cont.migrate(remote_client, wait=True)
            except LXDAPIException as e:
                self.agent.logger.info('migrate_entity()', ' LXD Plugin - LXD error {}'.format(e))
                cont.delete()
            instance.on_stop()

            self.current_entities.update({entity_uuid: entity})
            self.after_migrate_entity_actions(entity_uuid, False, instance_uuid)

    def before_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        if dst is True:
            self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Before Migration Destination')
            uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
            instance_info = json.loads(self.agent.dstore.get(uri))
            lxc_info = instance_info.get('entity_data')

            self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Waiting image')
            while True:
                base_image = lxc_info.get('base_image')
                if base_image in self.images.keys():
                    break

            self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Waiting entity')
            while True:
                if entity_uuid in self.current_entities.keys():
                    break
            self.agent.logger.info('before_migrate_entity_actions()', ' Entity {} defined!!!'.format(entity_uuid))

            img_info = self.images.get(base_image)
            entity = self.current_entities.get(entity_uuid)

            name = lxc_info.get('name')
            # disk_path = '{}.{}'.format(instance_uuid, img_info.get('format'))
            # cdrom_path = '{}_config.iso'.format(instance_uuid)
            # disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
            # cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)

            instance = LXDEntityInstance(instance_uuid, name, entity.networks, entity.image,
                                         entity.user_file, entity.ssh_key, entity.storage, entity.profiles,
                                         entity_uuid)

            instance.state = State.LANDING
            lxc_info.update({'name': name})

            instance_info.update({'entity_data': lxc_info})
            instance_info.update({'status': 'landing'})

            entity.add_instance(instance)
            self.current_entities.update({entity_uuid: entity})

            self.__update_actual_store_instance(entity_uuid, instance_uuid, instance_info)

            return True

        else:
            self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Before Migration Source: get information about destination node')

            local_var = MVar()
            def cb(key, value, v):
                local_var.put(value)


            entity = self.current_entities.get(entity_uuid, None)
            instance = entity.get_instance(instance_uuid)

            uri_entity = '{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid)
            entity_info = json.loads(self.agent.astore.get(uri_entity))
            entity_info.update({'status': 'define'})

            # reading instance info
            uri_instance = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
            instance_info = json.loads(self.agent.dstore.get(uri_instance))
            lxc_info = instance_info.get('entity_data')
            # destination node uuid
            destination_node_uuid = instance_info.get('dst')

            # flavor and image information
            flavor_info = self.flavors.get(lxc_info.get('flavor_id'))
            img_info = self.images.get(lxc_info.get('base_image'))

            # getting same plugin in destination node
            uri = '{}/{}/plugins'.format(self.agent.aroot, destination_node_uuid)
            all_plugins = json.loads(self.agent.astore.get(uri)).get('plugins')  # TODO: solve this ASAP

            runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
            search = [x for x in runtimes if 'LXD' in x.get('name')]
            if len(search) == 0:
                self.agent.logger.error('before_migrate_entity_actions()', 'LXD Plugin - Before Migration Source: No LXD Plugin, Aborting!!!')
                # self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance Migration error')
                return False
            else:
                lxd_uuid = search[0].get('uuid')

            # self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - check if image is present on destination')
            # uri_img = '{}/{}/runtime/{}/image/{}'.format(self.agent.aroot, destination_node_uuid, lxd_uuid, img_info)
            # if self.agent.astore.get(uri_img) is None:
            #     self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - sending image to destination')
            #     uri_img = '{}/{}/runtime/{}/image/{}'.format(self.agent.droot, destination_node_uuid, lxd_uuid, img_info)
            #     self.agent.dstore.put(uri_img, json.dumps(img_info))

            self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - check if entity is present on destination')
            uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.aroot, destination_node_uuid, lxd_uuid, entity_uuid)
            if self.agent.astore.get(uri_entity) is None:
                self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - sending entity to destination')
                uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.droot, destination_node_uuid, lxd_uuid, entity_uuid)
                self.agent.dstore.put(uri_entity, json.dumps(entity_info))
                self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - Waiting entity in destination')
                
                
                uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.aroot, destination_node_uuid, lxd_uuid, entity_uuid)
                subid = self.agent.astore.observe(uri_entity, cb)
                entity_info = json.loads(local_var.get())
                es = entity_info.get('status')
                while es not in ['defined','error']:
                    entity_info = json.loads(local_var.get())
                    es = entity_info.get('status')
                self.agent.astore.overlook(subid)
                self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - Entity in destination!')
                
                # while True:
                #     uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.aroot, destination_node_uuid, lxd_uuid, entity_uuid)
                #     jdata = self.agent.astore.get(uri_entity)
                #     # print('{}'.format(jdata))
                #     if jdata is not None:
                #         self.agent.logger.info('before_migrate_entity_actions()', 'LXD Plugin - Entity in destination!')
                #         entity_info = json.loads(jdata)
                #         if entity_info is not None and entity_info.get('status') == 'defined':
                #             break

            self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Before Migration Source: Waiting destination to be ready')
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.agent.aroot, destination_node_uuid, lxd_uuid, entity_uuid, instance_uuid)
            subid = self.agent.astore.observe(uri, cb)
            self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - Entity in destination!')
            entity_info = json.loads(local_var.get())
            es = entity_info.get('status')
            while es not in ['landing','error']:
                entity_info = json.loads(local_var.get())
                es = entity_info.get('status')
            self.agent.astore.overlook(subid)
            # while True:
            #     # self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Before Migration Source: Waiting destination to be ready')
            #     uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.agent.aroot, destination_node_uuid, lxd_uuid, entity_uuid, instance_uuid)
            #     lxc_info = self.agent.astore.get(uri)
            #     if lxc_info is not None:
            #         lxc_info = json.loads(lxc_info)
            #         if lxc_info is not None and lxc_info.get('status') == 'landing':
            #             break
            self.agent.logger.info('before_migrate_entity_actions()', ' LXD Plugin - Before Migration Source: Destination is ready!')

            instance.state = State.TAKING_OFF
            instance_info.update({'status': 'taking_off'})
            self.__update_actual_store_instance(entity_uuid, instance_uuid, instance_info)
            self.current_entities.update({entity_uuid: entity})
            return True

    def after_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('after_migrate_entity_actions()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('after_migrate_entity_actions()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in correct state',
                                                     'Entity {} is not in correct state'.format(entity.get_state()))
        else:
            if dst is True:
                '''
                Here the plugin also update to the current status, and remove unused keys
                '''
                instance = entity.get_instance(instance_uuid)
                '''
                Here the plugin also update to the current status, and remove unused keys
                '''
                self.agent.logger.info('after_migrate_entity_actions()', ' LXD Plugin - After Migration Destination: Updating state')
                instance.on_start()
                self.current_entities.update({entity_uuid: entity})

                uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                lxc_info = json.loads(self.agent.dstore.get(uri))
                lxc_info.pop('dst')
                lxc_info.update({'status': 'run'})

                self.__update_actual_store_instance(entity_uuid, instance_uuid, lxc_info)
                self.current_entities.update({entity_uuid: entity})

                return True
            else:
                '''
                Source node destroys all information about vm
                '''
                self.agent.logger.info('afterMigrateEntityActions()', ' LXD Plugin - After Migration Source: Updating state, destroy container')
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
                return True

    def __react_to_cache_entity(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' LXD Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'entity':
            uuid = uri.split('/')[-1]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            react_func = self.__react(action)
            if action == 'undefine':
                self.undefine_entity(uuid)
            elif react_func is not None and entity_data is None:
                react_func(uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': uuid})
                if action == 'define':
                    react_func(**entity_data)
                # else:
                #    if action == 'landing':
                #        react_func(entity_data, dst=True)
                #    else:
                #        react_func(entity_data)
        elif uri.split('/')[-2] == 'instance':
            instance_uuid = uri.split('/')[-1]
            entity_uuid = uri.split('/')[-3]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            # print(type(entity_data))
            react_func = self.__react(action)
            if action == 'clean':
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
            elif react_func is not None and entity_data is None:
                react_func(entity_uuid, instance_uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': entity_uuid})
                if action in ['landing', 'taking_off']:
                    self.agent.logger.warning('__react_to_cache_entity()', 'ACTION = {}'.format(action))
                    react_func(entity_data, dst=True, instance_uuid=instance_uuid)
                else:
                    react_func(entity_data, instance_uuid=instance_uuid)

    def __random_mac_generator(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: '%02x' % x, mac))

    def __lookup_by_uuid(self, uuid):
        domains = self.conn.listAllDomains(0)
        if len(domains) != 0:
            for domain in domains:
                if str(uuid) == domain.UUIDString():
                    return domain
        else:
            return None

    def __wait_boot(self, filename, configured=False):
        time.sleep(5)
        if configured:
            boot_regex = r"\[.+?\].+\[.+?\]:.+Cloud-init.+?v..+running.+'modules:final'.+Up.([0-9]*\.?[0-9]+).+seconds.\n"
        else:
            boot_regex = r".+?login:()"
        while True:
            file = open(filename, 'r')
            import os
            # Find the size of the file and move to the end
            st_results = os.stat(filename)
            st_size = st_results[6]
            file.seek(st_size)

            while 1:
                where = file.tell()
                line = file.readline()
                if not line:
                    time.sleep(1)
                    file.seek(where)
                else:
                    m = re.search(boot_regex, str(line))
                    if m:
                        found = m.group(1)
                        return found

    def __generate_custom_profile_userdata_configuration(self, userdata):
        userdata = {'user.user-data': userdata}
        return userdata

    def __generate_custom_profile_devices_configuration(self, instance):
        '''
        template = '[ {% for net in networks %}' \
                '{"eth{{loop.index -1 }}": ' \
                '{"name": "eth{{loop.index -1}}",' \
                '"type" : "nic",'  \
                '"parent": "{{ net.intf_name }}",' \
                '"nictype": "bridged" ,' \
                '"hwaddr" : {{ net.mac }} }"
                '{% endfor %} ]'
        '''
        devices = {}
        template_value_bridge = '{"name":"%s","type":"nic","parent":"%s","nictype":"bridged"}'
        template_value_bridge_mac = '{"name":"%s","type":"nic","parent":"%s","nictype":"bridged","hwaddr":"%s"}'
        template_value_phy = '{"name":"%s","type":"nic","parent":"%s","nictype":"physical"}'
        template_value_macvlan = '{"name":"%s","type":"nic","parent":"%s","nictype":"macvlan"}'

        '''
        # Create tenant's storage pool
        # TODO: allow more storage backends
        lxc storage create $TENANT dir

        # Add a root disk to the tenant's profile
        lxc profile device add $TENANT root disk path=/ pool=$TENANT

        '''

        template_disk = '{"path":"%s","type":"disk","pool":"%s"}'

        template_key = '{}'
        template_key2 = 'eth{}'
        for i, n in enumerate(instance.networks):
            if n.get('network_uuid') is not None:
                nws = self.agent.get_network_plugin(None).get(list(self.agent.get_network_plugin(None).keys())[0])
                # print(nws.getNetworkInfo(n.get('network_uuid')))
                br_name = nws.get_network_info(n.get('network_uuid')).get('virtual_device')
                # print(br_name)
                n.update({'br_name': br_name})
                if n.get('intf_name') is None:
                    n.update({'intf_name': 'eth{}'.format(i)})
                # nw_k = template_key % n.get('intf_name'))
                nw_k = template_key2.format(i)
                if n.get('mac') is not None:
                    nw_v = json.loads(str(template_value_bridge_mac % (n.get('intf_name'), n.get('br_name'), n.get('mac'))))
                else:
                    nw_v = json.loads(str(template_value_bridge % (n.get('intf_name'), n.get('br_name'))))

            elif self.agent.get_os_plugin().get_intf_type(n.get('br_name')) in ['ethernet']:
                # if n.get('')
                # cmd = "sudo ip link add name {} link {} type macvlan"
                # veth_name = 'veth-{}' % entity.uuid[:5])
                # cmd = cmd % (veth_name, n.get('br_name')))
                # self.agent.getOSPlugin().executeCommand(cmd, True)
                # nw_v = json.loads(template_value_phy % (n.get('intf_name'), veth_name)))
                nw_v = json.loads(str(template_value_macvlan % (n.get('intf_name'), n.get('br_name'))))
                # nw_k = template_key % n.get('intf_name'))
                nw_k = template_key2.format(i)
                # self.agent.getOSPlugin().set_interface_unaviable(n.get('br_name'))
            elif self.agent.get_os_plugin().get_intf_type(n.get('br_name')) in ['wireless']:
                nw_v = json.loads(str(template_value_phy % (n.get('intf_name'), n.get('br_name'))))
                # nw_k = template_key % n.get('intf_name'))
                nw_k = template_key2.format(i)
                self.agent.get_os_plugin().set_interface_unaviable(n.get('br_name'))
            else:
                if n.get('intf_name') is None:
                    n.update({'intf_name': 'eth{}'.format(i)})
                # nw_k = template_key % n.get('intf_name'))
                nw_k = template_key2.format(i)
                if n.get('mac') is not None:
                    nw_v = json.loads(str(template_value_bridge_mac % (n.get('intf_name'), n.get('br_name'), n.get('mac'))))
                else:
                    nw_v = json.loads(str(template_value_bridge % (n.get('intf_name'), n.get('br_name'))))
                

            devices.update({nw_k: nw_v})

        lxd_version = self.conn.host_info['environment']['server_version']
        if version.parse(lxd_version) >= version.parse('2.20'):
            if instance.storage is None or len(instance.storage) == 0:
                st_n = 'root'
                st_v = json.loads(str(template_disk % ('/', 'default')))
                devices.update({st_n: st_v})
            else:
                for s in instance.storage:
                    st_n = s.get('name')
                    st_v = json.loads(str(template_disk % (s.get('path'), s.get('pool'))))
                    devices.update({st_n: st_v})

        # devices = Environment().from_string(template)
        # devices = devices.render(networks=entity.networks)
        mid = {'machine-id': {'path': 'etc/machine-id', 'source': '/etc/machine-id', 'type': 'disk'}}
        devices.update(mid)
       
        return devices

    def __generate_container_dict(self, instance):
        conf = {'name': instance.name, 'profiles': instance.profiles,
                'source': {'type': 'image', 'alias': instance.image.get('uuid')}}
        self.agent.logger.info('__generate_container_dict()', 'LXD Plugin - Container Configuration {}'.format(conf))
        return conf

    def __update_actual_store(self, uri, value):
        uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME, uri)
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri, ):
        uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME, uri)
        self.agent.astore.remove(uri)

    def __update_actual_store_instance(self, entity_uuid, instance_uuid, value):
        uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store_instance(self, entity_uuid, instance_uuid, ):
        uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
        self.agent.astore.remove(uri)

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' LXD Plugin - Stop a container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'LXD Plugin - Entity not exists')
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'LXD Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() == State.PAUSED:
                    self.resume_entity(entity_uuid, instance_uuid)
                    self.stop_entity(entity_uuid, instance_uuid)
                    self.clean_entity(entity_uuid, instance_uuid)
                #    self.undefine_entity(k)
                if instance.get_state() == State.RUNNING:
                    self.stop_entity(entity_uuid, instance_uuid)
                    self.clean_entity(entity_uuid, instance_uuid)
                #    self.undefine_entity(k)
                if instance.get_state() == State.CONFIGURED:
                    self.clean_entity(entity_uuid, instance_uuid)
                #    self.undefine_entity(k)
                # if instance.get_state() == State.DEFINED:
                #    self.undefine_entity(k)

    def __monitor_instance(self, entity_id, instance_id, instance_name):
        self.agent.logger.info('__monitor_instance()', '[ INFO ] LXD Plugin - Staring monitoring of Container uuid {}'.format(instance_id))
        time.sleep(2)
        while True:
            time.sleep(2)
            uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_id, self.INSTANCE, instance_id)
            container_info = json.loads(self.agent.astore.get(uri))
            try:
                c = self.conn.containers.get(instance_name)
                cs = c.state()
                detailed_state = {}
                detailed_state.update({'network':cs.network})
                detailed_state.update({'cpu':cs.cpu})
                detailed_state.update({'memory':cs.memory})
                detailed_state.update({'disk':cs.disk})
                detailed_state.update({'processes':cs.processes})
                detailed_state.update({'pid':cs.pid})
                container_info.update({'detailed_state': detailed_state})
                self.__update_actual_store_instance(entity_id, instance_id, container_info)
                
                if c.status == 'Stopped':
                    self.agent.logger.info('__monitor_instance()', '[ INFO ] LXD Plugin - Stopping monitoring of Container uuid {}'.format(instance_id))
                    return
            except Exception as e:
                self.agent.logger.error('__monitor_instance()', '[ ERROR ] LXD Plugin - Stopping monitoring of Container uuid {} Error {}'.format(instance_id, e))
                return
                    

    def __add_image(self, manifest):
        url = manifest.get('base_image')
        uuid = manifest.get('uuid')
        if url.startswith('http'):
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, url.split('/')[-1])
            self.agent.get_os_plugin().download_file(url, image_name)
        elif url.startswith('file://'):
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, url.split('/')[-1])
            cmd = 'cp {} {}'.format(url[len('file://'):], image_name)
            self.agent.get_os_plugin().execute_command(cmd, True)

        self.agent.logger.info('__add_image()', '[ INFO ] LXD Plugin - Loading image data from: {}'.format(os.path.join(self.BASE_DIR, self.IMAGE_DIR, url)))
        image_data = self.agent.get_os_plugin().read_binary_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, image_name))
        self.agent.logger.info('__add_image()', '[ DONE ] LXD Plugin - Loading image data from: {}'.format(os.path.join(self.BASE_DIR, self.IMAGE_DIR, url)))
        img_info = {'url': url, 'path': image_name, 'uuid': uuid}

        self.agent.logger.info('__add_image()', '[ INFO ] LXD Plugin - Creating image with alias {}'.format(uuid))
        img = self.conn.images.create(image_data, public=True, wait=True)
        img.add_alias(uuid, description=image_name)
        self.agent.logger.info('__add_image()', '[ DONE ] LXD Plugin - Created image with alias {}'.format(uuid))
        self.images.update({uuid: img_info})
        manifest.update({'path': image_name})
        uri = '{}/{}'.format(self.HOME_IMAGE, manifest.get('uuid'))
        self.__update_actual_store(uri, manifest)

    def __remove_image(self, image_uuid):
        image = self.images.get(image_uuid, None)
        if image is None:
            self.agent.logger.info('__remove_image()', ' LXD Plugin - Image not found!!')
            return
        self.agent.get_os_plugin().remove_file(image.get('path'))
        self.images.pop(image_uuid)
        uri = '{}/{}'.format(self.HOME_IMAGE, image_uuid)
        self.__pop_actual_store(uri)

    def __add_flavor(self, manifest):
        uri = '{}/{}'.format(self.HOME_FLAVOR, manifest.get('uuid'))
        self.__update_actual_store(uri, manifest)
        self.flavors.update({manifest.get('uuid'): manifest})

    def __remove_flavor(self, flavor_uuid):
        self.flavors.pop(flavor_uuid)
        uri = '{}/{}'.format(self.HOME_FLAVOR, flavor_uuid)
        self.__pop_actual_store(uri)
    
    def __write_error_entity(self, entity_uuid, error):
        uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid)
        jdata = self.agent.dstore.get(uri)
        if jdata is not None:
            vm_info = json.loads(jdata)
        else:
            vm_info = {}

        vm_info.update({'status': 'error'})
        vm_info.update({'error': error})
        self.__update_actual_store(entity_uuid, vm_info)

    def __react_to_cache_image(self, uri, value, v):
        self.agent.logger.info('__react_to_cache_image()', 'LXD Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'image':
            image_uuid = uri.split('/')[-1]
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache_image()', 'LXD Plugin - This is a remove for URI: {}'.format(uri))
                self.__remove_image(image_uuid)
            else:
                value = json.loads(value)
                self.__add_image(value)

    def __react_to_cache_flavor(self, uri, value, v):
        self.agent.logger.info('__react_to_cache_flavor()', 'LXD Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'flavor':
            flavor_uuid = uri.split('/')[-1]
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache_flavor()', 'LXD Plugin - This is a remove for URI: {}'.format(uri))
                self.__remove_flavor(flavor_uuid)
            else:
                value = json.loads(value)
                self.__add_flavor(value)

    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'stop': self.stop_entity,
            'resume': self.resume_entity,
            'run': self.run_entity,
            'landing': self.migrate_entity,
            'taking_off': self.migrate_entity
        }

        return r.get(action, None)
