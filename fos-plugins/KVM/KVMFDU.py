
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


class KVMFDU(FDU):

    # , cpu, ram, disk_size, networks, image, user_file, ssh_key):
    def __init__(self, uuid, name, disk, cdrom, networks, user_file, ssh_key, flavor_id, image_id):

        super(KVMFDU, self).__init__()
        self.uuid = uuid
        self.name = name
        self.disk = disk
        self.cdrom = cdrom
        self.networks = networks
        self.user_file = user_file
        self.ssh_key = ssh_key
        self.image_id = image_id
        self.flavor_id = flavor_id
        self.xml = None
        self.state = State.DEFINED

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
        pass

    def before_migrate(self):
        pass

    def after_migrate(self):
        pass

    def set_user_file(self, user_file):
        self.user_file = user_file

    def set_ssh_key(self, ssh_key):
        self.ssh_key = ssh_key

    def set_networks(self, networks):
        self.networks = networks

    def on_defined(self):
        self.state = State.DEFINED
