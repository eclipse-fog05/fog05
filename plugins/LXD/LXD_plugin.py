# Copyright (c) 2014,2018 ADLINK Technology Inc.
# 
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
# 
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0
# 
# SPDX-License-Identifier: EPL-2.0
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

# TODO Plugins should not be aware of the Agent - The Agent is in OCaml no way to access his store, his logger and the OS plugin


class LXD(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(LXD, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from LXD Plugin')
        self.BASE_DIR = "/opt/fos/lxd"
        self.DISK_DIR = "disks"
        self.IMAGE_DIR = "images"
        self.LOG_DIR = "logs"
        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.INSTANCE = "instance"
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.conn = None
        self.start_runtime()

    def start_runtime(self):
        self.agent.logger.info('startRuntime()', ' LXD Plugin - Connecting to LXD')
        self.conn = Client()
        self.agent.logger.info('startRuntime()', '[ DONE ] LXD Plugin - Connecting to LXD')
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('startRuntime()', ' LXD Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)

        '''check if dirs exists if not exists create'''
        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists(str("%s/%s") % (self.BASE_DIR, self.DISK_DIR)):
                self.agent.get_os_plugin().create_dir(str("%s/%s") % (self.BASE_DIR, self.DISK_DIR))
            if not self.agent.get_os_plugin().dir_exists(str("%s/%s") % (self.BASE_DIR, self.IMAGE_DIR)):
                self.agent.get_os_plugin().create_dir(str("%s/%s") % (self.BASE_DIR, self.IMAGE_DIR))
            if not self.agent.get_os_plugin().dir_exists(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR)):
                self.agent.get_os_plugin().create_dir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.get_os_plugin().create_dir(str("%s") % self.BASE_DIR)
            self.agent.get_os_plugin().create_dir(str("%s/%s") % (self.BASE_DIR, self.DISK_DIR))
            self.agent.get_os_plugin().create_dir(str("%s/%s") % (self.BASE_DIR, self.IMAGE_DIR))
            self.agent.get_os_plugin().create_dir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))


        return self.uuid

    def stop_runtime(self):
        self.agent.logger.info('stopRuntime()', 'LXD Plugin - Destroying %d running domains' % len(self.current_entities))
        keys = list(self.current_entities.keys())
        for k in keys:
            self.agent.logger.info('stopRuntime()', 'Stopping %s' % k)
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

        self.conn = None
        self.agent.logger.info('stopRuntime()', '[ DONE ] LXD Plugin - Bye Bye')

    def get_entities(self):
        return self.current_entities

    def define_entity(self, *args, **kwargs):
        """
        Try defining vm
        generating xml from templates/vm.xml with jinja2
        """
        self.agent.logger.info('defineEntity()', ' LXD Plugin - Defining a Container')
        if len(args) > 0:
            entity_uuid = args[4]
            '''
                The plugin should never enter here!!!
            '''
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            entity = LXDEntity(entity_uuid, kwargs.get('name'), kwargs.get('networks'), kwargs.get('base_image'),
                               kwargs.get('user-data'), kwargs.get('ssh-key'), kwargs.get('storage'),
                               kwargs.get("profiles"))
        else:
            return None

        if entity.image_url.startswith('http'):
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image_url.split('/')[-1])
            self.agent.get_os_plugin().download_file(entity.image_url, image_name)
        elif entity.image_url.startswith('file://'):
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image_url.split('/')[-1])
            cmd = 'cp {} {}'.format(entity.image_url[len('file://'):], image_name)
            self.agent.get_os_plugin().execute_command(cmd, True)


        entity.image = image_name
        entity.set_state(State.DEFINED)

        # TODO check what can go here and what should be in instance configuration
        # i think image should be here and profile generation in instance configuration
        self.agent.logger.info('defineEntity()', '[ INFO ] LXD Plugin - Loading image data from: {}'.format(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image)))
        image_data = self.agent.get_os_plugin().read_binary_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image))
        self.agent.logger.info('defineEntity()', '[ DONE ] LXD Plugin - Loading image data from: {}'.format(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image)))
        try:
            self.agent.logger.info('defineEntity()', '[ INFO ] LXD Plugin - Creating image with alias {}'.format(entity_uuid))
            img = self.conn.images.create(image_data, public=True, wait=True)
            img.add_alias(entity_uuid, description=entity.name)
            self.agent.logger.info('defineEntity()', '[ DONE ] LXD Plugin - Created image with alias {}'.format(entity_uuid))

            '''
            Should explore how to setup correctly the networking, seems that you can't decide the interface you 
            want to attach to the container
            Below there is a try using a profile customized for network
            '''
            # custom_profile_for_network = self.conn.profiles.create(entity_uuid)
            #
            # # WAN=$(awk '$2 == 00000000 { print $1 }' /proc/net/route)
            # ## eno1
            #
            # dev = self.__generate_custom_profile_devices_configuration(entity)
            # custom_profile_for_network.devices = dev
            # custom_profile_for_network.save()

        except LXDAPIException as e:
            self.agent.logger.error('define_entity()', 'Error {0}'.format(e))
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "error"})
            vm_info.update({"error": '{}'.format(e)})
            self.__update_actual_store(entity_uuid, vm_info)
            self.agent.logger.info('defineEntity()', '[ ERRO ] LXD Plugin - Container uuid: %s' % entity_uuid)
            return entity_uuid

        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        vm_info = json.loads(self.agent.dstore.get(uri))
        vm_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, vm_info)
        self.agent.logger.info('defineEntity()', '[ DONE ] LXD Plugin - Container uuid: %s' % entity_uuid)
        return entity_uuid

    def undefine_entity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' LXD Plugin - Undefine a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)

            try:

                img = self.conn.images.get_by_alias(entity_uuid)
                img.delete()
            except LXDAPIException as e:
                self.agent.logger.error('undefine_entity()', 'Error {0}'.format(e))
                pass

            self.current_entities.pop(entity_uuid, None)
            self.agent.get_os_plugin().remove_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image))
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] LXD Plugin - Undefine a Container uuid %s ' %
                                   entity_uuid)
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' LXD Plugin - Configure a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            ''' 
                See if is possible to:
                - Put rootfs and images inside a custom path
            '''

            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print("This instance already existis!!")
            else:
                id = len(entity.instances)
                name = '{0}{1}'.format(entity.name,id)
                #uuid, name, networks, image, user_file, ssh_key, storage, profiles, entity_uuid)
                instance = LXDEntityInstance(instance_uuid, name, entity.networks,entity.image,
                                            entity.user_file, entity.ssh_key, entity.storage, entity.profiles ,
                                             entity_uuid)

                #wget_cmd = str('wget %s -O %s/%s/%s' % (entity.image, self.BASE_DIR, self.IMAGE_DIR, image_name))

                #self.agent.getOSPlugin().downloadFile(entity.image, os.path.join(self.BASE_DIR, self.IMAGE_DIR,
                # image_name))

                #self.agent.getOSPlugin().executeCommand(wget_cmd, True)

                #image_data = self.agent.get_os_plugin().read_binary_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image))
                self.agent.logger.info('configureEntity()', '[ INFO ] LXD Plugin - Creating profile...')
                try:
                    #img = self.conn.images.create(image_data, public=True, wait=True)
                    #img.add_alias(entity_uuid, description=entity.name)

                    '''
                    Should explore how to setup correctly the networking, seems that you can't decide the interface you 
                    want to attach to the container
                    Below there is a try using a profile customized for network
                    '''



                    custom_profile_for_instance = self.conn.profiles.create(instance_uuid)

                    #WAN=$(awk '$2 == 00000000 { print $1 }' /proc/net/route)
                    ## eno1
                    if instance.user_file is not None and instance.user_file != '':
                        user_data = self.__generate_custom_profile_userdata_configuration(instance.user_file)
                        custom_profile_for_instance.config = user_data

                    dev = self.__generate_custom_profile_devices_configuration(instance)
                    custom_profile_for_instance.devices = dev
                    custom_profile_for_instance.save()

                except LXDAPIException as e:
                    self.agent.logger.error('configureEntity()', 'Error {0}'.format(e))
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

                uri = str('%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid))
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({"status": "configured"})

                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                #self.__update_actual_store(entity_uuid, container_info)
                self.agent.logger.info('configureEntity()', '[ DONE ] LXD Plugin - Configure a Container uuid %s ' %
                                       instance_uuid)
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('cleanEntity()', ' LXD Plugin - Clean a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('cleanEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('cleanEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()','LXD Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                        'LXD Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                         str("Instance %s is not in CONFIGURED state" % instance_uuid))
                else:

                    self.agent.logger.info('cleanEntity()', '{0}'.format(instance))
                    c = self.conn.containers.get(instance.name)
                    c.delete()

                    #img = self.conn.images.get_by_alias(entity_uuid)
                    #img.delete()


                    time.sleep(2)
                    profile = self.conn.profiles.get(instance_uuid)

                    while True:
                        if len(profile.used_by) == 0:
                            break
                        time.sleep(1)
                    profile.delete()

                    '''
                    {'wan': {'nictype': 'physical', 'name': 'wan', 'type': 'nic', 'parent': 'veth-af90f'}, 
                    'root': {'type': 'disk', 'pool': 'default', 'path': '/'}, 
                    'mgmt': {'nictype': 'bridged', 'name': 'mgmt', 'type': 'nic', 'parent': 'br-45873fb0'}}
        
                    '''


                    #self.agent.getOSPlugin().removeFile(str("%s/%s/%s") % (self.BASE_DIR, self.IMAGE_DIR,
                    # entity.image))

                    instance.on_clean()
                    entity.remove_instance(instance)
                    self.current_entities.update({entity_uuid: entity})

                    #uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                    #container_info = json.loads(self.agent.dstore.get(uri))
                    #container_info.update({"status": "cleaned"})
                    #self.__update_actual_store(entity_uuid, container_info)
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('cleanEntity()', '[ DONE ] LXD Plugin - Clean a Container uuid %s ' % instance_uuid)

            return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('runEntity()', ' LXD Plugin - Starting a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('runEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('runEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.CONFIGURED:
                self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                         str("Instance %s is not in CONFIGURED state" % instance_uuid))
            else:
                uri = str('%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid))
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({"status": "starting"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.current_entities.update({entity_uuid: entity})

                c = self.conn.containers.get(instance.name)
                c.start()

                instance.on_start()

                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({"status": "run"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.current_entities.update({entity_uuid: entity})
                self.agent.logger.info('runEntity()', '[ DONE ] LXD Plugin - Starting a Container uuid %s ' % instance_uuid)
            return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stopEntity()', ' LXD Plugin - Stop a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stopEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('stopEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.RUNNING:
                self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException("Instance is not in RUNNING state",
                                                         str("Instance %s is not in RUNNING state" % entity_uuid))
            else:

                c = self.conn.containers.get(instance.name)
                c.stop()
                c.sync()

                while c.status != 'Stopped':
                    c.sync()
                    pass

                instance.on_stop()
                self.current_entities.update({entity_uuid: entity})

                uri = str('%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid))
                container_info = json.loads(self.agent.astore.get(uri))
                container_info.update({"status": "stop"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                self.agent.logger.info('stopEntity()', '[ DONE ] LXD Plugin - Stop a Container uuid %s ' % entity_uuid)

            return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('pauseEntity()', ' LXD Plugin - Pause a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('pauseEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('pauseEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()',
                                            'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in RUNNING state",
                                                             str(
                                                                 "Instance %s is not in RUNNING state" % instance_uuid))
                else:
                    c = self.conn.containers.get(instance.name)
                    c.freeze()

                    instance.on_pause()
                    self.current_entities.update({entity_uuid: entity})
                    uri = str('%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid))
                    container_info = json.loads(self.agent.astore.get(uri))
                    container_info.update({"status": "pause"})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, container_info)
                    self.agent.logger.info('pauseEntity()', '[ DONE ] LXD Plugin - Pause a Container uuid %s ' % instance_uuid)
                    return True

    def resume_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('resumeEntity()', ' LXD Plugin - Resume a Container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('resumeEntity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('resumeEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.PAUSED:
                    self.agent.logger.error('clean_entity()',
                                            'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in PAUSED state",
                                                             str(
                                                                 "Instance %s is not in PAUSED state" % instance_uuid))
                else:
                    c = self.conn.containers.get(instance.name)
                    c.unfreeze()

                    instance.on_resume()
                    self.current_entities.update({entity_uuid: entity})

                    uri = str('%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid))
                    container_info = json.loads(self.agent.astore.get(uri))
                    container_info.update({"status": "run"})
                    self.__update_actual_store_instance(entity_uuid,instance_uuid, container_info)
                    self.agent.logger.info('resumeEntity()', '[ DONE ] LXD Plugin - Resume a Container uuid %s ' % instance_uuid)
            return True


    # def migrate_entity(self, entity_uuid, dst=False, instance_uuid=None):
    #     if type(entity_uuid) == dict:
    #         entity_uuid = entity_uuid.get('entity_uuid')
    #     self.agent.logger.info('migrateEntity()', ' LXD Plugin - Migrate a Container uuid %s ' % entity_uuid)
    #     entity = self.current_entities.get(entity_uuid, None)
    #     if entity is None:
    #         if dst is True:
    #             self.agent.logger.info('migrateEntity()', " LXD Plugin - I\'m the Destination Node")
    #             self.before_migrate_entity_actions(entity_uuid, True)
    #
    #             '''
    #                 migration steps from destination node
    #             '''
    #
    #             self.after_migrate_entity_actions(entity_uuid, True)
    #             self.agent.logger.info('migrateEntity()', '[ DONE ] LXD Plugin - Migrate a Container uuid %s ' %
    #                                    entity_uuid)
    #             return True
    #
    #         else:
    #             self.agent.logger.error('migrateEntity()', 'LXD Plugin - Entity not exists')
    #             raise EntityNotExistingException("Enitity not existing",
    #                                              str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
    #     elif entity.get_state() != State.RUNNING:
    #         self.agent.logger.error('migrateEntity()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
    #         raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
    #                                                  str("Entity %s is not in RUNNING state" % entity_uuid))
    #     else:
    #         self.agent.logger.info('migrateEntity()', " LXD Plugin - I\'m the Source Node")
    #         self.before_migrate_entity_actions(entity_uuid)
    #         self.after_migrate_entity_actions(entity_uuid)
    #
    #
    # def before_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
    #     if dst is True:
    #         self.agent.logger.info('beforeMigrateEntityActions()', ' LXD Plugin - Before Migration Destination')
    #
    #         #self.current_entities.update({entity_uuid: entity})
    #
    #         #entity_info.update({"status": "landing"})
    #         #self.__update_actual_store(entity_uuid, cont_info)
    #
    #         return True
    #     else:
    #         self.agent.logger.info('beforeMigrateEntityActions()', ' LXD Plugin - Before Migration Source: get information about destination node')
    #
    #
    #         return True
    #
    # def after_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
    #     if type(entity_uuid) == dict:
    #         entity_uuid = entity_uuid.get('entity_uuid')
    #     entity = self.current_entities.get(entity_uuid, None)
    #     if entity is None:
    #         self.agent.logger.error('afterMigrateEntityActions()', 'LXD Plugin - Entity not exists')
    #         raise EntityNotExistingException("Enitity not existing",
    #                                          str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
    #     elif entity.get_state() not in (State.TAKING_OFF, State.LANDING, State.RUNNING):
    #         self.agent.logger.error('afterMigrateEntityActions()', 'LXD Plugin - Entity state is wrong, or transition not allowed')
    #         raise StateTransitionNotAllowedException("Entity is not in correct state",
    #                                                  str("Entity %s is not in correct state" % entity.get_state()))
    #     else:
    #         if dst is True:
    #             '''
    #             Here the plugin also update to the current status, and remove unused keys
    #             '''
    #             self.agent.logger.info('afterMigrateEntityActions()', ' LXD Plugin - After Migration Destination: Updating state')
    #             entity.state = State.RUNNING
    #             self.current_entities.update({entity_uuid: entity})
    #
    #             uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
    #             cont_info = json.loads(self.agent.dstore.get(uri))
    #             cont_info.update({"status": "run"})
    #             self.__update_actual_store(entity_uuid, cont_info)
    #
    #             return True
    #         else:
    #             '''
    #             Source node destroys all information about vm
    #             '''
    #             self.agent.logger.info('afterMigrateEntityActions()', ' LXD Plugin - After Migration Source: Updating state, destroy container')
    #             entity.state = State.CONFIGURED
    #             self.current_entities.update({entity_uuid: entity})
    #             self.clean_entity(entity_uuid)
    #             self.undefine_entity(entity_uuid)
    #             return True

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' LXD Plugin - React to to URI: %s Value: %s Version: %s' % (uri, value, v))
        if uri.split('/')[-2] == 'entity':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' LXD Plugin - This is a remove for URI: %s' % uri)
                entity_uuid = uri.split('/')[-1]
                self.undefine_entity(entity_uuid)
            else:
                uuid = uri.split('/')[-1]
                value = json.loads(value)
                action = value.get('status')
                entity_data = value.get('entity_data')
                react_func = self.__react(action)
                if react_func is not None and entity_data is None:
                    react_func(uuid)
                elif react_func is not None:
                    entity_data.update({'entity_uuid': uuid})
                    if action == 'define':
                        react_func(**entity_data)
                    #else:
                    #    if action == 'landing':
                    #        react_func(entity_data, dst=True)
                    #    else:
                    #        react_func(entity_data)
        elif uri.split('/')[-2] == 'instance':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' LXD Plugin - This is a remove for URI: %s' % uri)
                instance_uuid = uri.split('/')[-1]
                entity_uuid = uri.split('/')[-3]
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
            else:
                instance_uuid = uri.split('/')[-1]
                entity_uuid = uri.split('/')[-3]
                value = json.loads(value)
                action = value.get('status')
                entity_data = value.get('entity_data')
                # print(type(entity_data))
                react_func = self.__react(action)
                if react_func is not None and entity_data is None:
                    react_func(entity_uuid, instance_uuid)
                elif react_func is not None:
                    entity_data.update({'entity_uuid': entity_uuid})
                    #if action == 'landing':
                    #    react_func(entity_data, dst=True, instance_uuid=instance_uuid)
                    #else:
                    #    react_func(entity_data, instance_uuid=instance_uuid)

    def __random_mac_generator(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

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

        template_key = '%s'
        template_key2 = "eth%d"
        for i, n in enumerate(instance.networks):
            if n.get('network_uuid') is not None:
                nws = self.agent.get_network_plugin(None).get(list(self.agent.get_network_plugin(None).keys())[0])
                # print(nws.getNetworkInfo(n.get('network_uuid')))
                br_name = nws.get_network_info(n.get('network_uuid')).get('virtual_device')
                # print(br_name)
                n.update({'br_name': br_name})
                if n.get('intf_name') is None:
                    n.update({'intf_name': "eth"+str(i)})
                #nw_k = str(template_key % n.get('intf_name'))
                nw_k = str(template_key2 % i)
                if n.get('mac') is not None:
                    nw_v = json.loads(str(template_value_bridge_mac % (n.get('intf_name'), n.get('br_name'), n.get('mac'))))
                else:
                    nw_v = json.loads(str(template_value_bridge % (n.get('intf_name'), n.get('br_name'))))

            elif self.agent.get_os_plugin().get_intf_type(n.get('br_name')) in ['ethernet']:
                #if n.get('')
                #cmd = "sudo ip link add name %s link %s type macvlan"
                #veth_name = str('veth-%s' % entity.uuid[:5])
                #cmd = str(cmd % (veth_name, n.get('br_name')))
                #self.agent.getOSPlugin().executeCommand(cmd, True)
                #nw_v = json.loads(str(template_value_phy % (n.get('intf_name'), veth_name)))
                nw_v = json.loads(str(template_value_macvlan % (n.get('intf_name'), n.get('br_name'))))
                #nw_k = str(template_key % n.get('intf_name'))
                nw_k = str(template_key2 % i)
                #self.agent.getOSPlugin().set_interface_unaviable(n.get('br_name'))
            elif self.agent.get_os_plugin().get_intf_type(n.get('br_name')) in ['wireless']:
                nw_v = json.loads(str(template_value_phy % (n.get('intf_name'), n.get('br_name'))))
                #nw_k = str(template_key % n.get('intf_name'))
                nw_k = str(template_key2 % i)
                self.agent.get_os_plugin().set_interface_unaviable(n.get('br_name'))
            else:
                if n.get('intf_name') is None:
                    n.update({'intf_name': "eth" + str(i)})
                #nw_k = str(template_key % n.get('intf_name'))
                nw_k = str(template_key2 % i)
                nw_v = json.loads(str(template_value_bridge % (n.get('intf_name'), n.get('br_name'))))

            devices.update({nw_k: nw_v})

        lxd_version = self.conn.host_info['environment']['server_version']
        if version.parse(lxd_version) >= version.parse("2.20"):
            if instance.storage is None or len(instance.storage) == 0:
                st_n = "root"
                st_v = json.loads(str(template_disk % ("/","default")))
                devices.update({st_n: st_v})
            else:
                for s in instance.storage:
                    st_n = s.get("name")
                    st_v = json.loads(str(template_disk % (s.get("path"), s.get("pool"))))
                    devices.update({st_n: st_v})

        #devices = Environment().from_string(template)
        #devices = devices.render(networks=entity.networks)
        return devices

    def __generate_container_dict(self, instance):
        conf = {'name': instance.name, "profiles":  instance.profiles,
                'source': {'type': 'image', 'alias': instance.entity_uuid}}
        return conf

    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri,):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)

    def __update_actual_store_instance(self, entity_uuid, instance_uuid, value):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store_instance(self, entity_uuid, instance_uuid,):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        self.agent.astore.remove(uri)

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' LXD Plugin - Stop a container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
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
                #if instance.get_state() == State.DEFINED:
                #    self.undefine_entity(k)


    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'clean': self.clean_entity,
            'undefine': self.undefine_entity,
            'stop': self.stop_entity,
            'resume': self.resume_entity,
            'run': self.run_entity
            #'landing': self.migrateEntity,
            #'taking_off': self.migrateEntity
        }

        return r.get(action, None)
