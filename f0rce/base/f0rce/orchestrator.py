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
        ('Oo1onboard', {'entity': True}),
        ('Oo1offload', {'entity': True}),
        ('Oo1instantiate', {'entity': True}),
        ('Oo1terminate', {'entity': True}),
        ('Oo1list', {}),
    ]

class API(ykon.API):
    def __init__(self, component, path):
        super().__init__(component, path)
        for a in _api:
            self.define(a[0], a[1])




class Orchestrator(ykon.Component):
    def __init__(self, endpoint, name, uuid = None, domain = []):
        super().__init__(endpoint,
                name = name,
                uuid = uuid,
                package = 'f0rce',
                type = f0rce.enum.ComponentCode.ORC.name,
                version = '0.0.1')
        # Add the API on YKON
        for a in _api:
            self.api.define(a[0], a[1])
        # Add the YKON handles
        self.handle.info.append(self.ORCinfo)
        self.handle.peer_del.append(self.ORCpeer_del)
        self.handle.peer_new.append(self.ORCpeer_new)
        self.handle.register.append(self.ORCregister)
        self.handle.unregister.append(self.ORCunregister)
        # The  domains
        self.domain = domain
        self.network = {dom:f0rce.Network(self, dom) for dom in self.domain}
        self.stack = {dom:f0rce.Stack(self, dom) for dom in self.domain}
        # The list of peers
        self.vim = {}
        self.lcm = {}

    # Handles begin
    def ORCinfo(self):
        """
        Add the VIM-specific information
        """
        # TO FIX
        return {'domain': self.domain[0]}

    def ORCpeer_del(self, path, value, event):
        if 'domain' not in value or 'type' not in value:
            return
        if value['domain'] not in self.domain:
            return
        if value['type'] == f0rce.enum.ComponentCode.VIM.name and value['domain'] in self.vim:
            self.log.info('Deleting VIM...')
            del self.vim[value['domain']]
        if value['type'] == f0rce.enum.ComponentCode.LCM.name and value['domain'] in self.lcm:
            self.log.info('Deleting LCM...')
            del self.lcm[value['domain']]

    def ORCpeer_new(self, path, value, event):
        if 'domain' not in value or 'type' not in value:
            return
        if value['domain'] not in self.domain:
            return
        if value['type'] == f0rce.enum.ComponentCode.VIM.name and value['domain'] not in self.vim:
            self.log.info('Adding VIM...')
            self.vim[value['domain']] = f0rce.vim.API(self, value['path'])
        if value['type'] == f0rce.enum.ComponentCode.LCM.name and value['domain'] not in self.lcm:
            self.log.info('Adding LCM...')
            self.lcm[value['domain']] = f0rce.lcm.API(self, value['path'])

    def ORCregister(self):
        """
        Get available network upon registration
        """
        for n in self.network.values():
            n.register()
        for s in self.stack.values():
            s.register()

    def ORCunregister(self):
        """
        Remove associated nodes and links upon unregistration
        """
        #for n in self.network.values():
        #    n.unregister()
        #for s in self.stack.values():
        #    s.register()
        pass
    # Handles end
