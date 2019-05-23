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
    ]


class API(ykon.API):
    def __init__(self, component, path):
        super().__init__(component, path)
        for a in _api:
            self.define(a[0], a[1])


class LCMconnector(ykon.Component):
    def __init__(self, endpoint, name, uuid = None, domain = 'default'):
        super().__init__(endpoint,
                name = name,
                uuid = uuid,
                package = 'f0rce',
                type = f0rce.enum.ComponentCode.LCM.name,
                version = '0.0.1')
        # Add the API
        for a in _api:
            self.api.define(a[0], a[1])
        # Add the handles
        self.handle.info.append(self.LCMinfo)
        self.handle.peer_del.append(self.LCMpeer_del)
        self.handle.peer_new.append(self.LCMpeer_new)
        self.handle.register.append(self.LCMregister)
        self.handle.unregister.append(self.LCMunregister)
        # The  interface
        self.domain = domain
        self.stack = f0rce.Stack(self, self.domain)
        # The list of Orchestrator peers
        self.orc = {}

    # Handles begin
    def LCMinfo(self):
        """
        Add the LCM-specific information
        """
        return {'domain': self.domain}

    def LCMpeer_del(self, path, value, event):
        if 'domain' not in value or 'type' not in value:
            return
        if value['domain'] != self.domain:
            return
        if value['type'] == f0rce.enum.ComponentCode.ORC.name and value['domain'] in self.orc:
            self.log.info('Deleting ORC...')
            del self.orc[value['domain']]

    def LCMpeer_new(self, path, value, event):
        if 'domain' not in value or 'type' not in value:
            return
        if value['domain'] != self.domain:
            return
        if value['type'] == f0rce.enum.ComponentCode.ORC.name and value['domain'] not in self.orc:
            self.log.info('Adding ORC...')
            self.orc[value['domain']] = f0rce.orchestrator.API(self, value['path'])

    def LCMregister(self):
        """
        Announce the LCM and subscribe to Orchestrator advertisments
        """
        self.stack.register()

    def LCMunregister(self):
        """
        Unregister the network
        """
        #self.stack.unregister()
        pass
    # Handles end
