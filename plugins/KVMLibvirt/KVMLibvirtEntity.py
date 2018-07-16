
# Copyright (c) 2014,2018 ADLINK Technology Inc.
# 
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
# 
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0
# 
# SPDX-License-Identifier: EPL-2.0
#
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set

import sys
import os

sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from fog05.interfaces.States import State
from fog05.interfaces.Entity import Entity


class KVMLibvirtEntity(Entity):

    def __init__(self, uuid, name, image_id, flavor_id):  # , cpu, ram, disk_size, networks, image, user_file, ssh_key):

        super(KVMLibvirtEntity, self).__init__()
        self.uuid = uuid
        self.name = name
        self.image_id = image_id
        self.flavor_id = flavor_id

        self.user_file = None
        self.ssh_key = None
        self.networks = []

    def set_user_file(self, user_file):
        self.user_file = user_file

    def set_ssh_key(self, ssh_key):
        self.ssh_key = ssh_key

    def set_networks(self, networks):
        self.networks = networks

    def on_defined(self):
        self.state = State.DEFINED

