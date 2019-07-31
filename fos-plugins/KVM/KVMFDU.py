
# Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set

import sys
import os
import json
from fog05.interfaces.States import State
from fog05.interfaces.InfraFDU import InfraFDU


class KVMFDU(InfraFDU):

    def __init__(self, data):
        super(KVMFDU, self).__init__(data)
        self.xml = None
        self.cdrom = None
        self.disk = None
        self.name = 'v{}'.format(self.uuid)

    def on_defined(self):
        self.set_status(State.DEFINED)

    def on_configured(self, configuration):
        self.xml = configuration
        self.set_status(State.CONFIGURED)

    def on_clean(self):
        self.set_status(State.DEFINED)

    def on_start(self):
        self.set_status(State.RUNNING)

    def on_stop(self):
        self.set_status(State.CONFIGURED)

    def on_pause(self):
        self.set_status(State.PAUSED)

    def on_resume(self):
        self.set_status(State.RUNNING)

    def before_migrate(self):
        pass

    def after_migrate(self):
        pass
