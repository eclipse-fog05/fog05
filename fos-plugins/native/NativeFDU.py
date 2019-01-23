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
from fog05.interfaces.FDU import FDU

# TBD an FDU can be instantiated only once, ad is mapped to one or more
# atomic entities, meaning that to have more instances of the same
# atomic entity fog05 has to instantiate multiple FDUs


class NativeFDU(FDU):
    def __init__(self, uuid, name, command, source, args, outfile):
        super(NativeFDU, self).__init__()
        self.uuid = uuid
        self.name = name
        self.command = command
        self.args = args
        self.outfile = outfile
        self.pid = -1
        self.source_url = source
        self.process = None
        # self.source = ''
        # self.outfile = ''

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
        raise RuntimeError('Cannot migrate Native')

    def before_migrate(self):
        raise RuntimeError('Cannot migrate Native')

    def __str__(self):
        s = 'UUID {} Name {} Command {} ARGS {} OUTFILE {} PID {} SOURCE {}' \
            ' PROCESS {}'.format(
                self.uuid, self.name, self.command, self.args,
                self.outfile, self.pid, self.source_url, self.process)
        return s
