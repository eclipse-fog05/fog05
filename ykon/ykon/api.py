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

import json
import traceback
import ykon
from os.path import join




class API:
    def __init__(self, component, path):
        """
        Component is used to retrieve the connection to YAKS
        Path is used to determine the destination component
        """
        assert isinstance(component, ykon.Component)
        self.component = component
        self.path = path
        self.eval = {}


    def define(self, func, param = {}):
        """
        Define an API for the component given a function name and keywords
        parameters. This allows to call api.func() from external components.
        """
        def fb(param):
            def wrapper(*args, **kwargs):
                # Check if all the provided arguments are supported by the API
                check = [k for k in kwargs.keys() if k not in param]
                if check:
                    raise TypeError("{}() got {} unexpected keyword argument{}: '{}'" % \
                            (func, len(check), 's' if len(check) > 1 else '', ','.join(check)))
                # Check if all the mandatory keyword arguments are provided
                check = [p for p in param.keys() if param[p] and p not in kwargs]
                if check:
                    raise TypeError("{}() missing {} required keyword argument{}: '{}'" % \
                            (func, len(check), 's' if len(check) > 1 else '', ','.join(check)))
                # Compute path and query parameters if any
                p = join(self.path, func)
                if kwargs:
                    query = '?(' + ';'.join(['{}={}'.format(k,json.dumps(v)) for k,v in kwargs.items()]) + ')'
                    p = p + query
                return self.component.yaks.eval(p)
            return wrapper
        # Add the API function to the API instance
        setattr(self, func, fb(param))
        p = join(self.path, func)
        self.eval[p] = func
        return getattr(self, func)


    def register(self):
        """
        Register all the component's APIs.
        """
        def not_implemented(self):
            return ['Not implemented']

        for path,func in self.eval.items():
            self.component.log.info('Registering API: {}'.format(path))
            if hasattr(self.component, func):
                self.component.yaks.register_eval(path, getattr(self.component, func))
            else:
                self.component.log.warning('API not implemented: {}'.format(func))
                self.component.yaks.register_eval(path, not_implemented)


    def unregister(self):
        """
        Unregister all the component's APIs.
        """
        for path,func in self.eval.items():
            self.component.log.info('Unregistering API: {}'.format(path))
            self.component.yaks.unregister_eval(path)
