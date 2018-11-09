# Copyright (c) 2018 ADLINK Technology Inc.
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

class MEAO(ResourceOrchestratorPlugin):

    def __init__(self, name, version, agent, plugin_uuid, configuration={}):
        super(MEAO, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.configuration = configuration
        self.__services = {}
        self.__platform_managers = {}
        self.agent.logger.info('__init__()', ' Hello from 5GCity MEAO Plugin')

        '''
        should listen on:
        
        - //dfos/MEAO/platforms/**
        - //dfos/meao/mecapp/**
        - //dfos/MEAO/platform/*/services/*/configuration
        
        '''

        uri = '//dfos/meao/platforms/**'
        self.agent.dstore.observe(uri, self.__react_to_platforms_services)
        self.agent.logger.info(
            'startRuntime()', '5GCity MEAO Plugin - Observing {}'.format(uri))
        uri = '//dfos/meao/mecapp/**'
        self.agent.dstore.observe(uri, self.__react_to_mecapp)
        self.agent.logger.info(
            'startRuntime()', '5GCity MEAO Plugin - Observing {}'.format(uri))

        uri = '//afos/meao'
        data = {'name': configuration.get('name')}
        self.agent.astore.put(uri, json.dumps(data))

    def onboard_application(self, application_uuid, application_manifest):
        pass

    def offload_application(self, application_uuid):
        pass

    def __react_to_platforms_services(self, uri, value, v):
        if uri.split('/')[-2] == 'platform':
            value = json.loads(value)
            uuid = uri.split('/')[-1]
            self.__platform_managers.update({uuid: value})
            uri = '//afos/meao/platform/{}'.format(uuid)
            self.__update_actual_store(uri, json.dumps(value))
        elif uri.split('/')[-2] == 'services':
            if uri.split('/')[-1] == 'configuration':
                service_uuid = uri.split('/')[-2]
                platform_uuid = uri.split('/')[-4]
                print('~~~~~~~~~~~~~~ [MEAO] I should configure service {} on {} with {}'.format(
                    service_uuid, platform_uuid, value))
                uri = '//afos/meao/platform/{}/services/{}/configuration'.format(
                    platform_uuid, service_uuid)
                self.__update_actual_store(uri, json.dumps(value))
            else:
                value = json.loads(value)
                service_uuid = uri.split('/')[-1]
                platform_uuid = uri.split('/')[-3]
                self.__services.update({service_uuid: value})
                uri = '//afos/meao/platform/{}/services/{}'.format(
                    platform_uuid, service_uuid)
                self.__update_actual_store(uri, json.dumps(value))

        pass

    def __react_to_mecapp(self, uri, value, v):
        value = json.loads(value)
        pass

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
        self.agent.logger.info('__pop_actual_store()',
                               'Removing Key: {}'.format(uri))
        uri = '{}/{}'.format(self.agent.ahome, uri)
        self.agent.astore.remove(uri)
