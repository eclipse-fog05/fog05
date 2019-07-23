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
# OCaml implementation and API


import json
from fog05.interfaces.States import State
from fog05_im import user_fdu
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.serialise import pybindJSONEncoder
from collections import OrderedDict


class FDU(object):

    def __init__(self, data=None):
        '''

        Constructor for the FDU Descriptor
        :param data dictionary containing the FDU descriptor

        :return the FDU object

        '''

        self.fdu = user_fdu.user_fdu()
        self.encoder = pybindJSONEncoder()
        if data is not None:
            # data = json.loads(data)
            data = {'fdu_descriptor':data}
            pybindJSONDecoder.load_ietf_json(data, None, None, obj=self.fdu)
            self.enforce()

    def enforce(self):
        if self.fdu.fdu_descriptor.id == '':
            raise ValueError('FDU.ID cannot be empty')

        if self.fdu.fdu_descriptor.name == '':
            raise ValueError('FDU.Name cannot be empty')

        if self.fdu.fdu_descriptor.computation_requirements.cpu_arch == '':
            raise ValueError('FDU.Computation_Requirements.CPU_Arch cannot be empty')

        if self.fdu.fdu_descriptor.hypervisor == '':
            raise ValueError('FDU.Hypervisor cannot be empty')

        if self.fdu.fdu_descriptor.migration_kind == '':
            raise ValueError('FDU.Migration_Kind cannot be empty')

    def to_json(self):
        data = self.encoder.encode(self.fdu)
        data = json.loads(data)
        return data['fdu_descriptor']

    def get_uuid(self):
        return self.fdu.fdu_descriptor.uuid

    def set_uuid(self, uuid):
        self.fdu.fdu_descriptor.uuid = uuid

    def get_id(self):
        return self.fdu.fdu_descriptor.id

    def get_name(self):
        return self.fdu.fdu_descriptor.name

    def get_image_uri(self):
        return self.fdu.fdu_descriptor.base_image.uri

    def get_image_checksum(self):
        return self.fdu.fdu_descriptor.base_image.checksum

    def get_image_format(self):
        return self.fdu.fdu_descriptor.base_image.format

    def get_interfaces(self):
        return self.fdu.fdu_descriptor.interfaces

    def get_connection_points(self):
        return self.fdu.fdu_descriptor.connection_points

    def __str__(self):
        return "Name : {} ID: {}".format(self.fdu.fdu_descriptor.name, self.fdu.fdu_descriptor.id)
