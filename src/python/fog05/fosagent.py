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
from .store import Store
from fog05.PluginLoader import PluginLoader
from fog05.interfaces.Agent import Agent
from yaks import Yaks
from fog05.interfaces.Constants import *
import threading

class FosAgent(Agent):

    def __init__(self, debug=True, plugins_path=None, configuration=None):
        print(' _____            ____   ____\n'
              '|  ___|__   __ _ / __ \ | ___|\n'
              '| |_ / _ \ / _` | | /| ||___ \ \n'
              '|  _| (_) | (_| | |/_| | ___) |\n'
              '|_|  \___/ \__, |\____/ |____/ \n'
              '           |___/ \n')

        self.logger = DLogger(debug_flag=debug)
        print('\n\n##### OUTPUT TO LOGFILE #####\n\n')
        self.logger.info('__init__()', 'FosAgent Starting...')

        if plugins_path is None:
            self.__PLUGINDIR = './plugins'
        else:
            self.__PLUGINDIR = plugins_path

        try:

            self.logger.info(
                '__init__()', 'Plugins Dir: {}'.format(self.__PLUGINDIR))

            self.conf_file = configuration
            if configuration is None:
                self.conf_file = 'etc/agent.ini'

            self.config = self.__load_configuration(self.conf_file)

            self.pl = PluginLoader(self.__PLUGINDIR)
            self.pl.get_plugins()
            self.__osPlugin = None
            self.__rtPlugins = {}
            self.__nwPlugins = {}
            self.__monPlugins = {}
            self.__manPlugins = {}
            self.__orchPlugins = {}
            self.logger.info('__init__()', '[ INIT ] Loading OS Plugin...')
            self.__load_os_plugin()
            self.logger.info('__init__()', '[ DONE ] Loading OS Plugin...')
            super(FosAgent, self).__init__(self.__osPlugin.get_uuid())

            self.base_path = self.__osPlugin.get_base_path()

            self.sys_id = 0
            self.__PLUGIN_AUTOLOAD = True
            self.__autoload_list = []
            self.yaks_server = '127.0.0.1'
            self.export = True
            self.use_lldpd = True

            # Configuration Parsing

            if 'agent' in self.config:
                if 'SYSID' in self.config['agent']:
                    self.sys_id = int(self.config['agent']['SYSID'])
                if 'UUID' in self.config['agent']:
                    self.uuid = self.config['agent']['UUID']
                if 'YAKS' in self.config['agent']:
                    self.yaks_server = self.config['agent']['YAKS']
                if 'EXPORT' in self.config['agent']:
                    self.export = self.config['agent'].getboolean('EXPORT')
                if 'ENABLE_LLDP' in self.config['agent']:
                    self.use_lldpd = self.config['agent'].getboolean('ENABLE_LLDP')
            if 'plugins' in self.config:
                if 'autoload' in self.config['plugins']:
                    self.__PLUGIN_AUTOLOAD = self.config['plugins'].getboolean(
                        'autoload')
                if 'auto' in self.config['plugins']:
                    self.__autoload_list = json.loads(
                        self.config['plugins']['auto'])
            sid = str(self.uuid)

            self.yaks = Yaks.login(self.yaks_server)

            self.logger.info(
                '__init__()', '[ INIT ] #############################')
            self.logger.info(
                '__init__()', '[ INIT ] fog05 Agent configuration is:')
            self.logger.info(
                '__init__()', '[ INIT ] SYSID: {}'.format(self.sys_id))
            self.logger.info(
                '__init__()', '[ INIT ] UUID: {}'.format(self.uuid))
            self.logger.info(
                '__init__()', '[ INIT ] YAKS SEVER: {}'.format(self.yaks_server))
            self.logger.info(
                '__init__()', '[ INIT ] Plugins directory : {}'.format(self.__PLUGINDIR))
            self.logger.info('__init__()', '[ INIT ] AUTOLOAD Plugins: {}'.format(
                self.__PLUGIN_AUTOLOAD))
            self.logger.info('__init__()', '[ INIT ] Plugins to autoload: {} (empty means all plugin in the directory)'.format(
                ' '.join(self.__autoload_list)))
            self.logger.info(
                '__init__()', '[ INIT ] #############################')

            # self.sroot = append_to_path(sroot, self.sys_id)
            # self.shome = '{}/{}'.format(self.sroot, 'info')
            # self.logger.info('__init__()', '[ INIT ] Creating System Info Store ROOT: {} HOME: {}'.format(self.sroot, self.shome))
            # self.sstore = Store(self.yaks, self.sroot, self.shome, 1024)
            # self.logger.info('__init__()', '[ INIT ] fog05 System Information loading')

            # self.users = []
            # self.networks = []
            # self.entities = []

            # uri = '{}/tenants'.format(self.shome)
            # i = self.sstore.get(uri)
            # if i is not None:
            #     ti = json.loads(i)
            #     for t in ti:
            #         if t.get('uuid') == 0:
            #             n = t.get('nodes')
            #             n.append(sid)
            #             # t.update({'nodes': n})

            #     self.sstore.put(uri, json.dumps(ti))
            #     self.tenants = ti
            # else:
            #     quotas = {
            #         'max_vcpu': -1,
            #         'current_vcpu': 0,
            #         'max_vdisk': -1,
            #         'current_vdisk': 0,
            #         'max_vnetwork': -1,
            #         'current_vnetwork': 0,
            #         'max_instances': -1,
            #         'current_instances': 0
            #     }
            #     ti = [{
            #         'uuid': 0,
            #         'quotas': quotas,
            #         'users': [],
            #         'nodes': [sid],
            #         'name': 'default'
            #     }]
            #     self.sstore.put(uri, json.dumps(ti))
            #     self.tenants = ti

            # uri = '{}/users'.format(self.shome)
            # i = self.sstore.get(uri)
            # if i is not None:
            #     self.users = json.loads(i)

            # uri = '{}/entities'.format(self.shome)
            # i = self.sstore.get(uri)
            # if i is not None:
            #     self.entities = json.loads(i)

            # uri = '{}/networks'.format(self.shome)
            # i = self.sstore.get(uri)
            # if i is not None:
            #     self.networks = json.loads(i)

            # self.logger.info('__init__()', '[ INIT ] #############################')
            # self.logger.info('__init__()', '[ INIT ] fog05 System Information are:')
            # self.logger.info('__init__()', '[ INIT ] Tenants: {}'.format(json.dumps(self.tenants)))
            # self.logger.info('__init__()', '[ INIT ] Users: {}'.format(json.dumps(self.users)))
            # self.logger.info('__init__()', '[ INIT ] Networks: {}'.format(json.dumps(self.networks)))
            # self.logger.info('__init__()', '[ INIT ] #############################')

            # Desired Store. containing the desired state
            self.droot = append_to_path(droot, self.sys_id)
            self.dhome = '{}/{}'.format(self.droot, sid)
            self.logger.info('__init__()', '[ INIT ] Creating Desired State Store ROOT: {} HOME: {}'.format(
                self.droot, self.dhome))
            self.dstore = Store(self.yaks, self.droot, self.dhome, 1024)
            self.logger.info(
                '__init__()', '[ DONE ] Creating Desired State Store')

            # Actual Store, containing the Actual State
            self.aroot = append_to_path(aroot, self.sys_id)
            self.ahome = '{}/{}'.format(self.aroot, sid)
            self.logger.info('__init__()', '[ INIT ] Creating Actual State Store ROOT: {} HOME: {}'.format(
                self.aroot, self.ahome))
            self.astore = Store(self.yaks, self.aroot, self.ahome, 1024)
            self.logger.info(
                '__init__()', '[ DONE ] Creating Actual State Store')

            if self.export:
                self.logger.info(
                    '__init__()', '[ INIT ] Populating Actual Store with data from OS Plugin')
                val = {'version': self.__osPlugin.version,
                    'description': '{} plugin'.format(self.__osPlugin.name)}
                uri = '{}/plugins/{}/{}'.format(self.ahome,
                                                self.__osPlugin.name, self.__osPlugin.uuid)
                self.astore.put(uri, json.dumps(val))

                val = {'plugins': [{'name': self.__osPlugin.name, 'version': self.__osPlugin.version, 'uuid': str(
                    self.__osPlugin.uuid), 'type': 'os', 'status': 'loaded'}]}
                uri = '{}/plugins'.format(self.ahome)
                self.astore.put(uri, json.dumps(val))

                val = {'plugins': []}
                uri = '{}/plugins'.format(self.dhome)
                self.dstore.put(uri, json.dumps(val))

                self.__populate_node_information()
                self.logger.info(
                    '__init__()', '[ DONE ] Populating Actual Store with data from OS Plugin')
            else:
                self.logger.info(
                    '__init__()', '[ INIT ] Populating Actual Store with data as Orchestrator Node')
                node_info = {}
                node_info.update({'uuid': str(self.uuid)})
                node_info.update({'name': self.__osPlugin.get_hostname()})
                node_info.update({'orchestrator': True})
                self.astore.put(self.ahome, json.dumps(node_info))
                self.logger.info(
                    '__init__()', '[ DONE ] Populating Actual Store with data as Orchestrator Node')
            load_after = []
            if self.__PLUGIN_AUTOLOAD:
                self.logger.info('__init__()', 'Autoloading plugins....')
                plugins = self.pl.plugins
                for p in plugins:
                    if p['name'] in self.__autoload_list or len(self.__autoload_list) == 0:
                        mfile = p.get('info').replace(
                            '__init__.py', '{}_plugin.json'.format(p.get('name')))
                        if self.__osPlugin.file_exists(mfile):
                            manifest = json.loads(
                                self.__osPlugin.read_file(mfile))
                            name = manifest.get('name')
                            plugin_uuid = manifest.get('uuid')
                            conf = manifest.get('configuration', None)
                            # req = manifest.get('requirements', None)
                            # if req is not None:
                            #     self.pl.install_requirements(req)
                            if manifest.get('type') in ['manager', 'orchestrator']:
                                load_after.append(p)
                                self.logger.info(
                                    '__init__()', '[ INFO ] This plugin {} will be load after'.format(p))
                            else:
                                load_method = self.__load_plugin_method_selection(
                                    manifest.get('type'))
                                if load_method is not None:
                                    if conf is None:
                                        load_method(name, plugin_uuid)
                                    else:
                                        load_method(name, plugin_uuid, conf)
                for p in load_after:
                    mfile = p.get('info').replace(
                        '__init__.py', '{}_plugin.json'.format(p.get('name')))
                    if self.__osPlugin.file_exists(mfile):
                        manifest = json.loads(self.__osPlugin.read_file(mfile))
                        name = manifest.get('name')
                        self.logger.info(
                            '__init__()', '[ INFO ] {}'.format(manifest))
                        plugin_uuid = manifest.get('uuid')
                        conf = manifest.get('configuration', None)
                        load_method = self.__load_plugin_method_selection_mano(
                            manifest.get('type'))
                        if load_method is not None:
                            if conf is None:
                                load_method(name, plugin_uuid)
                            else:
                                load_method(name, plugin_uuid, conf)
                        else:
                            self.logger.warning(
                                '__react_to_plugins()', '[ WARN ] Plugins of type {} are not yet supported...'.format(manifest.get('type')))

            if (self.use_lldpd):
                mt = threading.Thread(target=self.__update_neighbors,
                                        args=(10,),daemon=True)
                mt.start()

        except FileNotFoundError as fne:
            self.logger.error(
                '__init__()', 'File Not Found Aborting {} '.format(fne.strerror))
            exit(-1)
        except Exception as e:
            self.logger.error(
                '__init__()', 'Something trouble happen {} '.format(e))
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
                self.logger.error('__load_os_plugin()',
                                  'Error on Loading GNU\Linux plugin!!!')
                raise RuntimeError('Error on loading OS Plugin')
        elif platform == 'darwin':
            self.logger.info('__load_os_plugin()', 'fosAgent running on macOS')
            self.logger.error('__load_os_plugin()',
                              ' Mac plugin not yet implemented...')
            raise RuntimeError('Mac plugin not yet implemented...')
        elif platform in ['windows', 'Windows', 'win32']:
            os = self.pl.locate_plugin('windows')
            if os is not None:
                os = self.pl.load_plugin(os)
                self.__osPlugin = os.run(agent=self)
            else:
                self.logger.error('__load_os_plugin()',
                                  'Error on Loading Windows plugin!!!')
                raise RuntimeError('Error on loading OS Plugin')
        else:
            self.logger.error('__load_os_plugin()',
                              'Platform {} not compatible!!!!'.format(platform))
            raise RuntimeError('__load_os_plugin()', 'Platform not compatible')

    def get_os_plugin(self):
        return self.__osPlugin

    def get_network_plugin(self, cnetwork_uuid):
        if cnetwork_uuid is None:
            return self.__nwPlugins
        else:
            return self.__nwPlugins.get(cnetwork_uuid)

    def __load_runtime_plugin(self, plugin_name, plugin_uuid, configuration=None):
        self.logger.info('__load_runtime_plugin()',
                         'Loading a Runtime plugin: {}'.format(plugin_name))
        rt = self.pl.locate_plugin(plugin_name)
        if rt is not None:
            self.logger.info('__load_runtime_plugin()',
                             '[ INIT ] Loading a Runtime plugin: {}'.format(plugin_name))
            rt = self.pl.load_plugin(rt)
            rt = rt.run(agent=self, uuid=plugin_uuid,
                        configuration=configuration)
            self.__rtPlugins.update({rt.uuid: rt})
            val = {'version': rt.version, 'description': str(
                'runtime {}'.format(rt.name)), 'plugin': ''}
            uri = '{}/plugins/{}/{}'.format(self.ahome, rt.name, rt.uuid)
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': rt.name, 'version': rt.version, 'uuid': str(rt.uuid),
                                'type': 'runtime', 'status': 'loaded'}]}
            uri = '{}/plugins'.format(self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_runtime_plugin()',
                             '[ DONE ] Loading a Runtime plugin: {}'.format(plugin_name))

            return rt
        else:
            self.logger.warning(
                '__load_runtime_plugin()', '[ WARN ] Runtime: {} plugin not found!'.format(plugin_name))
            return None

    def __load_network_plugin(self, plugin_name, plugin_uuid, configuration={}):
        self.logger.info('__load_network_plugin()',
                         'Loading a Network plugin: {}'.format(plugin_name))
        net = self.pl.locate_plugin(plugin_name)
        if net is not None:
            self.logger.info('__load_network_plugin()',
                             '[ INIT ] Loading a Network plugin: {}'.format(plugin_name))
            net = self.pl.load_plugin(net)
            net = net.run(agent=self, uuid=plugin_uuid,
                          configuration=configuration)
            self.__nwPlugins.update({net.uuid: net})

            val = {'version': net.version, 'description': 'network {}'.format(net.name),
                   'plugin': ''}
            uri = '{}/plugins/{}/{}'.format(self.ahome, net.name, net.uuid)
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': net.name, 'version': net.version, 'uuid': str(net.uuid),
                                'type': 'network', 'status': 'loaded'}]}
            uri = '{}/plugins'.format(self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_network_plugin()',
                             '[ DONE ] Loading a Network plugin: {}'.format(plugin_name))

            return net
        else:
            self.logger.warning(
                '__load_network_plugin()', '[ WARN ] Network: {} plugin not found!'.format(plugin_name))
            return None

    def __load_monitoring_plugin(self, plugin_name, plugin_uuid, configuration=None):
        self.logger.info('__load_monitoring_plugin()',
                         'Loading a Monitoring plugin: {}'.format(plugin_name))
        mon = self.pl.locate_plugin(plugin_name)
        if mon is not None:
            self.logger.info('__load_monitoring_plugin()',
                             '[ INIT ] Loading a Monitoring plugin: {}'.format(plugin_name))
            mon = self.pl.load_plugin(mon)
            mon = mon.run(agent=self, uuid=plugin_uuid,
                          configuration=configuration)
            self.__monPlugins.update({mon.uuid: mon})

            val = {'version': mon.version, 'description': 'monitoring {}'.format(
                mon.name), 'plugin': ''}
            uri = '{}/plugins/{}/{}'.format(self.ahome, mon.name, mon.uuid)
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': mon.name, 'version': mon.version, 'uuid': str(mon.uuid),
                                'type': 'monitoring', 'status': 'loaded'}]}
            uri = '{}/plugins'.format(self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_monitoring_plugin()',
                             '[ DONE ] Loading a Monitoring plugin: {}'.format(plugin_name))

            return mon
        else:
            self.logger.warning('__load_monitoring_plugin()',
                                '[ WARN ] Monitoring: {} plugin not found!'.format(plugin_name))
            return None

    def __load_orchestration_plugin(self, plugin_name, plugin_uuid, configuration=None):
        self.logger.info('__load_orchestration_plugin()',
                         'Loading a Orchestration plugin: {}'.format(plugin_name))
        orch = self.pl.locate_plugin(plugin_name)
        if orch is not None:
            self.logger.info('__load_orchestration_plugin()',
                             '[ INIT ] Loading a Orchestration plugin: {}'.format(plugin_name))
            orch = self.pl.load_plugin(orch)
            orch = orch.run(agent=self, uuid=plugin_uuid,
                            configuration=configuration)
            self.__orchPlugins.update({orch.uuid: orch})

            val = {'version': orch.version, 'description': 'orchestration {}'.format(
                orch.name), 'plugin': ''}
            uri = '{}/plugins/{}/{}'.format(self.ahome, orch.name, orch.uuid)
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': orch.name, 'version': orch.version, 'uuid': str(orch.uuid),
                                'type': 'orchestration', 'status': 'loaded'}]}
            uri = '{}/plugins'.format(self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_orchestration_plugin()',
                             '[ DONE ] Loading a Orchestration plugin: {}'.format(plugin_name))

            return orch
        else:
            self.logger.warning('__load_orchestration_plugin()',
                                '[ WARN ] Orchestration: {} plugin not found!'.format(plugin_name))
            return None

    def __load_manager_plugin(self, plugin_name, plugin_uuid, configuration=None):
        self.logger.info('__load_manager_plugin()',
                         'Loading a Manager plugin: {}'.format(plugin_name))
        man = self.pl.locate_plugin(plugin_name)
        self.logger.info('__load_manager_plugin()',
                         'Manager plugin: {}'.format(man))
        if man is not None:
            self.logger.info('__load_manager_plugin()',
                             '[ INIT ] Loading a Manager plugin: {}'.format(plugin_name))
            man = self.pl.load_plugin(man)
            man = man.run(agent=self, uuid=plugin_uuid,
                          configuration=configuration)
            self.__manPlugins.update({man.uuid: man})

            val = {'version': man.version,
                'description': 'manager {}'.format(man.name), 'plugin': ''}
            uri = '{}/plugins/{}/{}'.format(self.ahome, man.name, man.uuid)
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': man.name, 'version': man.version, 'uuid': str(man.uuid),
                                'type': 'manager', 'status': 'loaded'}]}
            uri = '{}/plugins'.format(self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_manager_plugin()',
                             '[ DONE ] Loading a Manager plugin: {}'.format(plugin_name))

            return man
        else:
            self.logger.warning(
                '__load_manager_plugin()', '[ WARN ] Manager: {} plugin not found!'.format(plugin_name))
            return None

    def __populate_node_information(self):

        node_info = {}
        node_info.update({'uuid': str(self.uuid)})
        node_info.update({'name': self.__osPlugin.get_hostname()})
        node_info.update({'os': self.__osPlugin.name})
        node_info.update({'cpu': self.__osPlugin.get_processor_information()})
        node_info.update({'ram': self.__osPlugin.get_memory_information()})
        node_info.update({'disks': self.__osPlugin.get_disks_information()})
        node_info.update(
            {'network': self.__osPlugin.get_network_informations()})
        node_info.update({'io': self.__osPlugin.get_io_informations()})
        node_info.update(
            {'accelerator': self.__osPlugin.get_accelerators_informations()})

        self.logger.info('__populate_node_information()', 'Node info size is: {}s'.format(len(json.dumps(node_info))))
        uri = '{}'.format(self.ahome)
        self.astore.put(uri, json.dumps(node_info))


        if self.use_lldpd:
            n_info = {'neighbors': self.__osPlugin.get_neighbors()}
            uri = '{}/neighbors'.format(self.ahome)
            self.astore.put(uri, json.dumps(n_info))

    def __update_neighbors(self, interval):
        self.logger.info('__update_neighbors()', 'With interval: {}s'.format(interval))
        time.sleep(interval)
        while True:
            n_info = self.__osPlugin.get_neighbors()
            uri = '{}/neighbors'.format(self.ahome)
            self.astore.put(uri, json.dumps(n_info))
            time.sleep(interval)

    def __react_to_plugins(self, uri, value, v):
        self.logger.info('__react_to_plugins()', ' Received a plugin action on Desired Store URI: {} Value: {} Version: {}'.format(uri, value, v))
        if value is None:
            self.logger.error('__react_to_plugins()', 'ERROR RECEIVED VALUE {}'.format(value))
            return
        value = json.loads(value)
        value = value.get('plugins')
        for v in value:
            uri = '{}/plugins'.format(self.ahome)
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

    def __load_plugin_method_selection_mano(self, type):
        r = {
            'orchestration': self.__load_orchestration_plugin,
            'manager': self.__load_manager_plugin
        }
        return r.get(type, None)

    def __react_to_onboarding(self, uri, value, v):
        self.logger.info('__react_to_onboarding()', 'Received a onboard action on Desired Store with URI:{} Value:{} Version:{}'.format(uri, value, v))
        application_uuid = uri.split('/')[-1]
        dvalue = json.loads(value)
        if dvalue.get('status') == 'undefine':
            self.logger.info('__react_to_onboarding()', 'This is a remove for URI: %s' % uri)
            nuri = '{}/onboard/{}'.format(self.ahome, application_uuid)
            self.astore.remove(nuri)
        else:
            nuri = '{}/onboard/{}'.format(self.ahome,application_uuid)
            self.astore.put(nuri,value)
            self.logger.info('__react_to_onboarding()', 'Received a onboard information storing to -> {}'.format(nuri))
            application_uuid = uri.split('/')[-1]

    def __get_manifest(self, manifest_path):
        return json.loads(self.dstore.get(manifest_path))

    def __search_plugin_by_name(self, name):
        uri = '{}/plugins'.format(self.ahome)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')
        search = [x for x in all_plugins if name in x.get('name')]
        if len(search) == 0:
            return None
        else:
            return search[0]

    def __exit_gracefully(self, signal, frame):
        self.logger.info('__exit_gracefully()', 'Received signal: {}'.format(signal))
        self.logger.info('__exit_gracefully()', 'fosAgent exiting...')
        keys = list(self.__manPlugins.keys())
        for k in keys:
            try:
                self.__manPlugins.get(k).stop()
            except Exception as e:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                pass
        keys = list(self.__rtPlugins.keys())
        for k in keys:
            try:
                self.__rtPlugins.get(k).stop_runtime()
            except Exception as e:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                # traceback.print_exc()
                pass
        keys = list(self.__nwPlugins.keys())
        for k in keys:
            try:
                self.__nwPlugins.get(k).stop_network()
            except Exception:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                # traceback.print_exc()
                pass

        keys = list(self.__monPlugins.keys())
        for k in keys:
            try:
                self.__monPlugins.get(k).stop_monitoring()
            except Exception:
                self.logger.error('__exit_gracefully()', '{}'.format(e))
                # traceback.print_exc()
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
        # self.dstore.remove('{}/**'.format(self.dhome))
        # self.astore.remove('{}/**'.format(self.ahome))
        [self.dstore.remove(x) for (x,_,_) in self.dstore.getAll('{}/**'.format(self.dhome))]
        [self.astore.remove(x) for (x,_,_) in self.astore.getAll('{}/**'.format(self.ahome))]
        self.astore.remove('{}'.format(self.ahome))
        self.dstore.remove('{}'.format(self.dhome))
        self.dstore.close()
        self.astore.close()
        self.logger.info('__exit_gracefully()', '[ DONE ] Bye')
        sys.exit(0)

    def run(self):

        uri = '{}/onboard/**'.format(self.dhome)
        self.dstore.observe(uri, self.__react_to_onboarding)
        self.logger.info('run()', 'fosAgent Observing for onboarding on: {}'.format(uri))

        uri = '{}/plugins'.format(self.dhome)
        self.dstore.observe(uri, self.__react_to_plugins)
        self.logger.info('run()', 'fosAgent Observing plugins on: {}'.format(uri))

        '''
        uri = '{}/entities'.format(self.shome)
        self.sstore.observe(uri,
                            lambda key ,value, version:
                                self.logger.info('lambda observer {}'.format(uri), 'KEY: {} VALUE:{} VERSION:{}'.format(key, value, version))
                            )
        self.logger.info('run()', 'fosAgent Observing entities on: {}'.format(uri))
        '''

        self.logger.info('run()', '[ DONE ] fosAgent Up and Running')
        return self

    def stop(self):
        self.__exit_gracefully(2, None)
