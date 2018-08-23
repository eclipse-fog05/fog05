# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Initial implementation and API

import json
# import networkx as nx
import configparser
import time
import traceback
import sys
import json
import uuid
from fog05.DLogger import DLogger
from dstore import Store
from fog05.PluginLoader import PluginLoader
from fog05.interfaces.Agent import Agent


class FosAgent(Agent):

    def __init__(self, debug=True, plugins_path=None):
        print(" _____            ____   ____\n"
              "|  ___|__   __ _ / __ \ | ___|\n"
              "| |_ / _ \ / _` | | /| ||___ \ \n"
              "|  _| (_) | (_| | |/_| | ___) |\n"
              "|_|  \___/ \__, |\____/ |____/ \n"
              "           |___/ \n")

        self.logger = DLogger(debug_flag=debug)
        print("\n\n##### OUTPUT TO LOGFILE #####\n\n")
        self.logger.info('__init__()', 'FosAgent Starting...')

        if plugins_path is None:
            self.__PLUGINDIR = './plugins'
        else:
            self.__PLUGINDIR = plugins_path



        try:

            self.logger.info('__init__()', 'Plugins Dir: {}'.format(self.__PLUGINDIR))
            self.config = self.__load_configuration('etc/agent.ini')

            self.pl = PluginLoader(self.__PLUGINDIR)
            self.pl.get_plugins()
            self.__osPlugin = None
            self.__rtPlugins = {}
            self.__nwPlugins = {}
            self.__monPlugins = {}
            self.logger.info('__init__()', '[ INIT ] Loading OS Plugin...')
            self.__load_os_plugin()
            self.logger.info('__init__()', '[ DONE ] Loading OS Plugin...')
            super(FosAgent, self).__init__(self.__osPlugin.get_uuid())

            self.base_path = self.__osPlugin.get_base_path()

            self.sys_id = 0
            self.__PLUGIN_AUTOLOAD = True
            self.__autoload_list = []

            # Configuration Parsing

            if 'agent' in self.config:
                if 'SYSID' in self.config['agent']:
                    self.sys_id = int(self.config['agent']['SYSID'])
                if 'UUID' in self.config['agent']:
                    self.uuid = self.config['agent']['uuid']
            if 'plugins' in self.config:
                if 'autoload' in self.config['plugins']:
                    self.__PLUGIN_AUTOLOAD = self.config['plugins'].getboolean('autoload')
                if 'auto' in self.config['plugins']:
                    self.__autoload_list = json.loads(self.config['plugins']['auto'])
            sid = str(self.uuid)

            self.logger.info('__init__()', '[ INIT ] #############################')
            self.logger.info('__init__()', '[ INIT ] fog05 Agent configuration is:')
            self.logger.info('__init__()', '[ INIT ] SYSID: {}'.format(self.sys_id))
            self.logger.info('__init__()', '[ INIT ] UUID: {}'.format(self.uuid))
            self.logger.info('__init__()', '[ INIT ] Plugins directory : {}'.format(self.__PLUGINDIR))
            self.logger.info('__init__()', '[ INIT ] AUTOLOAD Plugins: {}'.format(self.__PLUGIN_AUTOLOAD))
            self.logger.info('__init__()', '[ INIT ] Plugins to autoload: {} (empty means all plugin in the directory)'.format(' '.join(self.__autoload_list)))
            self.logger.info('__init__()', '[ INIT ] #############################')
            '''
            self.sroot = "sfos://{}".format(self.sys_id)
            self.shome = str("{}/{}".format(self.sroot, 'info'))
            self.logger.info('__init__()', '[ INIT ] Creating System Info Store ROOT: {} HOME: {}'.format(self.sroot, self.shome))
            self.sstore = Store(sid, self.sroot, self.shome, 1024)
            self.logger.info('__init__()', '[ INIT ] fog05 System Information loading')

            self.users = []
            self.networks = []

            uri = '{}/tenants'.format(self.shome)
            i = self.sstore.get(uri)
            if i is not None:
                ti = json.loads(i)
                for t in ti:
                    if t.get('uuid') == 0:
                        n = t.get('nodes')
                        n.append(sid)
                        # t.update({'nodes': n})

                self.sstore.put(uri, json.dumps(ti))
                self.tenants = ti
            else:
                quotas = {
                    'max_vcpu': -1,
                    'current_vcpu': 0,
                    'max_vdisk': -1,
                    'current_vdisk': 0,
                    'max_vnetwork': -1,
                    'current_vnetwork': 0,
                    'max_instances': -1,
                    'current_instances': 0
                }
                ti = [{
                    'uuid': 0,
                    'quotas': quotas,
                    'users': [],
                    'nodes': [sid],
                    'name': 'default'
                }]
                self.sstore.put(uri, json.dumps(ti))
                self.tenants = ti

            uri = '{}/users'.format(self.shome)
            i = self.sstore.get(uri)
            if i is not None:
                self.users = json.loads(i)

            uri = '{}/networks'.format(self.shome)
            i = self.sstore.get(uri)
            if i is not None:
                self.networks = json.loads(i)

            self.logger.info('__init__()', '[ INIT ] #############################')
            self.logger.info('__init__()', '[ INIT ] fog05 System Information are:')
            self.logger.info('__init__()', '[ INIT ] Tenants: {}'.format(json.dumps(self.tenants)))
            self.logger.info('__init__()', '[ INIT ] Users: {}'.format(json.dumps(self.users)))
            self.logger.info('__init__()', '[ INIT ] Networks: {}'.format(json.dumps(self.networks)))
            self.logger.info('__init__()', '[ INIT ] #############################')
            '''
            # Desired Store. containing the desired state
            self.droot = "dfos://{}".format(self.sys_id)
            self.dhome = str("{}/{}".format(self.droot, sid))
            self.logger.info('__init__()', '[ INIT ] Creating Desired State Store ROOT: {} HOME: {}'.format(self.droot, self.dhome))
            self.dstore = Store(sid, self.droot, self.dhome, 1024)
            self.logger.info('__init__()', '[ DONE ] Creating Desired State Store')

            # Actual Store, containing the Actual State
            self.aroot = "afos://{}".format(self.sys_id)
            self.ahome = str("{}/{}".format(self.aroot, sid))
            self.logger.info('__init__()', '[ INIT ] Creating Actual State Store ROOT: {} HOME: {}'.format(self.aroot, self.ahome))
            self.astore = Store(sid, self.aroot, self.ahome, 1024)
            self.logger.info('__init__()', '[ DONE ] Creating Actual State Store')

            self.logger.info('__init__()', '[ INIT ] Populating Actual Store with data from OS Plugin')
            val = {'version': self.__osPlugin.version, 'description': '{} plugin'.format(self.__osPlugin.name)}
            uri = str('{}/plugins/{}/{}'.format(self.ahome, self.__osPlugin.name, self.__osPlugin.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': self.__osPlugin.name, 'version': self.__osPlugin.version, 'uuid': str(
                self.__osPlugin.uuid), 'type': 'os', 'status': 'loaded'}]}
            uri = str('{}/plugins'.format(self.ahome))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': []}
            uri = str('{}/plugins'.format(self.dhome))
            self.dstore.put(uri, json.dumps(val))

            self.__populate_node_information()
            self.logger.info('__init__()', '[ DONE ] Populating Actual Store with data from OS Plugin')

            if self.__PLUGIN_AUTOLOAD:
                self.logger.info('__init__()', 'Autoloading plugins....')
                plugins = self.pl.plugins
                for p in plugins:

                    if p['name'] in self.__autoload_list or len(self.__autoload_list) == 0:
                        mfile = p.get('info').replace('__init__.py','{}_plugin.json'.format(p.get('name')))
                        if self.__osPlugin.file_exists(mfile):
                            manifest = json.loads(self.__osPlugin.read_file(mfile))
                            name = manifest.get('name')
                            plugin_uuid = manifest.get('uuid')
                            conf = manifest.get('configuration', None)
                            req = manifest.get('requirements', None)
                            # if req is not None:
                            #     self.pl.install_requirements(req)
                            load_method = self.__load_plugin_method_selection(manifest.get('type'))
                            if load_method is not None:
                                if conf is None:
                                    load_method(name, plugin_uuid)
                                else:
                                    load_method(name, plugin_uuid, conf)
                            else:
                                if len(s) != 0:
                                    self.logger.warning('__react_to_plugins()', '[ WARN ] Plugins of type {} are not yet supported...'.format(v.get('type')))
                                else:
                                    self.logger.warning('__react_to_plugins()', '[ WARN ] Plugin already loaded')



        except FileNotFoundError as fne:
            self.logger.error('__init__()', "File Not Found Aborting {} ".format(fne.strerror))
            exit(-1)
        except Exception as e:
            self.logger.error('__init__()', "Something trouble happen {} ".format(e))
            traceback.print_exc()
            exit(-1)

    def __load_configuration(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        return config

    def __load_os_plugin(self):
        platform = sys.platform
        if platform == 'linux':
            self.logger.info('__init__()', 'fosAgent running on GNU\Linux')
            os = self.pl.locate_plugin('linux')
            if os is not None:
                os = self.pl.load_plugin(os)
                self.__osPlugin = os.run(agent=self)
            else:
                self.logger.error('__load_os_plugin()', 'Error on Loading GNU\Linux plugin!!!')
                raise RuntimeError("Error on loading OS Plugin")
        elif platform == 'darwin':
            self.logger.info('__load_os_plugin()', 'fosAgent running on macOS')
            self.logger.error('__load_os_plugin()', ' Mac plugin not yet implemented...')
            raise RuntimeError("Mac plugin not yet implemented...")
        elif platform in ['windows', 'Windows', 'win32']:
            os = self.pl.locate_plugin('windows')
            if os is not None:
                os = self.pl.load_plugin(os)
                self.__osPlugin = os.run(agent=self)
            else:
                self.logger.error('__load_os_plugin()', 'Error on Loading Windows plugin!!!')
                raise RuntimeError("Error on loading OS Plugin")
        else:
            self.logger.error('__load_os_plugin()', 'Platform {} not compatible!!!!'.format(platform))
            raise RuntimeError('__load_os_plugin()', "Platform not compatible")

    def get_os_plugin(self):
        return self.__osPlugin

    def get_network_plugin(self, cnetwork_uuid):
        if cnetwork_uuid is None:
            return self.__nwPlugins
        else:
            return self.__nwPlugins.get(cnetwork_uuid)

    def __load_runtime_plugin(self, plugin_name, plugin_uuid, configuration = None):
        self.logger.info('__load_runtime_plugin()', 'Loading a Runtime plugin: {}'.format(plugin_name))
        rt = self.pl.locate_plugin(plugin_name)
        if rt is not None:
            self.logger.info('__load_runtime_plugin()', '[ INIT ] Loading a Runtime plugin: {}'.format(plugin_name))
            rt = self.pl.load_plugin(rt)
            rt = rt.run(agent=self, uuid=plugin_uuid, configuration=configuration)
            self.__rtPlugins.update({rt.uuid: rt})
            val = {'version': rt.version, 'description': str('runtime {}'.format(rt.name)), 'plugin': ''}
            uri = str('{}/plugins/{}/{}'.format(self.ahome, rt.name, rt.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': rt.name, 'version': rt.version, 'uuid': str(rt.uuid),
                                'type': 'runtime', 'status': 'loaded'}]}
            uri = str('{}/plugins'.format(self.ahome))
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_runtime_plugin()', '[ DONE ] Loading a Runtime plugin: {}'.format(plugin_name))

            return rt
        else:
            self.logger.warning('__load_runtime_plugin()', '[ WARN ] Runtime: {} plugin not found!'.format(plugin_name))
            return None

    def __load_network_plugin(self, plugin_name, plugin_uuid, configuration = None):
        self.logger.info('__load_network_plugin()', 'Loading a Network plugin: {}'.format(plugin_name))
        net = self.pl.locate_plugin(plugin_name)
        if net is not None:
            self.logger.info('__load_network_plugin()', '[ INIT ] Loading a Network plugin: {}'.format(plugin_name))
            net = self.pl.load_plugin(net)
            net = net.run(agent=self, uuid=plugin_uuid)
            self.__nwPlugins.update({net.uuid: net})

            val = {'version': net.version, 'description': str('network {}'.format(net.name)),
                   'plugin': ''}
            uri = str('{}/plugins/{}/{}'.format(self.ahome, net.name, net.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': net.name, 'version': net.version, 'uuid': str(net.uuid),
                                'type': 'network', 'status': 'loaded'}]}
            uri = str('{}/plugins'.format(self.ahome))
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_network_plugin()', '[ DONE ] Loading a Network plugin: {}'.format(plugin_name))

            return net
        else:
            self.logger.warning('__load_network_plugin()', '[ WARN ] Network: {} plugin not found!'.format(plugin_name))
            return None

    def __load_monitoring_plugin(self, plugin_name, plugin_uuid, configuration = None):
        self.logger.info('__load_monitoring_plugin()', 'Loading a Monitoring plugin: {}'.format(plugin_name))
        mon = self.pl.locate_plugin(plugin_name)
        if mon is not None:
            self.logger.info('__load_monitoring_plugin()', '[ INIT ] Loading a Monitoring plugin: {}'.format(plugin_name))
            mon = self.pl.load_plugin(mon)
            mon = mon.run(agent=self, uuid=plugin_uuid)
            self.__monPlugins.update({mon.uuid: mon})

            val = {'version': mon.version, 'description': 'monitoring {}'.format(mon.name), 'plugin': ''}
            uri = str('{}/plugins/{}/{}'.format(self.ahome, mon.name, mon.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': mon.name, 'version': mon.version, 'uuid': str(mon.uuid),
                                'type': 'network', 'status': 'loaded'}]}
            uri = str('{}/plugins'.format(self.ahome))
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_monitoring_plugin()', '[ DONE ] Loading a Monitoring plugin: {}'.format(plugin_name))

            return mon
        else:
            self.logger.warning('__load_monitoring_plugin()', '[ WARN ] Monitoring: {} plugin not found!'.format(plugin_name))
            return None

    def __populate_node_information(self):

        node_info = {}
        node_info.update({'uuid': str(self.uuid)})
        node_info.update({'name': self.__osPlugin.get_hostname()})
        node_info.update({'os': self.__osPlugin.name})
        node_info.update({'cpu': self.__osPlugin.get_processor_information()})
        node_info.update({'ram': self.__osPlugin.get_memory_information()})
        node_info.update({'disks': self.__osPlugin.get_disks_information()})
        node_info.update({'network': self.__osPlugin.get_network_informations()})
        node_info.update({'io': self.__osPlugin.get_io_informations()})
        node_info.update({'accelerator': self.__osPlugin.get_accelerators_informations()})

        uri = str('{}'.format(self.ahome))
        self.astore.put(uri, json.dumps(node_info))

    def __react_to_plugins(self, uri, value, v):
        self.logger.info('__react_to_plugins()', ' Received a plugin action on Desired Store URI: {} Value: {} Version: {}'.format(uri, value, v))
        if value is None:
            self.logger.error('__react_to_plugins()', 'ERROR RECEIVED VALUE {}'.format(value))
            return
        value = json.loads(value)
        value = value.get('plugins')
        for v in value:
            uri = str('{}/plugins'.format(self.ahome))
            all_plugins = json.loads(self.astore.get(uri))
            s = [x for x in all_plugins.get('plugins') if v.get('name') in x.get('name')]
            if v.get('status') == 'add' and len(s) == 0:
                name = v.get('name')
                plugin_uuid = v.get('uuid')
                conf = v.get('configuration', None)
                req = v.get('requirements', None)
                if req is not None:
                    self.pl.install_requirements(req)
                load_method = self.__load_plugin_method_selection(v.get('type'))
                if load_method is not None:
                    if conf is None:
                        load_method(name, plugin_uuid)
                    else:
                        load_method(name, plugin_uuid, conf)
                else:
                    if len(s) != 0:
                        self.logger.warning('__react_to_plugins()', '[ WARN ] Plugins of type {} are not yet supported...'.format(v.get('type')))
                    else:
                        self.logger.warning('__react_to_plugins()', '[ WARN ] Plugin already loaded')

    def __load_plugin_method_selection(self, type):
        r = {
            'runtime': self.__load_runtime_plugin,
            'network': self.__load_network_plugin,
            'monitoring': self.__load_monitoring_plugin
        }
        return r.get(type, None)

    def __react_to_onboarding(self, uri, value, v):
        self.logger.info('__react_to_onboarding()', 'Received a onboard action on Desired Store with URI:{} Value:{} Version:{}'.format(uri, value, v))
        application_uuid = uri.split('/')[-1]
        if value is None and v is None:
            self.logger.info('__react_to_onboarding()', 'This is a remove for URI: %s' % uri)
            nuri = '{}/onboard/{}'.format(self.ahome, application_uuid)
            self.astore.remove(nuri)
        else:
            nuri = '{}/onboard/{}'.format(self.ahome,application_uuid)
            self.astore.put(nuri,value)
            self.logger.info('__react_to_onboarding()', 'Received a onboard information storing to -> {}'.format(nuri))
            application_uuid = uri.split('/')[-1]
        # self.__application_onboarding(application_uuid, value)

    def __application_onboarding(self, application_uuid, value):
        self.logger.info('__application_onboarding()', ' Onboarding application with uuid: {}'.format(application_uuid))
        deploy_order_list = self.__resolve_dependencies(value.get('components', None))
        informations = {}
        '''
        With the ordered list of entities the agent should generate the graph of entities
        eg. using NetworkX lib and looking for loops, if it find a loop should fail the application
        onboarding, and signal in the proper uri.
        If no loop are detected then should start instantiate the components
        It's a MANO job to select the correct nodes, and selection should be based on proximity 
        After each deploy the agent should collect correct information for the deploy of components that need other
        components (eg. should retrive the ip address, and then pass in someway to others components)
        '''

        for c in deploy_order_list:
            search = [x for x in value.get('components') if x.get('name') == c]
            if len(search) > 0:
                component = search[0]
            else:
                self.logger.warning('__application_onboarding()', '[ WARN ] Could not find component in component list WTF?')
                raise AssertionError("Could not find component in component list WTF?")


            '''
            Should recover in some way the component manifest
            
            '''
            mf = self.__get_manifest(component.get('manifest'))
            '''
            from this manifest generate the correct json 
            '''
            t = mf.get('type')

            if t == "kvm":
                self.logger.info('__application_onboarding()', 'Component is a VM')
                kvm = self.__search_plugin_by_name('KVM')
                if kvm is None:
                    self.logger.error('__application_onboarding()', '[ ERRO ] KVM Plugin not loaded/found!!!')
                    return False

                '''
                Do stuffs... define, configure and run the vm
                get information about the deploy and save them
                eg. {'name':{ information }, 'name2':{}, .... }
                '''

                node_uuid = str(self.uuid) #@TODO: select deploy node in a smart way

                vm_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('__application_onboarding()', ' Define VM')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}'.format(node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('__application_onboarding()', ' Waiting VM to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}".format(node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] VM DEFINED')

                instance_uuid = str(uuid.uuid4())

                self.logger.info('__application_onboarding()', 'Configure VM')
                uri = str(
                    'dfos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(node_uuid, kvm.get('uuid'), vm_uuid, instance_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Waiting VM to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}".format(node_uuid, kvm.get('uuid'), vm_uuid, instance_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] VM Configured')

                self.logger.info('__application_onboarding()', 'Staring VM')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(node_uuid, kvm.get('uuid'), vm_uuid, instance_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Waiting VM to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}".format(node_uuid, kvm.get('uuid'), vm_uuid, instance_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break

                self.logger.info('__application_onboarding()', '[ DONE ] VM Running on node: {}'.format(node_uuid))

            elif t == "container":
                self.logger.info('__application_onboarding()', 'Component is a Container')
                ## TODO implement using LXD plugin
            elif t == "native":
                self.logger.info('__application_onboarding()', 'Component is a Native Application')
                native = self.__search_plugin_by_name('native')
                if native is None:
                    self.logger.error('__application_onboarding()', '[ ERRO ] Native Application Plugin not loaded/found!!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get('version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('__application_onboarding()', 'Define Native')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}'.format(node_uuid, native.get('uuid'), na_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('__application_onboarding()', 'Native to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}".format(node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] Native DEFINED')

                instance_uuid = str(uuid.uuid4())

                self.logger.info('__application_onboarding()', ' Configure Native')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Native to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}".format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] Native CONFIGURED')

                self.logger.info('__application_onboarding()', 'Starting Native')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Native to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}".format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] Native Running on node: {}'.format(node_uuid))

            elif t == "ros2":
                self.logger.info('__application_onboarding()', 'Component is a ROS2 Application')
                native = self.__search_plugin_by_name('ros2')
                if native is None:
                    self.logger.error('__application_onboarding()', '[ ERRO ] ROS2 Application Plugin not loaded/found!!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get('version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('__application_onboarding()', 'Define ROS2')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}'.format(node_uuid, native.get('uuid'), na_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('__application_onboarding()', 'ROS2 to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}".format(node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] ROS2 DEFINED')

                instance_uuid = str(uuid.uuid4())
                self.logger.info('__application_onboarding()', 'Configure Native')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'ROS2 to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}".format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] ROS2 CONFIGURED')

                self.logger.info('__application_onboarding()', 'Starting ROS2')
                uri = str('dfos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'ROS2 to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/{}/runtime/{}/entity/{}/instance/{}".format(node_uuid, native.get('uuid'), na_uuid, instance_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] ROS2 Running on node: {}'.format(node_uuid))

            elif t == "usvc":
                self.logger.info('__application_onboarding()', 'Component is a Microservice')

            elif t == "application":
                self.logger.info('__application_onboarding()', 'Component is a Complex Application')
                self.__application_onboarding(mf.get("uuid"), mf.get("entity_description"))

            else:
                self.logger.error('__application_onboarding()', "Component type not recognized {}" % t)
                raise AssertionError("Component type not recognized {}" % t)

    def __resolve_dependencies(self, components):
        '''
        The return list contains component's name in the order that can be used to deploy
         @TODO: should use less cycle to do this job
        :rtype: list
        :param components: list like [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]

        no_dependable_components -> list like [[{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}], [{'name': 'c3', 'need': []}], [{'name': 'c2', 'need': []}], [{'name': 'c1', 'need': []}], []]
        :return: list like ['c4', 'c5', 'c3', 'c2', 'c1']
        '''
        c = list(components)
        no_dependable_components = []
        for i in range(0, len(components)):
            no_dependable_components.append([x for x in c if len(x.get('need')) == 0])
            #print (no_dependable_components)
            c = [x for x in c if x not in no_dependable_components[i]]
            for y in c:
                n = y.get('need')
                n = [x for x in n if x not in [z.get('name') for z in no_dependable_components[i]]]
                y.update({"need": n})

        order = []
        for i in range(0, len(no_dependable_components)):
            n = [x.get('name') for x in no_dependable_components[i]]
            order.extend(n)
        return order

    def __get_manifest(self, manifest_path):
        return json.loads(self.dstore.get(manifest_path))

    def __search_plugin_by_name(self, name):
        uri = str('{}/plugins'.format(self.ahome))
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')
        search = [x for x in all_plugins if name in x.get('name')]
        if len(search) == 0:
            return None
        else:
            return search[0]

    def __exit_gracefully(self, signal, frame):
        self.logger.info('__exit_gracefully()', 'Received signal: {}'.format(signal))
        self.logger.info('__exit_gracefully()', 'fosAgent exiting...')
        keys = list(self.__rtPlugins.keys())
        for k in keys:
            try:
                self.__rtPlugins.get(k).stop_runtime()
            except Exception as e:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                #traceback.print_exc()
                pass
        keys = list(self.__nwPlugins.keys())
        for k in keys:
            try:
                self.__nwPlugins.get(k).stop_network()
            except Exception:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                #traceback.print_exc()
                pass

        keys = list(self.__monPlugins.keys())
        for k in keys:
            try:
                self.__monPlugins.get(k).stop_monitoring()
            except Exception:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                #traceback.print_exc()
                pass
        '''
        uri = '{}/tenants'.format(self.shome)
        self.tenants = json.loads(self.sstore.get(uri))
        for t in self.tenants:
            n = t.get('nodes')
            n.remove(str(self.uuid))
        self.sstore.put(uri, json.dumps(self.tenants))
        self.logger.info('__exit_gracefully()', '[ DONE ] Unregistering from tenants')

        self.sstore.close()
        '''
        self.dstore.close()
        self.astore.close()
        self.logger.info('__exit_gracefully()', '[ DONE ] Bye')
        sys.exit(0)

    def run(self):

        uri = str('{}/onboard/*'.format(self.dhome))
        self.dstore.observe(uri, self.__react_to_onboarding)
        self.logger.info('run()', 'fosAgent Observing for onboarding on: {}'.format(uri))

        uri = str('{}/plugins'.format(self.dhome))
        self.dstore.observe(uri, self.__react_to_plugins)
        self.logger.info('run()','fosAgent Observing plugins on: {}'.format(uri))

        self.logger.info('run()','[ DONE ] fosAgent Up and Running')
        return self

    def stop(self):
        self.__exit_gracefully(2, None)
