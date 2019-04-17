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
    def __init__(self, uuid,fdu_uuid,node, status, accelerators, io_ports,
                 interfaces, connection_points, hypervisor_info, command):
        super(NativeFDU, self).__init__()
        self.uuid = uuid
        self.fdu_uuid = fdu_uuid
        self.node = node
        self.status = status
        self.accelerators = accelerators
        self.io_ports = io_ports
        self.interfaces = interfaces
        self.cps = connection_points
        self.hv_info = hypervisor_info
        self.error_code = 0
        self.error_msg = ''
        self.migration_properties = None
        self.image = None
        self.comp_requirements = None
        self.devices = None
        self.conf = None
        self.profiles = None
        self.configuration = None
        self.name = 'n{}'.format(uuid)

        self.command = None
        self.args = None

        self.command = command
        if command is not None:
            self.command = command.get('binary')
            self.args = command.get('args')

        self.outfile = None
        self.pid = -1
        self.process = None
        self.source = ''
        # self.outfile = ''

    @staticmethod
    def from_record(record):
        fdu = NativeFDU(record.get('uuid'),
                     record.get('fdu_uuid'),
                     record.get('node'),
                     record.get('status'),
                     record.get('accelerators'),
                     record.get('io_ports'),
                     record.get('interfaces'),
                     record.get('connection_points'),
                     record.get('hypervisor_info'),
                     record.get('command'))
        return fdu

    def set_command(self, command):
        self.command = command
        if command is not None:
            self.command = command.get('binary')
            self.args = command.get('args')


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
        s = 'UUID {} Name {} Command {} ARGS {} OUTFILE {} PID {}' \
            ' SOURCE {}'.format(self.uuid, self.name, self.command,
                                self.args, self.outfile, self.pid, self.image)
        return s
