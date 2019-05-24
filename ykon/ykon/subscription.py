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
import json
import threading

from abc import ABC
from os.path import join
from uuid import uuid4,UUID
from yaks import Yaks, Value, Encoding




class Subscription:
    def __init__(self, component):
        assert isinstance(component, ykon.Component)
        self.component = component
        self.subscription = {}


    def unregister(self):
        """
        Remove all the active subscriptions.
        """
        for path in list(self.subscription.keys()):
            self.remove(path)


    def add(self, path, func):
        """
        Add a subscription given a path and a callback function.
        """
        if path in self.subscription:
            func = self.subscription[path][0]
            self.component.log.warning('Overriding existing subscription: {} {}'.format(path, func.__name__))
        self.component.log.info('Subscribing: {}'.format(path))
        sid = self.component.yaks.subscribe(path, func)
        self.subscription[path] = (func, sid)
        return sid


    def remove(self, path):
        """
        Remove a subscription given a path.
        """
        if path not in self.subscription:
            self.component.log.error('Subscription not existing: {}'.format(path))
            return
        func, sid = self.subscription[path][0], self.subscription[path][1]
        self.component.log.debug('Unsubscribing: {} {}'.format(path, func.__name__))
        r = self.component.yaks.unsubscribe(sid)
        del self.subscription[path]
        return r
