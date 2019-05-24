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

import ykon
import threading
from os.path import join
from uuid import UUID




class Peer:
    def __init__(self, component):
        assert isinstance(component, ykon.Component)
        self.component = component
        self.type = {}
        self.__timer = {}

    def __alive(self, value):
        type = value['type']
        uuid = str(UUID(value['uuid']))
        if uuid == str(self.component.uuid):
            return
        if uuid in self.__timer:
            self.__timer[uuid].cancel()
        timeout = 3.5 * float(value['interval'])
        #self.__timer[uuid] = threading.Timer(timeout, self.__leave, [value, 'Timeout'])
        #self.__timer[uuid].start()

    def __announce(self, path, value, event):
        if not value or not event:
            return
        type = value['type']
        uuid = str(UUID(value['uuid']))
        if uuid == str(self.component.uuid):
            return
        if type not in self.type:
            self.type[type] = {}
        if uuid not in self.type[type]:
            self.type[type][uuid] = value
            self.component.log.info('Peer discovered: {}'.format(value))
            self.component._peer_new(path, value, event)
        self.__alive(value)

    def __leave(self, path, value, event):
        if not value or not event:
            return
        type = value['type']
        uuid = str(UUID(value['uuid']))
        if uuid == str(self.component.uuid):
            return
        if uuid in self.__timer:
            self.__timer[uuid].cancel()
            del self.__timer[uuid]
        if type in self.type and uuid in self.type[type]:
            del self.type[type][uuid]
            self.component.log.info('Peer disconnected: {}'.format(value))
            if len(self.type[type]) == 0:
                del self.type[type]
        self.component._peer_del(path, value, event)

    def register(self):
        self.component.subscription.add(ykon.path.announce.format(**{'package': self.component.package}), self.__announce)
        self.component.subscription.add(ykon.path.leave.format(**{'package': self.component.package}), self.__leave)

    def unregister(self):
        for t in list(self.type.keys()):
            for value in list(self.type[t].values()):
                self.__leave(path = '', value = value, event = 'Unregister')
