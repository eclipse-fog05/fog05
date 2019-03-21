
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
from fog05.interfaces.FDU import FDU


class KVMFDU(FDU):

    def __init__(self, uuid, name, interfaces, connection_points, image,
                 comp_requirements, configuration, ssh_key):

        super(KVMFDU, self).__init__()
        self.uuid = uuid
        self.name = name
        self.interfaces = interfaces
        self.cps = connection_points
        self.image = image
        self.configuration = configuration
        self.ssh_key = ssh_key
        self.comp_requirements = comp_requirements
        self.xml = None
        self.cdrom = None
        self.disk = None

    @staticmethod
    def from_descriptor(desciptor):
        fdu = KVMFDU(desciptor.get('uuid'),
                     desciptor.get('name'),
                     desciptor.get('interfaces'),
                     desciptor.get('connection_points'),
                     desciptor.get('image'),
                     desciptor.get('computation_requirements'),
                     desciptor.get('configuration'),
                     desciptor.get('ssh-key'))
        return fdu

    @staticmethod
    def to_descriptor(fdu):
        d = {
            'name': fdu.name,
            'uuid': fdu.uuid,
            'computation_requirements': json.dumps(fdu.comp_requirements),
            'base_image': json.dumps(fdu.image),
            'hypervisor_type': 'KVM',
            'interfaces': json.dumps(fdu.interfaces),
            'connection_points': json.dumps(fdu.cps)
        }
        return d

    def on_define(self):
        self.state = State.DEFINED

    def on_configured(self, configuration):
        self.xml = configuration
        self.state = State.CONFIGURED

    def on_start(self):
        self.state = State.RUNNING

    def on_stop(self):
        self.state = State.CONFIGURED

    def on_pause(self):
        self.state = State.PAUSED

    def on_resume(self):
        self.state = State.RUNNING

    def on_clean(self):
        self.state = State.DEFINED

    def before_migrate(self):
        pass

    def after_migrate(self):
        pass

    def on_defined(self):
        self.state = State.DEFINED
