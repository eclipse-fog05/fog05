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
from fog05_im import infra_entity
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.serialise import pybindJSONEncoder
from collections import OrderedDict


class EntityRecord(object):

    def __init__(self, data=None):
        '''

        Constructor for the FDU Descriptor
        :param data dictionary containing the FDU descriptor

        :return the FDU object

        '''

        self.e = infra_entity.infra_entity()
        self.encoder = pybindJSONEncoder()
        self.entity_id = None
        self.uuid = None
        self.atomic_entities = []
        self.virtual_links = []
        self.connection_points = []
        if data is not None:
            pybindJSONDecoder.load_ietf_json({'entity_record':data}, None, None, obj=self.e)
            self.enforce()

            self.entity_id = self.e.entity_record.entity_id
            self.uuid =  self.e.entity_record.uuid
            self.atomic_entities = data.get('atomic_entities')
            self.virtual_links = data.get('virtual_links')
            self.connection_points = data.get('connection_points')


    def enforce(self):
        if self.e.entity_record.id == '':
            raise ValueError('EntityRecord.ID cannot be empty')

        if self.e.entity_record.uuid == '':
            raise ValueError('EntityRecord.UUID cannot be empty')

        if len (self.e.entity_record.atomic_entities) == 0:
            raise ValueError('EntityRecord.atomic_entities cannot be empty')

    def to_json(self):
        data = {
            'uuid': self.uuid,
            'entity_id': self.entity_id,
            'atomic_entities': self.atomic_entities,
            'virtual_links': self.virtual_links,
            'connection_points': self.connection_points
        }
        check_obj = infra_entity.infra_entity()
        pybindJSONDecoder.load_ietf_json({'entity_record':data}, None, None, obj=check_obj)
        return data

    def get_uuid(self):
        return self.uuid

    def set_uuid(self, uuid) :
        self.uuid = uuid

    def get_entity_id(self):
        return self.entity_id

    def set_entity_id(self, entity_id) :
        self.entity_id = entity_id

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
        return "UUID : {} Entity ID: {}".format(self.uuid, self.entity_id)
