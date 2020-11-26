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
from fog05.interfaces.States import State

from fog05.interfaces.EntityInstance import EntityInstance

class NativeEntityInstance(EntityInstance):
    def __init__(self, uuid, name, command, source, args, outfile, entity_uuid):
        super(NativeEntityInstance, self).__init__(uuid, entity_uuid)
        self.uuid = uuid
        self.name = name
        self.command = command
        self.args = args
        self.outfile = outfile
        self.pid = -1
        self.source = source
        self.process = None

    def on_configured(self):
        self.state = State.CONFIGURED

    def on_clean(self):
        self.state = State.DEFINED

    def on_start(self, pid, process):
        self.pid = pid
        self.process = process
        self.state = State.RUNNING

    def on_stop(self):
        self.pid = -1
        self.process = None
        self.state = State.CONFIGURED

    def on_pause(self):
        self.state = State.PAUSED

    def on_resume(self):
        self.state = State.RUNNING

    def after_migrate(self):
        raise Exception('Cannot migrate Native')

    def before_migrate(self):
        raise Exception('Cannot migrate Native')
