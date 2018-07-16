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

class Agent(object):

    def __init__(self, uuid):
        self.uuid = uuid

    def __load_os_plugin(self):
        raise NotImplementedError

    def __load_runtime_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def refresh_plugins(self):
        raise NotImplementedError

    def __load_network_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def __load_monitoring_plugin(self, plugin_name, plugin_uuid):
        raise NotImplementedError

    def get_os_plugin(self):
        raise NotImplementedError

    def get_runtime_plugin(self, runtime_uuid):
        raise NotImplementedError

    def get_network_plugin(self, cnetwork_uuid):
        raise NotImplementedError

    def list_runtime_plugins(self):
        raise NotImplementedError
    
    def list_network_plugins(self):
        raise NotImplementedError

