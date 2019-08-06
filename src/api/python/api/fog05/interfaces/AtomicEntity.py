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
# Atomic Entity Parsers and Python Class


import json
from fog05_im import user_atomic_entity
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.serialise import pybindJSONEncoder
from collections import OrderedDict
from fog05.interfaces.FDU import FDU


class AtomicEntity(object):

    def __init__(self, data=None):
        '''

        Constructor for the FDU Descriptor
        :param data dictionary containing the FDU descriptor

        :return the FDU object

        '''

        self.ae = user_atomic_entity.user_atomic_entity()
        self.encoder = pybindJSONEncoder()
        self.id = None
        self.uuid = None
        self.name = None
        self.description = None
        self.fdus = []
        self.internal_virtual_links = []
        self.connection_points = []
        self.depends_on = []
        if data is not None:
            pybindJSONDecoder.load_ietf_json({'ae_descriptor':data}, None, None, obj=self.ae)
            self.enforce()

            self.id = self.ae.ae_descriptor.id
            self.name = data.get('name')
            self.description = data.get('description')
            self.uuid = data.get('uuid', None)
            self.fdus = [FDU(x) for x in data.get('fdus')]
            self.internal_virtual_links = data.get('internal_virtual_links')
            self.connection_points = data.get('connection_points')
            self.depends_on = data.get('depends_on')



    def enforce(self):
        if self.ae.ae_descriptor.id == '':
            raise ValueError('AtomicEntity.ID cannot be empty')

        if self.ae.ae_descriptor.name == '':
            raise ValueError('AtomicEntity.Name cannot be empty')

        if len (self.ae.ae_descriptor.fdus) == 0:
            raise ValueError('AtomicEntity.FDUS cannot be empty')

    def to_json(self):
        data = {
            'uuid': self.uuid,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'fdus': [x.to_json() for x in self.fdus],
            'internal_virtual_links': self.internal_virtual_links,
            'connection_points': self.connection_points,
            'depends_on': self.depends_on,
        }
        check_obj = user_atomic_entity.user_atomic_entity()
        pybindJSONDecoder.load_ietf_json({'ae_descriptor':data}, None, None, obj=check_obj)
        return data

    def get_uuid(self):
        return self.uuid

    def set_uuid(self, uuid) :
        self.uuid = uuid

    def get_id(self):
        return self.id

    def set_id(self, id) :
        self.id = id

    def get_description(self):
        return self.description

    def set_description(self, description) :
        self.description = description

    def get_name(self):
        return self.name

    def set_name(self, name) :
        self.name = name

    def get_connection_points(self):
        return self.connection_points

    def set_connection_points(self, connection_points) :
        self.connection_points = connection_points

    def get_depends_on(self):
        return self.depends_on

    def set_depends_on(self, depends_on) :
        self.depends_on = depends_on


    def set_internal_virtual_links(self, virtual_links):
        self.internal_virtual_links = virtual_links

    def get_internal_virtual_links(self):
        return self.internal_virtual_links

    def set_fdus(self, fdus):
        self.fdus = fdus

    def get_fdus(self):
        return self.fdus

    def __str__(self):
        return "Name : {} ID: {} UUID: {}".format(self.name, self.id, self.uuid)
