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
import json
from yaks import Yaks, Value, Encoding




class YaksWrapper:
    def __init__(self, component, endpoint):
        assert isinstance(component, ykon.Component)
        self.endpoint = endpoint
        self.component = component
        self.yaks = None
        self.ws = None


    def connect(self):
        """
        Connect to YAKS
        """
        self.yaks = Yaks.login(self.endpoint)
        self.ws = self.yaks.workspace(self.component.path)
        self.component.log.info('Connected to YAKS: {}'.format(self.endpoint))


    def disconnect(self):
        """
        Disconnect from YAKS
        """
        if self.yaks:
            self.yaks.logout()
        self.yaks = None
        self.ws = None
        self.component.log.info('Disconnected from YAKS: {}'.format(self.endpoint))


    def eval(self, path):
        """
        Wrapper for YAKS's eval method
        """
        if self.ws:
            v = self.ws.eval(path)
            if v:
                v = json.loads(v[0][1].value)
            return v
        return None


    def get(self, path):
        """
        Wrapper for YAKS's get method
        """
        if self.ws:
            value = self.ws.get(path)
            return list(map(lambda x: (x[0], json.loads(x[1].value)), value))
        return None


    def publish(self, path, value):
        """
        Wrapper for YAKS's put method
        """
        if self.ws:
            return self.ws.put(path, Value(json.dumps(value), encoding = Encoding.STRING))
        return None


    def remove(self, path):
        """
        Wrapper for YAKS's remove method
        """
        if self.ws:
            return self.ws.remove(path)
        return None


    def subscribe(self, path, callback):
        """
        Wrapper for YAKS's subscribe method
        """
        def cb(vlist):
            for v in vlist:
                path = v[0]
                value = v[1].get_value()
                value = json.loads(value.value) if value else None
                event = v[1].get_kind()
                callback(path = path, value = value, event = event)
        if self.ws:
            return self.ws.subscribe(path, cb)
        return None


    def unsubscribe(self, sid):
        """
        Wrapper for YAKS's unsubscribe method
        """
        if self.ws:
            return self.ws.unsubscribe(sid)
        return None


    def register_eval(self, path, callback):
        """
        Wrapper for YAKS's register_eval method
        """
        def cb(path, **kwargs):
            return Value(json.dumps(callback(**kwargs)), encoding = Encoding.STRING)
        if self.ws:
            return self.ws.register_eval(path, cb)
        return None


    def unregister_eval(self, path):
        """
        Wrapper for YAKS's unregister_eval method
        """
        if self.ws:
            return self.ws.unregister_eval(path)
        return None
