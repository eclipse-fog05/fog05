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
import datetime

from os.path import join
from uuid import uuid4,UUID




class Component(object):
    def __init__(self, endpoint, name,
            package = None, uuid = None,
            type = None, version = None):
        # Set name
        self.name = name
        # Set component's package
        self.package = 'ykon' if package is None else package
        # Set component's uuid
        self.uuid = uuid4() if uuid is None else UUID(uuid)
        # Set component's type
        self.type = 'default' if type is None else type
        # Set component's version
        self.version = '0.0.1' if version is None else version
        # Set component's path
        self.path = ykon.path.component.format(**{'package': self.package, 'name': self.name, 'uuid': self.uuid}).lower()
        # Set component's logger
        self.log = ykon.Logger(self.name, str(self.uuid))
        # Set component's yaks
        self.yaks = ykon.YaksWrapper(self, endpoint)
        # Set component's API
        self.api = ykon.API(self, self.path)
        # Set component's handle
        self.handle = ykon.Handle(self)
        # Set component's announce
        self.announce = ykon.Announce(self)
        # Set component's subscription
        self.subscription = ykon.Subscription(self)
        # Set component's peer
        self.peer = ykon.Peer(self)
        # Store the component's status
        self.isconnected = False
        self.isregistered = False
        # Log successful creation
        self.log.info('Created and ready to start')

    def _connect(self):
        """
        Connect the component to YAKS and execute additional code (if any)
        """
        self.log.debug('Connect: starting')
        self.yaks.connect()
        for func in self.handle.connect:
            func()
        self.isconnected = True
        self.log.debug('Connect: complete')

    def _disconnect(self):
        """
        Disconnect the component from YAKS and execute additional code (if any)
        """
        self.log.debug('Disconnect: starting')
        for func in self.handle.disconnect:
            func()
        self.yaks.disconnect()
        self.isconnected = False
        self.log.debug('Disconnect: complete')

    def _info(self):
        """
        Provides the basic and additional information on the component.
        Basic information:
            path: /<component's path/<component's uuid/
            uuid: e6f5fcae-35dd-480d-996a-630021de46f1
            version: 1.0.0
            timestamp: 2019-02-20T17:07:56.402719
                the timestamp is provided in ISO format
        """
        i = {}
        for func in self.handle.info:
            i = {**i, **func()}
        i['interval'] = str(self.announce.interval)
        i['name'] = str(self.name)
        i['path'] = str(self.path)
        i['timestamp'] = str(datetime.datetime.utcnow().isoformat())
        i['type'] = str(self.type)
        i['uuid'] = str(self.uuid)
        i['version'] = str(self.version)
        return i

    def _peer_del(self, path, value, event):
        """
        Execute additional code when a peer disappears
        """
        for func in self.handle.peer_del:
            func(path, value, event)

    def _peer_new(self, path, value, event):
        """
        Execute additional code when a peer is found
        """
        for func in self.handle.peer_new:
            func(path, value, event)

    def _peer_upd(self, path, value, event):
        """
        Execute additional code when a peer is updated
        """
        for func in self.handle.peer_upd:
            func(path, value, event)

    def _register(self):
        """
        Register the component and execute additional code (if any)
        """
        self.log.debug('Register: starting')
        # Register the component's API
        self.api.register()
        # Register the peer
        self.peer.register()
        # Start announcing the component
        self.announce.register()
        # Execute addictional code if any
        for func in self.handle.register:
            func()
        # Set the status to registered
        self.isregistered = True
        self.log.debug('Register: complete')

    def _unregister(self):
        """
        Unregister the component and execute additional code (if any)
        """
        self.log.debug('Unregister: starting')
        # Execute addictional code if any
        for func in self.handle.unregister:
            func()
        # Stop the advertisement
        self.announce.unregister()
        # Stop the peers
        self.peer.unregister()
        # Cancel the subscriptions
        self.subscription.unregister()
        # Unregister the component's API
        self.api.unregister()
        # Set the status to unregistered
        self.isregistered = False
        self.log.debug('Unregister: complete')

    ############################################################################
    def start(self):
        """
        Start the component by executing the following actions in order:
        1) Connect to YAKS
        2) Enable the component and subscribe to the default subscriptions
           Register the component's APIs and start announcing the component
        """
        self._connect()
        self._register()
        self.announce.start()

    def stop(self):
        """
        Stop the component by executing the following actions in order:
        1) Stop announcing the component unregister the component's APIs
           Disable the component and unsubscribe from all the subscriptions
        2) Disconnect from YAKS
        """
        self.announce.stop()
        self._unregister()
        self._disconnect()
