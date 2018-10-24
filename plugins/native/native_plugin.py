
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
import psutil
import json
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from NativeEntity import NativeEntity
from NativeEntityInstance import NativeEntityInstance
from jinja2 import Environment
import time


class Native(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):

        super(Native, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.operating_system = self.agent.get_os_plugin().name
        self.agent.logger.info('__init__()', ' Hello from Native Plugin - Running on {}'.format(self.operating_system))
        self.HOME = 'runtime/{}/entity'.format(self.uuid)
        self.INSTANCE = 'instance'
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.BASE_DIR = os.path.join(self.agent.base_path, 'native')
        self.LOG_DIR = 'logs'
        self.STORE_DIR = 'apps'

        self.start_runtime()

    def start_runtime(self):

        uri = '{}/{}/**'.format(self.agent.dhome, self.HOME)
        self.agent.logger.info('startRuntime()', ' Native Plugin - Observing {}'.format(uri))
        self.agent.dstore.observe(uri, self.__react_to_cache)

        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.STORE_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.STORE_DIR))
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.LOG_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR))
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.STORE_DIR))
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.LOG_DIR))

        return self.uuid

    def stop_runtime(self):
        self.agent.logger.info('stopRuntime()', ' Native Plugin - Destroy running BE')
        for k in list(self.current_entities.keys()):
            entity = self.current_entities.get(k)
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(k, i)
            # if entity.get_state() == State.PAUSED:
            #     self.resume_entity(k)
            #     self.stop_entity(k)
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            # if entity.get_state() == State.RUNNING:
            #     self.stop_entity(k)
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            # if entity.get_state() == State.CONFIGURED:
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            if entity.get_state() == State.DEFINED:
                self.undefine_entity(k)
        self.agent.logger.info('stopRuntime()', '[ DONE ] Native Plugin - Bye')
        return True

    def define_entity(self, *args, **kwargs):

        if len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            out_file = 'native_{}.log'.format(entity_uuid)
            out_file = os.path.join(self.BASE_DIR, self.LOG_DIR, out_file)
            entity = NativeEntity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('source'),
                                  kwargs.get('args'), out_file)
        else:
            return None

        self.agent.logger.info('defineEntity()', ' Native Plugin - Define BE')

        if entity.source_url is not None and entity.source_url.startswith('http'):
            zip_name = entity.source_url.split('/')[-1]
            zip_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, zip_name)
            dest = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid)
            # entity.source = os.path.join(dest,entity.command)

            if self.operating_system.lower() == 'linux':
                if zip_name.endswith('.tar.gz'):
                    unzip_cmd = 'tar -zxvf {} -C {}'.format(zip_file, dest)
                else:
                    unzip_cmd = 'unzip {} -d {}'.format(zip_file, dest)
            elif self.operating_system.lower() == 'windows':
                unzip_cmd = 'Expand-Archive -Path {} -DestinationPath {}'.format(zip_file, dest)
            else:
                unzip_cmd = ''

            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid))
            self.agent.get_os_plugin().download_file(entity.source_url,
                                                     os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, zip_name))
            # self.agent.getOSPlugin().executeCommand(wget_cmd, True)
            self.agent.get_os_plugin().execute_command(unzip_cmd, blocking=True, external=True)
            entity.source = dest
        else:
            entity.source = None

        entity.set_state(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME, entity_uuid)
        na_info = json.loads(self.agent.dstore.get(uri))
        na_info.update({'status': 'defined'})
        self.__update_actual_store(entity_uuid, na_info)
        self.agent.logger.info('defineEntity()', ' Native Plugin - Defined BE uuid {}'.format(entity_uuid))
        return entity_uuid

    def undefine_entity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' Native Plugin - Undefine BE uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)
            self.agent.get_os_plugin().remove_dir(os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid))
            self.current_entities.pop(entity_uuid, None)
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] Native Plugin - Undefine BE uuid {}'.format(entity_uuid))
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' Native Plugin - Configure BE uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print('This instance already existis!!')
            else:
                id = len(entity.instances)
                name = '{0}{1}'.format(entity.name, id)
                out_file = 'native_{}_{}.log'.format(entity_uuid, instance_uuid)
                out_file = os.path.join(self.BASE_DIR, self.LOG_DIR, out_file)

                # uuid, name, command, source, args, outfile, entity_uuid)
                instance = NativeEntityInstance(instance_uuid, name, entity.command, entity.source,
                                                entity.args, out_file, entity_uuid)
                native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                self.agent.get_os_plugin().create_file(instance.outfile)
                self.agent.get_os_plugin().create_dir(native_dir)

                # if entity.source is not None:
                #     zip_name = entity.source.split('/')[-1]
                #     self.agent.getOSPlugin().createDir(os.path.join(self.BASE_DIR, self.STORE_DIR, entity.name))
                #     #wget_cmd = str('wget {} -O {}/{}/{}/{}' %
                #     #               (entity.source, self.BASE_DIR, self.STORE_DIR, entity.name, zip_name))
                #
                #     zip_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity.name, zip_name)
                #     dest = os.path.join(self.BASE_DIR, self.STORE_DIR, entity.name)
                #
                #     if self.operating_system == 'linux':
                #         unzip_cmd = str('unzip {} -d {}' % (zip_file, dest))
                #     elif self.operating_system == 'windows':
                #         unzip_cmd = str('Expand-Archive -Path {} -DestinationPath {}' % (zip_file, dest))
                #     else:
                #         unzip_cmd = ''
                #
                #     self.agent.getOSPlugin().downloadFile(entity.image,
                #                                           os.path.join(self.BASE_DIR, self.STORE_DIR, zip_name))
                #     # self.agent.getOSPlugin().executeCommand(wget_cmd, True)
                #     self.agent.getOSPlugin().executeCommand(unzip_cmd, True)

                instance.on_configured()
                entity.add_instance(instance)
                self.current_entities.update({entity_uuid: entity})
                uri = '{}/{}/{}'.format(self.agent.dhome, self.HOME, entity_uuid)
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({'status': 'configured'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('configureEntity()', '[ DONE ] Native Plugin - Configure BE uuid {}'.format(instance_uuid))
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('cleanEntity()', ' Native Plugin - Clean BE uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('cleanEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('cleanEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()', 'Native Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance is None:
                    self.agent.logger.error('clean_entity()',
                                            'Instance {} not existing'.format(instance_uuid))
                    return False
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                            'has_instance Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state',
                                                             'Instance {} is not in CONFIGURED state'.format(instance_uuid))
                else:

                    self.agent.get_os_plugin().remove_file(instance.outfile)
                    native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                    self.agent.get_os_plugin().remove_dir(native_dir)

                    # if entity.source is not None:
                    #    entity_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, instance.name)
                    #    self.agent.getOSPlugin().removeDir(entity_dir)
                    instance.on_clean()
                    entity.remove_instance(instance)
                    self.current_entities.update({entity_uuid: entity})

                    # uri = str('{}/{}/{}' % (self.agent.dhome, self.HOME, entity_uuid))
                    # na_info = json.loads(self.agent.dstore.get(uri))
                    # na_info.update({'status': 'cleaned'})
                    # self.__update_actual_store(entity_uuid, na_info)
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('cleanEntity()', '[ DONE ] Native Plugin - Clean BE uuid {}'.format(instance_uuid))
                    return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('runEntity()', ' Native Plugin - Starting BE uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('runEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('runEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance is None:
                self.agent.logger.error('clean_entity()',
                                        'Instance {} not existing'.format(instance_uuid))
                return False
            if instance.get_state() == State.RUNNING:
                self.agent.logger.error('run_entity()',
                                        'Native Plugin - Instance already running')
                return True
            if instance.get_state() != State.CONFIGURED:
                self.agent.logger.error('run_entity()',
                                        'Native Plugin - Instance state is wrong, or transition not allowed - State: {}'.format(instance.get_state()))
                raise StateTransitionNotAllowedException('Instance is not in CONFIGURED state',
                                                         'Instance {} is not in CONFIGURED state'.format(instance_uuid))
            else:

                if instance.source is not None:

                    native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)

                    source_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid)

                    pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                    run_script = self.__generate_run_script(instance.command, instance.args, source_dir, pid_file)
                    if self.operating_system.lower() == 'linux':
                        self.agent.get_os_plugin().store_file(run_script, native_dir, '{}_run.sh'.format(instance_uuid))
                        chmod_cmd = 'chmod +x {}'.format(os.path.join(native_dir, '{}_run.sh'.format(instance_uuid)))
                        self.agent.get_os_plugin().execute_command(chmod_cmd, True)
                        cmd = '{}'.format(os.path.join(native_dir, '{}_run.sh'.format(instance_uuid)))
                    elif self.operating_system.lower() == 'windows':
                        self.agent.get_os_plugin().store_file(run_script, native_dir, '{}_run.ps1'.format(instance_uuid))
                        cmd = '{}'.format(os.path.join(native_dir, '{}_run.ps1'.format(instance_uuid)))
                    else:
                        cmd = ''

                    process = self.__execute_command(cmd, instance.outfile)

                    time.sleep(1)
                    pid_file = '{}.pid'.format(instance_uuid)
                    pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, pid_file)
                    pid = int(self.agent.get_os_plugin().read_file(pid_file))
                    instance.on_start(pid, process)
                else:
                    # try to inject the pid file if script use {{pid_file}}
                    '''

                    This make possible to add on the launch file of you native application that fog05 can inject the pid output file
                    in this way is possible to fog05 to correct send signal to your application, in the case the {{pid_file}} is not defined the script
                    will not be modified

                    '''
                    if self.operating_system.lower() == 'linux':
                        native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                        pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                        template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_unix2.sh'))
                        na_script = Environment().from_string(template_xml)
                        cmd = '{} {}'.format(entity.command, ' '.join(entity.args))
                        na_script = na_script.render(command=cmd, outfile=pid_file)
                        self.agent.get_os_plugin().store_file(na_script, native_dir, '{}_run.sh'.format(instance_uuid))
                        chmod_cmd = 'chmod +x {}'.format(os.path.join(native_dir, '{}_run.sh'.format(instance_uuid)))
                        self.agent.get_os_plugin().execute_command(chmod_cmd, True)
                        cmd = '{}'.format(os.path.join(native_dir, '{}_run.sh'.format(instance_uuid)))
                        # if instance.command.endswith('.sh'):
                        #     command = self.agent.get_os_plugin().read_file(instance.command)
                        #     pid_file = '{}_{}.pid'.format(os.path.join(self.BASE_DIR, entity_uuid), instance_uuid)
                        #     run_script = self.__generate_run_script(instance.command, instance.args, None, pid_file)
                        #     f_name = '{}_{}.sh'.format(entity_uuid, instance_uuid)
                        #     f_path = self.BASE_DIR
                        #     self.agent.get_os_plugin().store_file(run_script, f_path, f_name)
                        #     cmd = '{} {}'.format('{}_{}.sh'.format(os.path.join(self.BASE_DIR, entity_uuid), instance_uuid), ''.join(entity.args))
                        #     f_path = os.path.join(f_path, f_name)
                        #     self.agent.get_os_plugin().execute_command('chmod +x {}'.format(f_path))
                        # else:
                        #     native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                        #     pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                        #     template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_unix2.sh'))
                        #     na_script = Environment().from_string(template_xml)
                        #     cmd = '{} {}'.format(entity.command, ' '.join(entity.args))
                        #     na_script = na_script.render(command=cmd, outfile=pid_file)
                        #     self.agent.get_os_plugin().store_file(na_script, native_dir, '{}_run.sh'.format(instance_uuid))
                        #     chmod_cmd = 'chmod +x {}'.format(os.path.join(native_dir, '{}_run.sh'.format(instance_uuid)))
                        #     self.agent.get_os_plugin().execute_command(chmod_cmd, True)
                        #     cmd = '{}'.format(os.path.join(native_dir, '{}_run.sh'.format(instance_uuid)))
                    elif self.operating_system.lower() == 'windows':

                        native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                        pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                        run_script = self.__generate_run_script(instance.command, instance.args, None, pid_file)
                        self.agent.logger.info('runEntity()', '[ INFO ] PowerShell script is {}'.format(run_script))
                        self.agent.get_os_plugin().store_file(run_script, native_dir, '{}_run.ps1'.format(instance_uuid))
                        cmd = '{}'.format(os.path.join(native_dir, '{}_run.ps1'.format(instance_uuid)))

                    self.agent.logger.info('runEntity()', 'Command is {}'.format(cmd))

                    process = self.__execute_command(cmd, instance.outfile)
                    instance.on_start(process.pid, process)

                entity.add_instance(instance)
                self.current_entities.update({entity_uuid: entity})
                uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({'status': 'run'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('runEntity()', '[ DONE ] Native Plugin - Running BE uuid {}'.format(instance_uuid))
                return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stopEntity()', ' Native Plugin - Stop BE uuid {}'.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stopEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException('Enitity not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('stopEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException('Entity is not in DEFINED state',
                                                     'Entity {} is not in DEFINED state'.format(entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.RUNNING:
                self.agent.logger.error('clean_entity()',
                                        'Native Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException('Instance is not in RUNNING state',
                                                         'Instance {} is not in RUNNING state'.format(instance_uuid))
            else:
                p = instance.process
                p.terminate()
                os.system("sudo kill -15 {}".format(p.pid))
                self.agent.logger.info('stopEntity()', 'Sended sigterm - Sleep 3 seconds')
                self.agent.logger.info('stopEntity()', 'sigterm - sudo kill -15 {}'.format(p.pid))

                cmd = '{} {}'.format(entity.command, ' '.join(str(x) for x in entity.args))
                time.sleep(3)
                if instance.source is None and p.is_running():
                    pid_file = '{}.pid'.format(os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid))
                    pid = int(self.agent.get_os_plugin().read_file(pid_file))
                    self.agent.logger.info('stopEntity()', 'FILE PID: {}'.format(pid))
                    #pid = instance.pid
                    pid = p.pid
                    self.agent.logger.info('stopEntity()', 'Instance source is none')
                    self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                    self.agent.logger.info('stopEntity()', 'Still Alive - Sending sigint - Sleep 2 seconds')
                    self.agent.logger.info('stopEntity()', 'sigterm - sudo kill -2 {}'.format(p.pid))
                    p.send_signal(2)
                    os.system("sudo kill -2 {}".format(p.pid))
                    f_name = '{}_{}.pid'.format(entity_uuid, instance_uuid)
                    f_path = self.BASE_DIR
                    time.sleep(2)
                    if p.is_running():
                        self.agent.logger.info('stopEntity()', 'Still Alive!!!!! - Sending sigkill')
                        p.kill()
                        os.system("sudo kill -9 {}".format(p.pid))
                        self.agent.logger.info('stopEntity()', 'sigterm - sudo kill -9 {}'.format(p.pid))

                    pid_file = os.path.join(f_path, f_name)
                    self.agent.logger.info('stopEntity()', 'Check if PID file exists {}'.format(pid_file))
                    if self.agent.get_os_plugin().file_exists(pid_file):
                        pid = int(self.agent.get_os_plugin().read_file(pid_file))
                        self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                        self.agent.get_os_plugin().execute_command('sudo pkill -9 -P {}'.format(pid))
                        if self.agent.get_os_plugin().check_if_pid_exists(pid):
                            self.agent.get_os_plugin().send_sig_int(pid)
                            time.sleep(3)
                        if self.agent.get_os_plugin().check_if_pid_exists(pid):
                            self.agent.get_os_plugin().send_sig_kill(pid)

                    pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, '{}.pid'.format(instance_uuid))
                    self.agent.logger.info('stopEntity()', 'Check if PID file exists {}'.format(pid_file))
                    if self.agent.get_os_plugin().file_exists(pid_file):
                        pid = int(self.agent.get_os_plugin().read_file(pid_file))
                        self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                        self.agent.get_os_plugin().execute_command('sudo pkill -9 -P {}'.format(pid))
                        if self.agent.get_os_plugin().check_if_pid_exists(pid):
                            self.agent.get_os_plugin().send_sig_int(pid)
                            time.sleep(3)
                        if self.agent.get_os_plugin().check_if_pid_exists(pid):
                            self.agent.get_os_plugin().send_sig_kill(pid)

                else:
                    self.agent.logger.info('stopEntity()', 'Instance source is not none')
                    pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, '{}.pid'.format(instance_uuid))
                    pid = int(self.agent.get_os_plugin().read_file(pid_file))
                    if self.operating_system.lower == 'linux':
                        self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                        self.agent.get_os_plugin().execute_command('sudo pkill -9 -P {}'.format(pid))
                    if self.agent.get_os_plugin().check_if_pid_exists(pid):
                        self.agent.get_os_plugin().send_sig_int(pid)
                        time.sleep(3)
                    if self.agent.get_os_plugin().check_if_pid_exists(pid):
                        self.agent.get_os_plugin().send_sig_kill(pid)

                instance.on_stop()
                self.current_entities.update({entity_uuid: entity})
                uri = '{}/{}/{}/{}/{}'.format(self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid)
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({'status': 'stop'})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('stopEntity()', '[ DONE ] Native Plugin - Stopped BE uuid {}'.format(instance_uuid))
                return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        self.agent.logger.warning('pauseEntity()', 'Native Plugin - Cannot pause a BE')
        return False

    def resume_entity(self, entity_uuid, instance_uuid=None):
        self.agent.logger.warning('resumeEntity()', 'Native Plugin - Cannot resume a BE')
        return False

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

    def __execute_command(self, command, out_file):
        f = open(out_file, 'w')
        if self.operating_system.lower() == 'windows':
            p = psutil.Popen(['PowerShell', '-File', command], shell=True, stdout=f, stderr=f)
        else:
            # cmd = 'sh -c {}'.format(command)
            cmd_splitted = command.split()
            self.agent.logger.info('__execute_command()', 'CMD SPLIT = {}'.format(cmd_splitted))
            p = psutil.Popen(cmd_splitted, shell=False, stdout=f, stderr=f)
        return p

    def __generate_run_script(self, cmd, args, directory, outfile):
        if self.operating_system.lower() == 'windows':
            if len(args) == 0:
                self.agent.logger.info('__generate_run_script()', ' Native Plugin - Generating run script for Windows')
                template_script = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_windows.ps1'))
                na_script = Environment().from_string(template_script)
                if directory:
                    cmd = os.path.join(directory,cmd)
                na_script = na_script.render(command=cmd, outfile=outfile)
            else:
                args = json.dumps(args)[1:-1]
                template_script = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_windows_args.ps1'))
                na_script = Environment().from_string(template_script)
                if directory:
                    cmd = os.path.join(directory, cmd)
                na_script = na_script.render(command=cmd,args_list=args, outfile=outfile)

        else:
            self.agent.logger.info('__generate_run_script()', ' Native Plugin - Generating run script for Linux')
            template_script = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_unix.sh'))
            na_script = Environment().from_string(template_script)
            if directory:
                cmd = os.path.join(directory, cmd)
            if len(args)>0:
                cmd = cmd + ' {}'.format(' '.join(args))
            na_script = na_script.render(command=cmd, outfile=outfile)


        self.agent.logger.info('__generate_run_script()', 'Script is {}'.format(na_script))
        return na_script

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' Native Plugin - React to to URI: {} Value: {} Version: {}'.format(uri, value, v))
        if uri.split('/')[-2] == 'entity':
            uuid = uri.split('/')[-1]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            react_func = self.__react(action)
            if action == 'undefine':
                self.agent.logger.info('__react_to_cache()', ' Native Plugin - This is a remove for URI: {}'.format(uri))
                self.undefine_entity(uuid)
            elif react_func is not None and entity_data is None:
                react_func(uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': uuid})
                if action == 'define':
                    react_func(**entity_data)
                else:
                    react_func(entity_data)
        elif uri.split('/')[-2] == 'instance':
            instance_uuid = uri.split('/')[-1]
            entity_uuid = uri.split('/')[-3]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            # print(type(entity_data))
            react_func = self.__react(action)
            if action == 'clean':
                self.agent.logger.info('__react_to_cache()', ' Native Plugin - This is a remove for URI: {}'.format(uri))
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
            elif react_func is not None and entity_data is None:
                react_func(entity_uuid, instance_uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': entity_uuid})

    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'stop': self.stop_entity,
            'resume': self.resume_entity,
            'run': self.run_entity
        }

        return r.get(action, None)

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('__force_entity_instance_termination()', ' Native Plugin - Stop a BE uuid {} '.format(entity_uuid))
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('__force_entity_instance_termination()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException('Native not existing',
                                             'Entity {} not in runtime {}'.format(entity_uuid, self.uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('__force_entity_instance_termination()', 'Native Plugin - Instance not found!!')
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






