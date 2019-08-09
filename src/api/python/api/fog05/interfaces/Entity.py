# Copyright (c) 2014,2019 Contributors to the Eclipse Foundation
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
# Entity Parsers and Python Class


import json
from fog05_im import user_entity
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.serialise import pybindJSONEncoder
from collections import OrderedDict


class Entity(object):

    def __init__(self, data=None):
        '''

        Constructor for the FDU Descriptor
        :param data dictionary containing the FDU descriptor

        :return the FDU object

        '''

        self.e = user_entity.user_entity()
        self.encoder = pybindJSONEncoder()
        self.id = None
        self.uuid = None

        self.atomic_entities = []
        self.virtual_links = []
        if data is not None:
            pybindJSONDecoder.load_ietf_json({'entity_descriptor':data}, None, None, obj=self.e)
            self.enforce()

            self.id = self.e.entity_descriptor.id
            self.name = data.get('name')
            self.description = data.get('description')
            self.uuid = data.get('uuid', None)
            self.atomic_entities = data.get('atomic_entities')
            self.virtual_links = data.get('virtual_links')


    def enforce(self):
        if self.e.entity_descriptor.id == '':
            raise ValueError('Entity.ID cannot be empty')

        if self.e.entity_descriptor.name == '':
            raise ValueError('Entity.Name cannot be empty')

        if len (self.e.entity_descriptor.atomic_entities) == 0:
            raise ValueError('Entity.atomic_entities cannot be empty')

    def to_json(self):
        data = {
            'uuid': self.uuid,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'atomic_entities': self.atomic_entities,
            'virtual_links': self.virtual_links
        }
        check_obj = user_entity.user_entity()
        pybindJSONDecoder.load_ietf_json({'entity_descriptor':data}, None, None, obj=check_obj)
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

    def set_virtual_links(self, virtual_links):
        self.virtual_links = virtual_links

    def get_virtual_links(self):
        return self.virtual_links

    def set_atomic_entities(self, atomic_entities):
        self.atomic_entities = atomic_entities

    def get_atomic_entities(self):
        return self.atomic_entities

    def __str__(self):
        return "Name : {} ID: {} UUID:{}".format(self.name, self.id, self.uuid)
