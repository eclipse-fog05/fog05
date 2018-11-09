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
#
# This plugin is part of EU H2020 5GCity Project Platform
#

import sys
import os
import uuid
import struct
import json
from fog05.interfaces.ResourceOrchestratorPlugin import *
from jinja2 import Environment
import socket


# TODO Plugins should not be aware of the Agent - The Agent is in OCaml no way to access his store, his logger and the OS plugin

class MEPMV(ResourceManagmentPlugin):

    def __init__(self, name, version, agent, plugin_uuid, configuration={}):
        super(MEPMV, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.configuration = configuration
        self.__services = {}
        self.__apps = {}
        self.mec_host = configuration.get('mehost')
        self.meaod = configuration.get('meaod')
        self.meaoa = configuration.get('meaoa')
        self.agent.logger.info('__init__()', ' Hello from 5GCity MEPM-V Plugin')

        '''
        should listen on:
        
        - //dfos/mempv/<uuid>/**
        
        Resources:
        
        - //dfos/mepmv/<uuid>/*/services/<sid>
        - //dfos/mepmv/<uuid>/*/services/<sid>/configuration
        - //dfos/mepmv/<uuid>/*/mecapp/<aid>
        - 
        
        '''

        obs_uri = '//dfos/mepmv/{}/**'.format(self.uuid)
        self.agent.dstore.observe(obs_uri, self.__react_to_cache)
        self.agent.logger.info('startRuntime()', '5GCity MEPM-V Plugin - Observing {}'.format(obs_uri))

        services_uri = '//dfos/mepmv/{}/services'.format(self.uuid)
        mec_app_uri = '//dfos/mepmv/{}/mecapp'.format(self.uuid)
        platform_uri = '//dfos/mepmv/{}'.format(self.uuid)

        uri = '{}/platform/{}'.format(self.meaod, self.uuid)
        data = {'mec_host': self.mec_host,
                'serivice_uri': services_uri,
                'mec_app_uri': mec_app_uri,
                'platform_uri': platform_uri
                }
        self.agent.dstore.put(uri, json.dumps(data))
        uri = '//afos/mepmv/{}'.format(self.uuid)
        self.agent.astore.put(uri, json.dumps(data))

    def configure_application(self, application_uuid, application_manifest):
        raise NotImplemented

    def get_application_configuration(self, application_uuid):
        raise NotImplemented

    def __react_to_cahe(self, uri, value, v):
        if uri.split('/')[-2] == 'services':
            if uri.split('/')[-1] == 'configuration':
                service_uuid = uri.split('/')[-2]
                print('~~~~~~~~~~~~~~ [MEMPV] I should configure service {} on {} with {}'.format(service_uuid, self.uuid, value))
                uri = '//afos/mepmv/{}/services/{}/configuration'.format(self.uuid, service_uuid)
                self.__update_actual_store(uri, json.dumps(value))
            else:
                value = json.loads(value)
                service_uuid = uri.split('/')[-1]
                self.__services.update({service_uuid: value})
                uri = '//afos/mepmv/{}/services/{}'.format(self.uuid, service_uuid)
                self.__update_actual_store(uri, json.dumps(value))
        elif uri.split('/')[-2] == 'mecapp':
            value = json.loads(value)
            app_uuid = uri.split('/')[-1]
            self.__apps.update({app_uuid: value})
            uri = '//afos/mepmv/{}/mecapp/{}'.format(self.uuid, app_uuid)
            self.__update_actual_store(uri, json.dumps(value))
        
    def __react(self, action):
        r = {
            'stop': None,
            'pause': None,
            'remove': None,
            'restart': None,
        }

        return r.get(action, None)

    def __update_actual_store(self, uri, value):
        uri = '{}/{}'.format(self.agent.ahome, uri)
        # self.agent.logger.error('__update_actual_store()', 'Updating Key: {} Value: {}'.format(uri, value))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri):
        self.agent.logger.info('__pop_actual_store()', 'Removing Key: {}'.format(uri))
        uri = '{}/{}'.format(self.agent.ahome, uri)
        self.agent.astore.remove(uri)
