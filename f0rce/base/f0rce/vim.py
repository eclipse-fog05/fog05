# Copyright (c) 2014,2019 Contributors to the Eclipse Foundation
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
# Contributors: Luca Cominardi, University Carlos III of Madrid.

import f0rce
import ykon


_api = [
        ('O4onboard', {'entity': True, 'instance': True}),
        ('O4offload', {'entity': True, 'instance': True}),
        ('O4instantiate', {'entity': True, 'instance': True}),
        ('O4terminate', {'entity': True, 'instance': True}),
    ]


class API(ykon.API):
    def __init__(self, component, path):
        super().__init__(component, path)
        for a in _api:
            self.define(a[0], a[1])


class VIMconnector(ykon.Component):
    def __init__(self, endpoint, name, uuid = None, domain = 'default'):
        super().__init__(endpoint,
                name = name,
                uuid = uuid,
                package = 'f0rce',
                type = f0rce.enum.ComponentCode.VIM.name,
                version = '0.0.1')
        # Add the API
        for a in _api:
            self.api.define(a[0], a[1])
        # Add the handles
        self.handle.info.append(self.VIMinfo)
        self.handle.peer_del.append(self.VIMpeer_del)
        self.handle.peer_new.append(self.VIMpeer_new)
        self.handle.register.append(self.VIMregister)
        self.handle.unregister.append(self.VIMunregister)
        # The O4 interface
        self.O4domain = domain
        self.O4network = f0rce.Network(self, self.O4domain)
        self.O4stack = f0rce.Stack(self, self.O4domain)
        # The list of Orchestrator peers
        self.orc = {}

    # Handles begin
    def VIMinfo(self):
        """
        Add the VIM-specific information
        """
        return {'domain': self.O4domain}

    def VIMpeer_del(self, path, value, event):
        if 'domain' not in value or 'type' not in value:
            return
        if value['domain'] != self.name:
            return
        if value['type'] == f0rce.enum.ComponentCode.ORC.name and value['domain'] in self.orc:
            self.log.info('Deleting ORC...')
            del self.orc[value['domain']]

    def VIMpeer_new(self, path, value, event):
        if 'domain' not in value or 'type' not in value:
            return
        if value['domain'] != self.O4domain:
            return
        if value['type'] == f0rce.enum.ComponentCode.ORC.name and value['domain'] not in self.orc:
            self.log.info('Adding ORC...')
            self.orc[value['domain']] = f0rce.orchestrator.API(self, value['path'])

    def VIMregister(self):
        """
        Announce the VIM and subscribe to Orchestrator advertisments
        """
        self.O4network.register()
        self.O4stack.register()

    def VIMunregister(self):
        """
        Unregister the network
        """
        self.O4network.unregister()
        self.O4stack.unregister()
    # Handles end
