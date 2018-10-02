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
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from KVMLibvirtEntity import KVMLibvirtEntity
from KVMLibvirtEntityInstance import KVMLibvirtEntityInstance
from jinja2 import Environment
import json
import random
import time
import re
import libvirt
import ipaddress
import threading


# TODO Plugins should not be aware of the Agent - The Agent is in OCaml no way to access his store, his logger and the OS plugin

class KVMLibvirt(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(KVMLibvirt, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from KVM Plugin')
        self.BASE_DIR = os.path.join(self.agent.base_path, 'kvm')
        self.DISK_DIR = 'disks'
        self.IMAGE_DIR = 'images'
        self.LOG_DIR = 'logs'
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

        self.start_runtime()

    def start_runtime(self):
        self.agent.logger.info('startRuntime()', ' KVM Plugin - Connecting to KVM')
        self.conn = libvirt.open('qemu:///system')
        self.agent.logger.info('startRuntime()', '[ DONE ] KVM Plugin - Connecting to KVM')
        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_ENTITY)
        self.agent.logger.info('startRuntime()', ' KVM Plugin - Observing {} for entity'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_entity)

        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_FLAVOR)
        self.agent.logger.info('startRuntime()', ' KVM Plugin - Observing {} for flavor'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_flavor)

        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME_IMAGE)
        self.agent.logger.info('startRuntime()', ' KVM Plugin - Observing {} for image'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache_image)

        '''check if dirs exists if not exists create'''
        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.DISK_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DISK_DIR))
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.IMAGE_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.IMAGE_DIR))
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.LOG_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.get_os_plugin().create_dir(self.BASE_DIR)
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DISK_DIR))
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.IMAGE_DIR))
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.LOG_DIR))
        return self.uuid

    def stop_runtime(self):
        self.agent.logger.info('stopRuntime()', ' KVM Plugin - Destroying running domains')
        for k in list(self.current_entities.keys()):
            entity = self.current_entities.get(k)
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(k, i)
            if entity.get_state() == State.DEFINED:
                self.undefine_entity(k)

        for k in list(self.images.keys()):
            self.__remove_image(k)
        for k in list(self.flavors.keys()):
            self.__remove_flavor(k)

        try:
            self.conn.close()
        except libvirt.libvirtError as err:
            pass
        self.agent.logger.info('stopRuntime()', '[ DONE ] KVM Plugin - Bye Bye')

    def get_entities(self):
        return self.current_entities

    def define_entity(self, *args, **kwargs):
        self.agent.logger.info('define_entity()', ' KVM Plugin - Defining a VM')

        entity = None
        img = None
        flavor = None

        if len(kwargs) > 0:
            self.agent.logger.info('define_entity()', ' KVM Plugin - Called with **kwargs')
            entity_uuid = kwargs.get('entity_uuid')
            base_image = kwargs.get('base_image')
            name = kwargs.get('name')

            if self.is_uuid(base_image):
                img = self.images.get(base_image, None)
                if img is None:
                    self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Cannot find image {}'.format(base_image))
                    self.__write_error_entity(entity_uuid, 'Image not found!')
                    return
            else:
                self.agent.logger.warning('define_entity()', '[ WARN ] KVM Plugin - No image id specified defining from manifest information new image id uuid:{}'.format(entity_uuid))
                img_info = {}
                img_info.update({'uuid': entity_uuid})
                img_info.update({'name': '{}_img'.format(name)})
                img_info.update({'base_image': base_image})
                img_info.update({'format': base_image.split('.')[-1]})
                self.__add_image(img_info)
                img = self.images.get(entity_uuid, None)
                if img is None:
                    self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Cannot find image {}'.format(entity_uuid))
                    self.__write_error_entity(entity_uuid, 'Image not found!')
                    return

            if kwargs.get('flavor_id', None) is None:
                self.agent.logger.warning('define_entity()', '[ WARN ] KVM Plugin - No flavor specified defining from manifest information new flavor uuid:{}'.format(entity_uuid))
                cpu = kwargs.get('cpu')
                mem = kwargs.get('memory')
                disk_size = kwargs.get('disk_size')
                flavor_info = {}
                flavor_info.update({'name': '{}_flavor'.format(name)})
                flavor_info.update({'uuid': entity_uuid})
                flavor_info.update({'cpu': cpu})
                flavor_info.update({'memory': mem})
                flavor_info.update({'disk_size': disk_size})
                self.__add_flavor(flavor_info)
                flavor = self.flavors.get(entity_uuid, None)
                if flavor is None:
                    self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Cannot find flavor {}'.format(entity_uuid))
                    self.__write_error_entity(entity_uuid, 'Flavor not found!')
                    return
            else:
                flavor = self.flavors.get(kwargs.get('flavor_id'), None)
                if flavor is None:
                    self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Cannot find flavor {}'.format(kwargs.get('flavor_id')))
                    self.__write_error_entity(entity_uuid, 'Flavor not found!')
                    return

            entity = KVMLibvirtEntity(entity_uuid, name, img.get('uuid'), flavor.get('uuid'))
            entity.set_user_file(kwargs.get('user-data'))
            entity.set_ssh_key(kwargs.get('ssh-key'))
            entity.set_networks(kwargs.get('networks'))
        else:
            self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Wrong parameters args:{} kwargs:{}'.format(args, kwargs))
            e = {'errors': 'wrong parameters to define_entity'}
            self.__update_actual_store(self.ERRORS, e)
            return

        entity.on_defined()
        self.current_entities.update({entity_uuid: entity})
        uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid)
        vm_info = json.loads(self.agent.dstore.get(uri))
        vm_info.update({'status': 'defined'})
        data = vm_info.get('entity_data')

        data.update({'flavor_id': flavor.get('uuid')})
        data.pop('cpu', None)
        data.pop('memory', None)
        data.pop('disk_size', None)
        data.update({'base_image': img.get('uuid')})

        vm_info.update({'entity_data': data})
        self.__update_actual_store_entity(entity_uuid, vm_info)
        self.agent.logger.info('define_entity()', '[ DONE ] KVM Plugin - VM Defined uuid: {}'.format(entity_uuid))
        return entity_uuid

    def undefine_entity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefine_entity()', ' KVM Plugin - Undefine a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefine_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))

        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefine_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if (self.current_entities.pop(entity_uuid, None)) is None:
                self.agent.logger.warning('undefine_entity()', 'KVM Plugin - pop from entities dict returned none')

            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)

            self.__pop_actual_store_entity(entity_uuid)
            self.agent.logger.info('undefine_entity()', '[ DONE ] KVM Plugin - Undefine a VM uuid {} '.format(entity_uuid))
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):
        '''
        :param entity_uuid:
        :param instance_uuid:
        :return:
        '''

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configure_entity()', ' KVM Plugin - Configure a VM uuid {} '.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configure_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configure_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:

            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print('This instance already existis!!')
            else:

                id = len(entity.instances)
                name = '{}{}'.format(entity.name, id)
                flavor = self.flavors.get(entity.flavor_id, None)
                img = self.images.get(entity.image_id, None)
                if flavor is None:
                    self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Cannot find flavor {}'.format(entity.flavor_id))
                    self.__write_error_instance(entity_uuid, instance_uuid, 'Flavor not found!')
                    return

                if img is None:
                    self.agent.logger.error('define_entity()', '[ ERRO ] KVM Plugin - Cannot find image {}'.format(entity.image_id))
                    self.__write_error_instance(entity_uuid, instance_uuid, 'Image not found!')
                    return

                disk_path = '{}.{}'.format(instance_uuid, img.get('format'))
                cdrom_path = '{}_config.iso'.format(instance_uuid)
                disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
                cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)

                # uuid, name, disk, cdrom, networks, user_file, ssh_key, entity_uuid, flavor_id, image_id):
                instance = KVMLibvirtEntityInstance(instance_uuid, name, disk_path, cdrom_path, entity.networks, entity.user_file,
                                                    entity.ssh_key, entity_uuid, flavor.get('uuid'), img.get('uuid'))

                ### vm networking TODO: add support for SR-IOV
                for i, n in enumerate(instance.networks):
                    if n.get('type') in ['wifi']:

                        nw_ifaces = self.agent.get_os_plugin().get_network_informations()
                        for iface in nw_ifaces:
                            if self.agent.get_os_plugin().get_intf_type(iface.get('intf_name')) == 'wireless' and iface.get('available') is True:
                                self.agent.get_os_plugin().set_interface_unaviable(iface.get('intf_name'))
                                n.update({'direct_intf': iface.get('intf_name')})
                        # TODO get available interface from os plugin
                    if n.get('network_uuid') is not None:
                        nws = self.agent.get_network_plugin(None).get(list(self.agent.get_network_plugin(None).keys())[0])
                        # print(nws.getNetworkInfo(n.get('network_uuid')))
                        br_name = nws.get_network_info(n.get('network_uuid')).get('virtual_device')
                        # print(br_name)
                        n.update({'br_name': br_name})
                    if n.get('intf_name') is None:
                        n.update({'intf_name': 'veth{0}'.format(i)})
                ######

                vm_xml = self.__generate_dom_xml(instance, flavor, img)

                vendor_conf = self.__generate_vendor_data(instance_uuid, entity_uuid, self.agent.get_os_plugin().get_uuid())
                vendor_filename = 'vendor_{}.yaml'.format(instance_uuid)
                self.agent.get_os_plugin().store_file(vendor_conf, self.BASE_DIR, vendor_filename)
                vendor_filename = os.path.join(self.BASE_DIR, vendor_filename)
                ### creating cloud-init initial drive TODO: check all the possibilities provided by OSM
                conf_cmd = '{} --hostname {} --uuid {} --vendor-data {}'.format(os.path.join(self.DIR, 'templates',
                                                                            'create_config_drive.sh'), entity.name, entity_uuid,
                                                                              vendor_filename)

                rm_temp_cmd = 'rm'
                if instance.user_file is not None and instance.user_file != '':
                    data_filename = 'userdata_{}'.format(entity_uuid)
                    self.agent.get_os_plugin().store_file(entity.user_file, self.BASE_DIR, data_filename)
                    data_filename = os.path.join(self.BASE_DIR, data_filename)
                    conf_cmd = conf_cmd + ' --user-data {}'.format(data_filename)
                if instance.ssh_key is not None and instance.ssh_key != '':
                    key_filename = 'key_{}.pub'.format(entity_uuid)
                    self.agent.get_os_plugin().store_file(instance.ssh_key, self.BASE_DIR, key_filename)
                    key_filename = os.path.join(self.BASE_DIR, key_filename)
                    conf_cmd = conf_cmd + ' --ssh-key {}'.format(key_filename)


                conf_cmd = conf_cmd + ' {}'.format(instance.cdrom)
                #############

                qemu_cmd = 'qemu-img create -f {} {} {}G'.format(img.get('format'), instance.disk, flavor.get('disk_size'))

                # As in the first example, but the output format will be qcow2 instead of a raw  disk:
                #
                # qemu-img create -f qcow2 -o preallocation=metadata newdisk.qcow2 15G
                # virt-resize --expand /dev/sda2 olddisk newdisk.qcow2

                dd_cmd = 'dd if={} of={}'.format(img.get('path'), instance.disk)

                self.agent.get_os_plugin().execute_command(qemu_cmd, True)
                self.agent.get_os_plugin().execute_command(conf_cmd, True)
                self.agent.get_os_plugin().execute_command(dd_cmd, True)

                if instance.ssh_key is not None and instance.ssh_key != '':
                    self.agent.get_os_plugin().remove_file(key_filename)
                if instance.user_file is not None and instance.user_file != '':
                    self.agent.get_os_plugin().remove_file(data_filename)

                try:
                    self.conn.defineXML(vm_xml)
                except libvirt.libvirtError as err:
                    self.conn = libvirt.open('qemu:///system')
                    self.conn.defineXML(vm_xml)

                instance.on_configured(vm_xml)
                entity.add_instance(instance)
                self.current_entities.update({entity_uuid: entity})

                uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid)
                vm_info = json.loads(self.agent.astore.get(uri))
                vm_info.update({'status': 'configured'})
                vm_info.update({'name': instance.name})
                data = vm_info.get('entity_data')
                data.update({'flavor_id': flavor.get('uuid')})
                data.update({'base_image': img.get('uuid')})
                vm_info.update({'entity_data': data})

                self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)

                self.agent.logger.info('configure_entity()', '[ DONE ] KVM Plugin - Configure a VM uuid {}'.format(instance_uuid))
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('clean_entity()', ' KVM Plugin - Clean a VM uuid {} '.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('clean_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('clean_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:

            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance not found!!')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                return
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance state is wrong, or transition not allowed')
                    self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance state transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state', 'Instance {} is not in CONFIGURED state'.format(instance_uuid))
                else:
                    dom = self.__lookup_by_uuid(instance_uuid)
                    if dom is not None:
                        dom.undefine()
                    else:
                        self.agent.logger.error('clean_entity()', 'KVM Plugin - Domain not found!!')
                        self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance KVM domain not found')

                    self.agent.get_os_plugin().remove_file(instance.cdrom)
                    self.agent.get_os_plugin().remove_file(instance.disk)
                    self.agent.get_os_plugin().remove_file(os.path.join(self.BASE_DIR, self.LOG_DIR, instance_uuid))

                    entity.remove_instance(instance)

                    self.current_entities.update({entity_uuid: entity})
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('clean_entity()', '[ DONE ] KVM Plugin - Clean a VM uuid {} '.format(entity_uuid))

                return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('run_entity()', 'KVM Plugin - Starting a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('run_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('run_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                return
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() == State.RUNNING:
                    self.agent.logger.error('run_entity()',
                                            'KVM Plugin - Instance already running')
                    return True
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state', 'Instance {} is not in CONFIGURED state'.format(instance_uuid))
                else:
                    dom = self.__lookup_by_uuid(instance_uuid)
                    dom.create()
                    while dom.state()[0] != 1:
                        pass

                    instance.on_start()
                    # log_filename = '{}/{}/{}_log.log'.format(self.BASE_DIR, self.LOG_DIR, instance_uuid)
                    # if instance.user_file is not None and instance.user_file != '':
                    #     self.__wait_boot(log_filename, True)
                    # else:
                    #     self.__wait_boot(log_filename)
                    #     self.__wait_boot(log_filename)

                    self.agent.logger.info('run_entity()', ' KVM Plugin - VM {} Started!'.format(instance))
                    uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                    vm_info = json.loads(self.agent.astore.get(uri))
                    vm_info.update({'status': 'run'})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)
                    self.current_entities.update({entity_uuid: entity})
                    self.agent.logger.info('run_entity()', '[ DONE ] KVM Plugin - Starting a VM uuid {}'.format(entity_uuid))
                    return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' KVM Plugin - Stop a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            self.agent.logger.error('stop_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
                return
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance state is wrong, or transition not allowed')
                    self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                    raise StateTransitionNotAllowedException('Instance is not in RUNNING state', 'Instance {} is not in RUNNING state'.format(instance_uuid))
                else:
                    dom = self.__lookup_by_uuid(instance_uuid)
                    dom.destroy()
                    while dom.state()[0] != 5:
                        pass
                    dom.undefine()
                    instance.on_stop()
                    self.current_entities.update({entity_uuid: entity})

                    uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                    vm_info = json.loads(self.agent.astore.get(uri))
                    vm_info.update({'status': 'stop'})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)
                    self.agent.logger.info('stop_entity()', '[ DONE ] KVM Plugin - Stop a VM uuid {}'.format(instance_uuid))

            return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('pause_entity()', ' KVM Plugin - Pause a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('pause_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('pause_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                return
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance state is wrong, or transition not allowed')
                    self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance state transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in RUNNING state', 'Instance {} is not in RUNNING state'.format(instance_uuid))
                else:
                    self.__lookup_by_uuid(instance_uuid).suspend()
                    instance.on_pause()
                    self.current_entities.update({entity_uuid: entity})
                    uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                    vm_info = json.loads(self.agent.astore.get(uri))
                    vm_info.update({'status': 'pause'})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)
                    self.agent.logger.info('pause_entity()', '[ DONE ] KVM Plugin - Pause a VM uuid {}'.format(instance_uuid))
                    return True

    def resume_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('resume_entity()', ' KVM Plugin - Resume a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('resume_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('resume_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                return
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.PAUSED:
                    self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance state is wrong, or transition not allowed')
                    self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance state transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in PAUSED state', 'Instance {} is not in PAUSED state'.format(entity_uuid))
                else:
                    self.__lookup_by_uuid(instance_uuid).resume()
                    instance_uuid.on_resume()
                    self.current_entities.update({entity_uuid: entity})
                    uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                    vm_info = json.loads(self.agent.dstore.get(uri))
                    vm_info.update({'status': 'run'})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)
                    self.agent.logger.info('resume_entity()', '[ DONE ] KVM Plugin - Resume a VM uuid {}'.format(instance_uuid))
                    return True

    # TODO rethink the migration workflow to be faster, copy the disk first and copy the base image only when migration ended
    def migrate_entity(self, entity_uuid, dst=False, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('migrate_entity()', ' KVM Plugin - Migrate a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None or entity.get_instance(instance_uuid) is None:

            '''
            How migration works:

            Issue the migration by writing on the store of source and destination the correct states and set dst with uuid for destination node:
                source: migrating | destination: migrating

            ## BEFORE MIGRATING

            The source node send to the destination node the flavor, the image and the entity

            When flavor and image are defined the destination node create the disks and change status to LANDING
            The source node change status to TAKING_OFF

            ## MIGRATING

            Actual migration using libvirt API

            Destination node wait the VM to be defined and active on KVM
            Source Node issue the migration from libvirt

            ## AFTER MIGRATING


            Source node destroy all information about entity instance (so the entity remains defined, and flavor and image remains in the node)

            Destination node update status in RUNNING


            '''
            if dst is True:

                self.agent.logger.info('migrate_entity()', ' KVM Plugin - I\'m the Destination Node')
                self.before_migrate_entity_actions(entity_uuid, True, instance_uuid)

                while True:  # wait for migration to be finished
                    dom = self.__lookup_by_uuid(instance_uuid)
                    if dom is None:
                        self.agent.logger.info('migrate_entity()', ' KVM Plugin - Domain not already in this host')
                    else:
                        if dom.isActive() == 1:
                            break
                        else:
                            self.agent.logger.info('migrate_entity()', ' KVM Plugin - Domain in this host but not running')
                    time.sleep(5)

                self.after_migrate_entity_actions(entity_uuid, True, instance_uuid)
                self.agent.logger.info('migrate_entity()', '[ DONE ] KVM Plugin - Migrate a VM uuid {}'.format(entity_uuid))
                return True

            else:
                self.agent.logger.error('migrate_entity()', 'KVM Plugin - Entity not exists')
                self.__write_error_entity(entity_uuid, 'Entity not exist')
                raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('migrate_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state', 'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() not in [State.RUNNING, State.TAKING_OFF]:
                self.agent.logger.error('clean_entity()', 'KVM Plugin - Instance state is wrong, or transition not allowed')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                raise StateTransitionNotAllowedException('Instance is not in RUNNING state', 'Instance {} is not in RUNNING state'.format(entity_uuid))

            self.agent.logger.info('migrate_entity()', ' KVM Plugin - I\'m the Source Node')
            res = self.before_migrate_entity_actions(entity_uuid, instance_uuid=instance_uuid)
            if not res:
                self.agent.logger.error('migrate_entity()', ' KVM Plugin - Error source node before migration, aborting')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance migration error on source')
                return

            #### MIGRATION

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
            # print(dst_node_info)
            dst_node_info = json.loads(dst_node_info)
            ## json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
            # dst_node_info = json.loads(self.agent.astore.get(uri)[0])
            ##
            dom = self.__lookup_by_uuid(instance_uuid)
            nw = dst_node_info.get('network')

            dst_hostname = dst_node_info.get('name')

            dst_ip = [x for x in nw if x.get('default_gw') is True]
            # TODO: or x.get('inft_configuration').get('ipv6_gateway') for ip_v6
            if len(dst_ip) == 0:
                return False

            dst_ip = dst_ip[0].get('inft_configuration').get('ipv4_address')  # TODO: as on search should use ipv6

            # ## ADDING TO /etc/hosts otherwise migration can fail
            self.agent.get_os_plugin().add_know_host(dst_hostname, dst_ip)
            ###

            # ## ACTUAL MIGRATIION ##################
            dst_host = 'qemu+ssh://{}/system'.format(dst_ip)
            dest_conn = libvirt.open(dst_host)
            if dest_conn is None:
                self.agent.logger.error('before_migrate_entity_actions()', 'KVM Plugin - Before Migration Source: Error on libvirt connection')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Source Error on libvirt connection')
                return
            flags = libvirt.VIR_MIGRATE_LIVE | libvirt.VIR_MIGRATE_PERSIST_DEST
            new_dom = dom.migrate(dest_conn, flags, name, None, 0)
            # new_dom = dom.migrate(dest_conn, libvirt.VIR_MIGRATE_LIVE and libvirt.VIR_MIGRATE_PERSIST_DEST and libvirt.VIR_MIGRATE_NON_SHARED_DISK, name, None, 0)
            if new_dom is None:
                self.agent.logger.error('before_migrate_entity_actions()', 'KVM Plugin - Before Migration Source: Migration failed')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Source Error Migration failed')
                return
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: Migration succeeds')
            dest_conn.close()
            # #######################################

            # ## REMOVING AFTER MIGRATION
            self.agent.get_os_plugin().remove_know_host(dst_hostname)
            instance.on_stop()
            self.current_entities.update({entity_uuid: entity})

            ####

            res = self.after_migrate_entity_actions(entity_uuid, instance_uuid=instance_uuid)
            if not res:
                self.agent.logger.error('migrate_entity()', ' KVM Plugin - Error source node after migration, aborting')
                return

    def before_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        if dst is True:

            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Destination: Create Domain and destination files')
            uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
            instance_info = json.loads(self.agent.dstore.get(uri))
            vm_info = instance_info.get('entity_data')

            # waiting flavor
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Waiting flavor')
            while True:
                flavor_id = vm_info.get('flavor_id')
                if flavor_id in self.flavors.keys():
                    break

            # waiting image
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Waiting image')
            while True:
                base_image = vm_info.get('base_image')
                if base_image in self.images.keys():
                    break

            # waiting entity
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Waiting entity')
            while True:
                if entity_uuid in self.current_entities.keys():
                    break
            self.agent.logger.info('before_migrate_entity_actions()', ' Entity {} defined!!!'.format(entity_uuid))

            # v = self.agent.astore.resolve('{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid))
            # print('>>>>>> V: {}'.format(v))

            img_info = self.images.get(base_image)
            flavor_info = self.flavors.get(flavor_id)
            entity = self.current_entities.get(entity_uuid)

            name = vm_info.get('name')
            disk_path = '{}.{}'.format(instance_uuid, img_info.get('format'))
            cdrom_path = '{}_config.iso'.format(instance_uuid)
            disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
            cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)

            instance = KVMLibvirtEntityInstance(instance_uuid, name, disk_path, cdrom_path, entity.networks, entity.user_file,
                                                entity.ssh_key, entity_uuid, flavor_info.get('uuid'), img_info.get('uuid'))

            instance.state = State.LANDING
            vm_info.update({'name': name})
            vm_xml = self.__generate_dom_xml(instance, flavor_info, img_info)

            instance.xml = vm_xml
            qemu_cmd = 'qemu-img create -f {} {} {}G'.format(img_info.get('format'), instance.disk, flavor_info.get('disk_size'))
            self.agent.get_os_plugin().execute_command(qemu_cmd, True)
            self.agent.get_os_plugin().create_file(instance.cdrom)
            self.agent.get_os_plugin().create_file(os.path.join(self.BASE_DIR, self.LOG_DIR, '{}_log.log'.format(instance_uuid)))

            conf_cmd = '{} --hostname {} --uuid {}'.format(os.path.join(self.DIR, 'templates',
                                                                        'create_config_drive.sh'), instance.name, instance_uuid)
            rm_temp_cmd = 'rm'
            if instance.user_file is not None and instance.user_file != '':
                data_filename = 'userdata_{}'.format(instance_uuid)
                self.agent.get_os_plugin().store_file(instance.user_file, self.BASE_DIR, data_filename)
                data_filename = os.path.join(self.BASE_DIR, data_filename)
                conf_cmd = conf_cmd + ' --user-data {}'.format(data_filename)
                # rm_temp_cmd = rm_temp_cmd + ' {}'.format(data_filename)
            if instance.ssh_key is not None and instance.ssh_key != '':
                key_filename = 'key_{}.pub'.format(instance_uuid)
                self.agent.get_os_plugin().store_file(instance.ssh_key, self.BASE_DIR, key_filename)
                key_filename = os.path.join(self.BASE_DIR, key_filename)
                conf_cmd = conf_cmd + ' --ssh-key {}'.format(key_filename)
                # rm_temp_cmd = rm_temp_cmd + ' {}'.format(key_filename)

            conf_cmd = conf_cmd + ' {}'.format(instance.cdrom)

            self.agent.get_os_plugin().execute_command(conf_cmd, True)

            instance_info.update({'entity_data': vm_info})
            instance_info.update({'status': 'landing'})

            entity.add_instance(instance)
            self.current_entities.update({entity_uuid: entity})

            self.__update_actual_store_instance(entity_uuid, instance_uuid, instance_info)

            return True
        else:
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: get information about destination node')

            entity = self.current_entities.get(entity_uuid, None)
            instance = entity.get_instance(instance_uuid)

            # reading entity info
            uri_entity = '{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid)
            entity_info = json.loads(self.agent.astore.get(uri_entity))
            entity_info.update({'status': 'define'})

            # reading instance info
            uri_instance = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
            instance_info = json.loads(self.agent.dstore.get(uri_instance))
            vm_info = instance_info.get('entity_data')
            # destination node uuid
            destination_node_uuid = instance_info.get('dst')

            # flavor and image information
            flavor_info = self.flavors.get(vm_info.get('flavor_id'))
            img_info = self.images.get(vm_info.get('base_image'))

            # getting same plugin in destination node
            uri = '{}/{}/plugins'.format(self.agent.aroot, destination_node_uuid)
            all_plugins = json.loads(self.agent.astore.get(uri)).get('plugins')  # TODO: solve this ASAP

            runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
            search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
            if len(search) == 0:
                self.agent.logger.error('before_migrate_entity_actions()', 'KVM Plugin - Before Migration Source: No KVM Plugin, Aborting!!!')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance Migration error')
                return False
            else:
                kvm_uuid = search[0].get('uuid')

            self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - check if flavor is present on destination')
            uri_flavor = '{}/{}/runtime/{}/flavor/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, flavor_info.get('uuid'))
            if self.agent.astore.get(uri_flavor) is None:
                self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - sending flavor to destination')
                uri_flavor = '{}/{}/runtime/{}/flavor/{}'.format(self.agent.droot, destination_node_uuid, kvm_uuid, flavor_info.get('uuid'))
                self.agent.dstore.put(uri_flavor, json.dumps(flavor_info))
            # wait to be defined flavor
            # self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - waiting flavor in destination')
            # while True:
            #     time.sleep(0.1)
            #     uri_flavor = '{}/{}/runtime/{}/flavor/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, flavor_info.get('uuid'))
            #     f_i = self.agent.astore.get(uri_flavor)
            #     print('{}'.format(f_i))
            #     if f_i is not None:
            #         self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - Flavor in destination!')
            #         break

            self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - check if image is present on destination')
            uri_img = '{}/{}/runtime/{}/image/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, img_info.get('uuid'))
            if self.agent.astore.get(uri_img) is None:
                self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - sending image to destination')
                uri_img = '{}/{}/runtime/{}/image/{}'.format(self.agent.droot, destination_node_uuid, kvm_uuid, img_info.get('uuid'))
                self.agent.dstore.put(uri_img, json.dumps(img_info))

            # wait to be defined image
            # self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - Waiting image in destination')
            # while True:
            #     time.sleep(0.1)
            #     uri_img = '{}/{}/runtime/{}/image/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, img_info.get('uuid'))
            #     i_i = self.agent.astore.get(uri_img)
            #     if i_i is not None:
            #         self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - Image in destination!')
            #         break

            # send entity definition

            # uri = '{}/{}/runtime/{}/entity/*'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, entity_uuid, instance_uuid)
            # self.agent.astore.observe(uri, self.dummy_observer)
            # import colorama
            # colorama.init()
            # print(colorama.Fore.RED + '>>>>>> Registered observer for {} <<<<<<< '.format(uri) + colorama.Style.RESET_ALL)

            self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - check if image is present on destination')
            uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, entity_uuid)
            if self.agent.astore.get(uri_entity) is None:
                self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - sending entity to destination')
                uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.droot, destination_node_uuid, kvm_uuid, entity_uuid)
                self.agent.dstore.put(uri_entity, json.dumps(entity_info))
                self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - Waiting entity in destination')
                while True:
                    uri_entity = '{}/{}/runtime/{}/entity/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, entity_uuid)
                    jdata = self.agent.astore.get(uri_entity)
                    # print('{}'.format(jdata))
                    if jdata is not None:
                        self.agent.logger.info('before_migrate_entity_actions()', 'KVM Plugin - Entity in destination!')
                        entity_info = json.loads(jdata)
                        if entity_info is not None and entity_info.get('status') == 'defined':
                            break

            # waiting for destination node to be ready
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: Waiting destination to be ready')
            while True:
                # self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: Waiting destination to be ready')
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.agent.aroot, destination_node_uuid, kvm_uuid, entity_uuid, instance_uuid)
                vm_info = self.agent.astore.get(uri)
                if vm_info is not None:
                    vm_info = json.loads(vm_info)
                    if vm_info is not None and vm_info.get('status') == 'landing':
                        break
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: Destination is ready!')

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
            self.agent.logger.error('after_migrate_entity_actions()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            raise EntityNotExistingException('Enitity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('after_migrate_entity_actions()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            self.__write_error_entity(entity_uuid, 'Entity state transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in correct state', 'Entity {} is not in correct state'.format(entity.get_state()))
        else:
            if dst is True:

                instance = entity.get_instance(instance_uuid)
                '''
                Here the plugin also update to the current status, and remove unused keys
                '''
                self.agent.logger.info('after_migrate_entity_actions()', ' KVM Plugin - After Migration Destination: Updating state')
                instance.on_start()
                self.current_entities.update({entity_uuid: entity})

                uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
                vm_info = json.loads(self.agent.dstore.get(uri))
                vm_info.pop('dst')
                vm_info.update({'status': 'run'})

                self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)
                self.current_entities.update({entity_uuid: entity})

                return True
            else:
                '''
                Source node destroys all information about vm
                '''
                self.agent.logger.info('after_migrate_entity_actions()', ' KVM Plugin - After Migration Source: Updating state, destroy vm')
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
                return True

    def __add_image(self, manifest):
        url = manifest.get('base_image')
        if url.startswith('http'):
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, url.split('/')[-1])
            self.agent.get_os_plugin().download_file(url, image_name)
        elif url.startswith('file://'):
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, url.split('/')[-1])
            cmd = 'cp {} {}'.format(url[len('file://'):], image_name)
            self.agent.get_os_plugin().execute_command(cmd, True)
        manifest.update({'path': image_name})
        uri = '{}/{}'.format(self.HOME_IMAGE, manifest.get('uuid'))
        self.__update_actual_store(uri, manifest)
        self.images.update({manifest.get('uuid'): manifest})

    def __remove_image(self, image_uuid):
        image = self.images.get(image_uuid, None)
        if image is None:
            self.agent.logger.info('__remove_image()', ' KVM Plugin - Image not found!!')
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

    def __react_to_cache_image(self, uri, value, v):
        self.agent.logger.info('__react_to_cache_image()', 'KVM Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'image':
            image_uuid = uri.split('/')[-1]
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache_image()', 'KVM Plugin - This is a remove for URI: {}'.format(uri))
                self.__remove_image(image_uuid)
            else:
                value = json.loads(value)
                self.__add_image(value)

    def __react_to_cache_flavor(self, uri, value, v):
        self.agent.logger.info('__react_to_cache_flavor()', 'KVM Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'flavor':
            flavor_uuid = uri.split('/')[-1]
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache_flavor()', 'KVM Plugin - This is a remove for URI: {}'.format(uri))
                self.__remove_flavor(flavor_uuid)
            else:
                value = json.loads(value)
                self.__add_flavor(value)

    def __react_to_cache_entity(self, uri, value, v):
        self.agent.logger.info('__react_to_cache_entity()', 'KVM Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'entity':
            uuid = uri.split('/')[-1]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            # print(type(entity_data))
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
            react_func = self.__react(action)
            if action == 'clean':
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
            elif react_func is not None and entity_data is None:
                react_func(entity_uuid, instance_uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': entity_uuid})
                if action in ['landing', 'taking_off']:
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
        try:
            domains = self.conn.listAllDomains(0)
        except libvirt.libvirtError as err:
            self.conn = libvirt.open('qemu:///system')
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

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' KVM Plugin - Stop a VM uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'KVM Plugin - Entity not exists')
            self.__write_error_entity(entity_uuid, 'Entity not exist')
            # raise EntityNotExistingException('Entity not existing', 'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
                self.__write_error_instance(entity_uuid, instance_uuid, 'Entity Instance not exist')
                return
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() == State.PAUSED:
                    self.resume_entity(entity_uuid, instance_uuid)
                    self.stop_entity(entity_uuid, instance_uuid)
                    self.clean_entity(entity_uuid, instance_uuid)
                if instance.get_state() == State.RUNNING:
                    self.stop_entity(entity_uuid, instance_uuid)
                    self.clean_entity(entity_uuid, instance_uuid)
                if instance.get_state() == State.CONFIGURED:
                    self.clean_entity(entity_uuid, instance_uuid)

    def __generate_dom_xml(self, instance, flavor, image):
        template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'vm.xml'))
        vm_xml = Environment().from_string(template_xml)
        vm_xml = vm_xml.render(name=instance.name, uuid=instance.uuid, memory=flavor.get('memory'),
                               cpu=flavor.get('cpu'), disk_image=instance.disk,
                               iso_image=instance.cdrom, networks=instance.networks, format=image.get('format'))
        return vm_xml

    def __generate_vendor_data(self, instanceid, entityid, nodeid):
        vendor_yaml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'vendor_data.yaml'))
        vendor_conf = Environment().from_string(vendor_yaml)
        vendor_conf = vendor_conf.render(instanceid=instanceid, nodeid=nodeid, entityid=entityid)
        return vendor_conf

    def __update_actual_store(self, uri, value):
        uri = '{}/{}'.format(self.agent.ahome, uri)
        # self.agent.logger.error('__update_actual_store()', 'Updating Key: {} Value: {}'.format(uri, value))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri):
        self.agent.logger.info('__pop_actual_store()', 'Removing Key: {}'.format(uri))
        uri = '{}/{}'.format(self.agent.ahome, uri)
        self.agent.astore.remove(uri)

    def __update_actual_store_entity(self, uri, value):
        uri = '{}/{}'.format(self.HOME_ENTITY, uri)
        # value = json.dumps(value)
        self.__update_actual_store(uri, value)
        # self.agent.astore.put(uri, value)

    def __update_actual_store_instance(self, entity_uuid, instance_uuid, value):
        uri = '{}/{}/{}/{}'.format(self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
        # value = json.dumps(value)
        # self.agent.astore.put(uri, value)
        self.__update_actual_store(uri, value)

    def __pop_actual_store_entity(self, entity_uuid):
        uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid)
        self.agent.astore.remove(uri)

    def __pop_actual_store_instance(self, entity_uuid, instance_uuid):
        uri = '{}/{}/{}/{}/{}'.format(self.agent.ahome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
        self.agent.astore.remove(uri)

    def __netmask_to_cidr(self, netmask):
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])

    def __write_error_entity(self, entity_uuid, error):
        uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid)
        jdata = self.agent.dstore.get(uri)
        if jdata is not None:
            vm_info = json.loads(jdata)
        else:
            vm_info = {}

        vm_info.update({'status': 'error'})
        vm_info.update({'error': error})
        self.__update_actual_store_entity(entity_uuid, vm_info)

    def __write_error_instance(self, entity_uuid, instance_uuid, error):
        uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME_ENTITY, entity_uuid, self.INSTANCE, instance_uuid)
        jdata = self.agent.dstore.get(uri)
        if jdata is not None:
            vm_info = json.loads(jdata)
        else:
            vm_info = {}
        vm_info.update({'status': 'error'})
        vm_info.update({'error': error})
        self.__update_actual_store_instance(entity_uuid, instance_uuid, vm_info)

    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'stop': self.stop_entity,
            'pause': self.pause_entity,
            'resume': self.resume_entity,
            'run': self.run_entity,
            'landing': self.migrate_entity,
            'taking_off': self.migrate_entity
        }

        return r.get(action, None)

    def dummy_observer(self, key, value, version):
        import colorama
        colorama.init()
        print(colorama.Fore.GREEN + '>>>>>>>>>>>>>>>>>>>>> Updated K:{} Va:{} Ve:{} <<<<<<<<<<<<<<<<<<<< '.format(key, value, version) + colorama.Style.RESET_ALL)
