# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc.
# Initial implementation and API


import sys
import os
from fog05.interfaces.Plugin import Plugin


class MonitoringPlugin(Plugin):

    def __init__(self, version, plugin_uuid=None):
        super(MonitoringPlugin, self).__init__(version, plugin_uuid)
        self.name = ''

    def start_monitoring(self):
        '''
        start the runtime
        :return: runtime pid or runtime uuid?
        '''
        raise NotImplementedError('This is and interface!')

    def stop_monitoring(self):
        '''
        stop this runtime
        '''
        raise NotImplementedError('This is and interface!')
