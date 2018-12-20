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
from DockEntity import DockEntity
from DockEntityInstance import DockEntityInstance
from jinja2 import Environment
import json
import random
import time
import re
import threading
import docker


# TODO Plugins should not be aware of the Agent - The Agent is in OCaml no way to access his store, his logger and the OS plugin


class Dock(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(Dock, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from Docker Plugin')
        self.BASE_DIR = '/opt/fos/docker'
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
            'startRuntime()', ' Docker Plugin - Connecting to Docker')
        self.conn = docker.from_env()
        self.agent.logger.info(
            'startRuntime()', '[ DONE ] Docker Plugin - Connecting to Docker')
        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME)
        self.agent.logger.info(
            'startRuntime()', ' Docker Plugin - Observing {} for entity'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_entity)

        # uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_FLAVOR)
        # self.agent.logger.info(
        #     'startRuntime()', ' Docker Plugin - Observing {} for flavor'.format(uri))
        # self.agent.dstore.observe(uri, self.__react_to_cache_flavor)

        # uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_IMAGE)
        # self.agent.logger.info(
        #     'startRuntime()', ' Docker Plugin - Observing {} for image'.format(uri))
        # self.agent.dstore.observe(uri, self.__react_to_cache_image)

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
            'stopRuntime()', 'Docker Plugin - Destroying {} running domains'.format(len(self.current_entities)))
        keys = list(self.current_entities.keys())
        for k in keys:
            self.agent.logger.info('stopRuntime()', 'Stopping {}'.format(k))
            entity = self.current_entities.get(k)
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(k, i)
            if entity.get_state() == State.DEFINED:
                self.undefine_entity(k)
        keys = list(self.images.keys())
        for k in keys:
            self.agent.logger.info(
                'stopRuntime()', 'Removing Image {}'.format(k))
            try:
                img = self.images.get(k)
                self.conn.images.remove(img.get('docker_name'))
            except Exception as e:
                self.agent.logger.error('stopRuntime()', 'Error {}'.format(e))
                pass

        self.conn = None
        self.agent.logger.info(
            'stopRuntime()', '[ DONE ] Docker Plugin - Bye Bye')

    def get_entities(self):
        return self.current_entities

    def define_entity(self, *args, **kwargs):
        '''
        Try defining vm
        generating xml from templates/vm.xml with jinja2
        '''
        self.agent.logger.info(
            'defineEntity()', ' Docker Plugin - Defining a Container')
        if len(args) > 0:
            entity_uuid = args[4]
            '''
                The plugin should never enter here!!!
            '''
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            entity = DockEntity(entity_uuid, kwargs.get('name'),  kwargs.get(
                'base_image'), kwargs.get('port-mappings'))
        else:
            return None

        if entity.image_url.startswith('file://'):
            image_name = os.path.join(
                self.BASE_DIR, self.IMAGE_DIR, entity.image_url.split('/')[-1])
            cmd = 'cp {} {}'.format(
                entity.image_url[len('file://'):], image_name)
            self.agent.get_os_plugin().execute_command(cmd, True)
            self.agent.logger.info('defineEntity()', '[ INFO ] LXD Plugin - Loading image data from: {}'.format(
                os.path.join(self.BASE_DIR, self.IMAGE_DIR, image_name)))
            image_name = os.path.join(
                self.BASE_DIR, self.IMAGE_DIR, image_name)

        else:
            self.agent.logger.Error(
                 'defineEntity()', 'Error image can only be a local file!!')
            return None

        img_data = self.agent.get_os_plugin().read_binary_file(image_name)
        img = self.conn.images.load(img_data)[0]
        self.agent.logger.info('defineEntity()', '[ DONE ] Docker Plugin - Created image with tags {}'.format(img.tags[0]))
        img_info = {}
        img_info.update({'uuid': entity_uuid})
        img_info.update({'name': '{}_img'.format(entity.name)})
        img_info.update({'base_image': image_name})
        img_info.update({'type': 'Docker'})
        img_info.update({'docker_name':img.tags[0]})
        img_info.update({'format': '.'.join(image_name.split('.')[-2:])})
        entity.image = img_info
        self.images.update({entity_uuid: img_info})
        uri = '{}/{}'.format(self.HOME_IMAGE, entity_uuid)
        self.__update_actual_store(uri, img_info)

           

        entity.image = img_info
        entity.set_state(State.DEFINED)
        
        uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME, entity_uuid)
        docker_info = json.loads(self.agent.dstore.get(uri))
        e_data = docker_info.get('entity_data')
        e_data.update({'base_image': img_info.get('docker_name')})
        docker_info.update({'status': 'defined'})
        docker_info.update({'entity_data': e_data})
        self.current_entities.update({entity_uuid: entity})
        self.__update_actual_store(entity_uuid, docker_info)
        self.agent.logger.info('defineEntity()', '[ DONE ] Docker Plugin - Container uuid: {}'.format(entity_uuid))
        return entity_uuid

    def undefine_entity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' Docker Plugin - Undefine a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)
                
            img = entity.image.get('docker_name')
            self.conn.images.remove(img)
            self.current_entities.pop(entity_uuid, None)
            # self.agent.get_os_plugin().remove_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image.get('base_image')))
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] Docker Plugin - Undefine a Container uuid {}'.format(entity_uuid))
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' Docker Plugin - Configure a Container uuid {} '.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
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
                instance = DockEntityInstance(instance_uuid, name, entity.image,entity.ports_mappings, entity_uuid)

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
                self.agent.logger.info('configureEntity()', '[ DONE ] Docker Plugin - Configure a Container uuid {}'.format(instance_uuid))
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('clean_entity()', ' Docker Plugin - Clean a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('clean_entity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('clean_entity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()', 'Docker Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                            'Docker Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state',
                                                             'Instance {} is not in CONFIGURED state'.format(instance_uuid))
                else:
                    self.agent.logger.info('clean_entity()', '{}'.format(instance))
                        
                    instance.on_clean()
                    entity.remove_instance(instance)
                    self.current_entities.update({entity_uuid: entity})

                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('clean_entity()', '[ DONE ] Docker Plugin - Clean a Container uuid {} '.format(instance_uuid))

            return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('run_entity()', ' Docker Plugin - Starting a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('run_entity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('run_entity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() == State.RUNNING:
                self.agent.logger.error('run_entity()',
                                        'Docker Plugin - Instance already running')
                return True
            if instance.get_state() != State.CONFIGURED:
                self.agent.logger.error('clean_entity()',
                                        'Docker Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state',
                                                         'Instance {} is not in CONFIGURED state'.format(instance_uuid))
            else:
                uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'starting'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.current_entities.update({entity_uuid: entity})

                image_name = instance.image.get('docker_name')
                pm = {}
                for k in instance.ports_mappings:
                    v = instance.ports_mappings.get(k)
                    pm.update({int(k): v})
                print(pm)
                # ports = list(pm.keys())
                # hc = self.conn.create_host_config(port_bindings=pm)
                self.agent.logger.info('run_entity()', '[ INFO ] IMAGE: {}'.format(image_name))
                self.agent.logger.info('run_entity()', '[ INFO ] PORTS: {}'.format(pm))
                # self.agent.logger.info('run_entity()', '[ INFO ] Host Config: {}'.format(hc))
                cid = self.conn.containers.run(image_name, ports=pm, name=instance.name, detach = True)
                # cid = self.conn.create_container(image=image_name, ports=ports, host_config=hc, name=instance.name)
                # self.conn.start(cid)
                instance.on_start(cid)

                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'run'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.current_entities.update({entity_uuid: entity})
                self.agent.logger.info('run_entity()', '[ DONE ] Docker Plugin - Starting a Container uuid {}'.format(instance_uuid))

            return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' Docker Plugin - Stop a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('stop_entity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in RUNNING state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.RUNNING:
                self.agent.logger.error('clean_entity()',
                                        'Docker Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException('Instance is not in RUNNING state',
                                                         'Instance {} is not in RUNNING state'.format(entity_uuid))
            else:

                instance.cid.stop()
                instance.cid.remove()

                instance.on_stop()
                self.current_entities.update({entity_uuid: entity})

                uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({'status': 'stop'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.agent.logger.info('stop_entity()', '[ DONE ] Docker Plugin - Stop a Container uuid {}'.format(entity_uuid))

            return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('pause_entity()', ' Docker Plugin - Pause a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('pause_entity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('pause_entity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'Docker Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()',
                                            'Docker Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in RUNNING state',

                                                             'Instance {} is not in RUNNING state'.format(instance_uuid))
                else:
                    self.agent.logger.info('pause_entity()', '[ DONE ] Docker Plugin - Pause a Container uuid {}'.format(instance_uuid))
                    return True

    def resume_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('resume_entity()', ' Docker Plugin - Resume a Container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('resume_entity()', 'Docker Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('resume_entity()', 'Docker Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'Docker Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.PAUSED:
                    self.agent.logger.error('clean_entity()',
                                            'Docker Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in PAUSED state',
                                                             'Instance {} is not in PAUSED state'.format(instance_uuid))
                else:
                    self.agent.logger.info('resume_entity()', '[ DONE ] Docker Plugin - Resume a Container uuid {}'.format(instance_uuid))
            return True

    def migrate_entity(self, entity_uuid, dst=False, instance_uuid=None):
        raise NotImplementedError

    def before_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        raise NotImplementedError

    def after_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        raise NotImplementedError

    def __react_to_cache_entity(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' Docker Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
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
        self.agent.logger.info('stop_entity()', ' Docker Plugin - Stop a container uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'Docker Plugin - Entity not exists')
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'Docker Plugin - Instance not found!!')
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

    def __add_image(self, manifest):
        raise NotImplementedError

    def __remove_image(self, image_uuid):
       raise NotImplementedError

    def __add_flavor(self, manifest):
       raise NotImplementedError

    def __remove_flavor(self, flavor_uuid):
       raise NotImplementedError
    
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
        raise NotImplementedError

    def __react_to_cache_flavor(self, uri, value, v):
        raise NotImplementedError

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
