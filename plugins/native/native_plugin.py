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
        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.INSTANCE = "instance"
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.BASE_DIR = os.path.join(self.agent.base_path, 'native')
        self.LOG_DIR = "logs"
        self.STORE_DIR = "apps"

        self.start_runtime()

    def start_runtime(self):

        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('startRuntime()', ' Native Plugin - Observing %s' % uri)
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
            out_file = str("native_%s.log" % entity_uuid)
            out_file = os.path.join(self.BASE_DIR, self.LOG_DIR, out_file)
            entity = NativeEntity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('source'),
                                  kwargs.get('args'), out_file)
        else:
            return None

        self.agent.logger.info('defineEntity()', ' Native Plugin - Define BE')

        if entity.source_url is not None and entity.source_url.startswith("http"):
            zip_name = entity.source_url.split('/')[-1]
            zip_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, zip_name)
            dest = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid)
            # entity.source = os.path.join(dest,entity.command)

            if self.operating_system.lower() == 'linux':
                if zip_name.endswith('.tar.gz'):
                    unzip_cmd = 'tar -zxvf {} -C {}'.format(zip_file, dest)
                else:
                    unzip_cmd = str("unzip %s -d %s" % (zip_file, dest))
            elif self.operating_system.lower() == 'windows':
                unzip_cmd = str('Expand-Archive -Path %s -DestinationPath %s' % (zip_file, dest))
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
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        na_info = json.loads(self.agent.dstore.get(uri))
        na_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, na_info)
        self.agent.logger.info('defineEntity()', ' Native Plugin - Defined BE uuid %s' % entity_uuid)
        return entity_uuid

    def undefine_entity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' Native Plugin - Undefine BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)
            self.agent.get_os_plugin().remove_dir(os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid))
            self.current_entities.pop(entity_uuid, None)
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] Native Plugin - Undefine BE uuid %s' % entity_uuid)
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' Native Plugin - Configure BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print("This instance already existis!!")
            else:
                id = len(entity.instances)
                name = '{0}{1}'.format(entity.name, id)
                out_file = str("native_%s_%s.log" % (entity_uuid, instance_uuid))
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
                #     #wget_cmd = str('wget %s -O %s/%s/%s/%s' %
                #     #               (entity.source, self.BASE_DIR, self.STORE_DIR, entity.name, zip_name))
                #
                #     zip_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity.name, zip_name)
                #     dest = os.path.join(self.BASE_DIR, self.STORE_DIR, entity.name)
                #
                #     if self.operating_system == 'linux':
                #         unzip_cmd = str("unzip %s -d %s" % (zip_file, dest))
                #     elif self.operating_system == 'windows':
                #         unzip_cmd = str('Expand-Archive -Path %s -DestinationPath %s' % (zip_file, dest))
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
                uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({"status": "configured"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('configureEntity()', '[ DONE ] Native Plugin - Configure BE uuid %s' % instance_uuid)
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('cleanEntity()', ' Native Plugin - Clean BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('cleanEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('cleanEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()', 'Native Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                            'has_instance Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                             str("Instance %s is not in CONFIGURED state" % instance_uuid))
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

                    # uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                    # na_info = json.loads(self.agent.dstore.get(uri))
                    # na_info.update({"status": "cleaned"})
                    # self.__update_actual_store(entity_uuid, na_info)
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('cleanEntity()', '[ DONE ] Native Plugin - Clean BE uuid %s' % instance_uuid)
                    return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('runEntity()', ' Native Plugin - Starting BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('runEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('runEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
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

                if instance.source is None:
                    cmd = "{} {}".format(entity.command, ' '.join(str(x) for x in entity.args))
                else:

                    native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)

                    source_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid)

                    pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                    run_script = self.__generate_run_script(instance.command, source_dir, pid_file)
                    if self.operating_system.lower() == 'linux':
                        self.agent.get_os_plugin().store_file(run_script, native_dir, str("%s_run.sh" % instance_uuid))
                        chmod_cmd = str("chmod +x %s" % os.path.join(native_dir, str("%s_run.sh" % instance_uuid)))
                        self.agent.get_os_plugin().execute_command(chmod_cmd, True)
                        cmd = str("%s" % os.path.join(native_dir, str("%s_run.sh" % instance_uuid)))
                    elif self.operating_system.lower() == 'windows':
                        self.agent.get_os_plugin().store_file(run_script, native_dir, str("%s_run.ps1" % instance_uuid))
                        cmd = str("%s" % os.path.join(native_dir, str("%s_run.ps1" % instance_uuid)))
                    else:
                        cmd = ''

                if instance.source is not None:
                    process = self.__execute_command(cmd, instance.outfile)

                    time.sleep(1)
                    pid_file = str('%s.pid' % instance_uuid)
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
                        if instance.command.endswith('.sh'):
                            command = self.agent.get_os_plugin().read_file(instance.command)
                            na_script = Environment().from_string(command)
                            na_script = na_script.render(pid_file='{}_{}.pid'.format(os.path.join(self.BASE_DIR, entity_uuid), instance_uuid))

                            f_name = '{}_{}.sh'.format(entity_uuid, instance_uuid)
                            f_path = self.BASE_DIR
                            self.agent.get_os_plugin().store_file(na_script, f_path, f_name)
                            cmd = '{} {}'.format('{}_{}.sh'.format(os.path.join(self.BASE_DIR, entity_uuid), instance_uuid), ''.join(entity.args))
                            f_path = os.path.join(f_path, f_name)
                            self.agent.get_os_plugin().execute_command('chmod +x {}'.format(f_path))
                        else:
                            native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                            pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                            template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_unix2.sh'))
                            na_script = Environment().from_string(template_xml)
                            na_script = na_script.render(command=cmd, outfile=pid_file)
                            self.agent.get_os_plugin().store_file(na_script, native_dir, str("%s_run.sh" % instance_uuid))
                            chmod_cmd = str("chmod +x %s" % os.path.join(native_dir, str("%s_run.sh" % instance_uuid)))
                            self.agent.get_os_plugin().execute_command(chmod_cmd, True)
                            cmd = str("%s" % os.path.join(native_dir, str("%s_run.sh" % instance_uuid)))
                    elif self.operating_system.lower() == 'windows':
                        native_dir = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name)
                        pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, instance_uuid)
                        template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_windows.ps1'))
                        na_script = Environment().from_string(template_xml)
                        na_script = na_script.render(command=cmd, outfile=pid_file)
                        self.agent.get_os_plugin().store_file(na_script, native_dir, str("%s_run.ps1" % instance_uuid))
                        cmd = str("%s" % os.path.join(native_dir, str("%s_run.ps1" % instance_uuid)))

                    self.agent.logger.info('runEntity()', 'Command is {}'.format(cmd))

                    process = self.__execute_command(cmd, instance.outfile)
                    instance.on_start(process.pid, process)

                self.current_entities.update({entity_uuid: entity})
                uri = str('%s/%s/%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({"status": "run"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('runEntity()', '[ DONE ] Native Plugin - Running BE uuid %s' % instance_uuid)
                return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stopEntity()', ' Native Plugin - Stop BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stopEntity()', 'Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('stopEntity()', 'Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.RUNNING:
                self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException("Instance is not in RUNNING state",
                                                         str("Instance %s is not in RUNNING state" % instance_uuid))
            else:
                p = instance.process
                p.terminate()

                cmd = "{} {}".format(entity.command, ' '.join(str(x) for x in entity.args))

                if instance.source is None:
                    # pid = int(self.agent.get_os_plugin().read_file(os.path.join(self.BASE_DIR,entity_uuid)))
                    pid = instance.pid
                    self.agent.logger.info('stopEntity()', 'Instance source is none')
                    self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                    self.agent.get_os_plugin().send_sig_int(pid)
                    f_name = '{}_{}.pid'.format(entity_uuid, instance_uuid)
                    f_path = self.BASE_DIR

                    pid_file = os.path.join(f_path, f_name)
                    self.agent.logger.info('stopEntity()', 'Check if PID file exists {}'.format(pid_file))
                    if self.agent.get_os_plugin().file_exists(pid_file):
                        pid = int(self.agent.get_os_plugin().read_file(pid_file))
                        self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                        self.agent.get_os_plugin().execute_command('sudo pkill -9 -P {}'.format(pid))
                        if self.agent.get_os_plugin().check_if_pid_exists(pid):
                            self.agent.get_os_plugin().send_sig_int(pid)
                            time.sleep(10)
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
                            time.sleep(10)
                        if self.agent.get_os_plugin().check_if_pid_exists(pid):
                            self.agent.get_os_plugin().send_sig_kill(pid)

                else:
                    self.agent.logger.info('stopEntity()', 'Instance source is not none')
                    pid_file = os.path.join(self.BASE_DIR, self.STORE_DIR, entity_uuid, instance.name, '{}.pid'.format(instance_uuid))
                    pid = int(self.agent.get_os_plugin().read_file(pid_file))
                    self.agent.logger.info('stopEntity()', 'Native Plugin - PID {}'.format(pid))
                    self.agent.get_os_plugin().execute_command('sudo pkill -9 -P {}'.format(pid))
                    if self.agent.get_os_plugin().check_if_pid_exists(pid):
                        self.agent.get_os_plugin().send_sig_int(pid)
                        time.sleep(10)
                    if self.agent.get_os_plugin().check_if_pid_exists(pid):
                        self.agent.get_os_plugin().send_sig_kill(pid)

                instance.on_stop()
                self.current_entities.update({entity_uuid: entity})
                uri = str('%s/%s/%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({"status": "stop"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('stopEntity()', '[ DONE ] Native Plugin - Stopped BE uuid %s' % instance_uuid)
                return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        self.agent.logger.warning('pauseEntity()', 'Native Plugin - Cannot pause a BE')
        return False

    def resume_entity(self, entity_uuid, instance_uuid=None):
        self.agent.logger.warning('resumeEntity()', 'Native Plugin - Cannot resume a BE')
        return False

    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri, ):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)

    def __update_actual_store_instance(self, entity_uuid, instance_uuid, value):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store_instance(self, entity_uuid, instance_uuid, ):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        self.agent.astore.remove(uri)

    def __execute_command(self, command, out_file):
        f = open(out_file, 'w')
        if self.operating_system.lower() == 'windows':
            p = psutil.Popen(['PowerShell', '-File', command], shell=True, stdout=f, stderr=f)
        else:
            # cmd = 'sh -c {}'.format(command)
            cmd_splitted = command.split()
            p = psutil.Popen(cmd_splitted, stdout=f, stderr=f)
        return p

    def __generate_run_script(self, cmd, directory, outfile):
        if self.operating_system.lower() == 'windows':
            self.agent.logger.info('__generate_run_script()', ' Native Plugin - Generating run script for Windows')
            template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates',
                                                                             'run_native_windows.ps1'))
        else:
            self.agent.logger.info('__generate_run_script()', ' Native Plugin - Generating run script for Linux')
            template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'run_native_unix.sh'))
        na_script = Environment().from_string(template_xml)
        na_script = na_script.render(command=cmd, path=directory, outfile=outfile)
        return na_script

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' Native Plugin - React to to URI: %s Value: %s Version: %s' %
                               (uri, value, v))
        if uri.split('/')[-2] == 'entity':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' Native Plugin - This is a remove for URI: %s' % uri)
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
                    else:
                        react_func(entity_data)
        elif uri.split('/')[-2] == 'instance':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' Native Plugin - This is a remove for URI: %s' % uri)
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

    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'clean': self.clean_entity,
            'undefine': self.undefine_entity,
            'stop': self.stop_entity,
            'resume': self.resume_entity,
            'run': self.run_entity
        }

        return r.get(action, None)

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('__force_entity_instance_termination()', ' Native Plugin - Stop a container uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('__force_entity_instance_termination()', 'LXD Plugin - Entity not exists')
            raise EntityNotExistingException("Native not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('__force_entity_instance_termination()', 'LXD Plugin - Instance not found!!')
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






