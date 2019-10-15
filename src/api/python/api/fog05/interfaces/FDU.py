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

        Parameters
        ----------
        data : dictionary
            optional dictionart containing the FDU descriptor

        returns
        -------
        FDU

        '''

        self.fdu = user_fdu.user_fdu()
        self.encoder = pybindJSONEncoder()
        self.id = None
        self.uuid = None
        self.name = None
        self.description = None
        self.image = {}
        self.command = {}
        self.storage = []
        self.computation_requirements = {}
        self.geographical_requirements = {}
        self.energy_requirements = {}
        self.hypervisor = None
        self.migration_kind = None
        self.configuration = {}
        self.interfaces = []
        self.io_ports = []
        self.connection_points = []
        self.depends_on = []
        if data is not None:
            pybindJSONDecoder.load_ietf_json({'fdu_descriptor':data}, None, None, obj=self.fdu)
            self.enforce()

            self.id = self.fdu.fdu_descriptor.id
            self.uuid = data.get('uuid', None)
            self.image = data.get('image', None)
            self.command = data.get('command', None)
            self.name =  data.get('name')
            self.description =  data.get('description', None)
            self.storage = data.get('storage')
            self.computation_requirements = data.get('computation_requirements')
            self.geographical_requirements = data.get('geographical_requirements', None)
            self.energy_requirements = data.get('energy_requirements', None)
            self.hypervisor = data.get('hypervisor')
            self.migration_kind = data.get('migration_kind')
            self.configuration = data.get('configuration', None)
            self.interfaces = data.get('interfaces')
            self.io_ports = data.get('io_ports')
            self.connection_points = data.get('connection_points')
            self.depends_on = data.get('depends_on')


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
        '''
        Converts the FDU into a dictionary
        '''
        data = {
            'uuid': self.uuid,
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image': self.image,
            'command': self.command,
            'storage': self.storage,
            'computation_requirements': self.computation_requirements,
            'geographical_requirements': self.geographical_requirements,
            'energy_requirements': self.energy_requirements,
            'hypervisor': self.hypervisor,
            'migration_kind': self.migration_kind,
            'configuration': self.configuration,
            'interfaces': self.interfaces,
            'io_ports': self.io_ports,
            'connection_points': self.connection_points,
            'depends_on': self.depends_on,
        }
        check_obj = user_fdu.user_fdu()
        pybindJSONDecoder.load_ietf_json({'fdu_descriptor':data}, None, None, obj=check_obj)
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

    def get_image(self):
        return self.image

    def set_image(self, image) :
        self.image = image

    def get_image_uri(self):
        return self.image.get('uri')

    def set_image_uri(self, uri) :
        self.image.update({'uri':uri})

    def get_image_uuid(self):
        return self.image.get('uuid')

    def set_image_uuid(self, uuid) :
        self.image.update({'uuid':uuid})

    def get_image_format(self):
        return self.image.get('format')

    def set_image_format(self, format) :
        self.image.update({'format':format})

    def get_command(self):
        return self.command

    def set_command(self, command) :
        self.command = command

    def get_storage(self):
        return self.storage

    def set_storage(self, storage) :
        self.storage = storage

    def get_computation_requirements(self):
        return self.computation_requirements

    def set_computation_requirements(self, computation_requirements) :
        self.computation_requirements = computation_requirements

    def get_geographical_requirements(self):
        return self.geographical_requirements

    def set_geographical_requirements(self, geographical_requirements) :
        self.geographical_requirements = geographical_requirements

    def get_energy_requirements(self):
        return self.energy_requirements

    def set_energy_requirements(self, energy_requirements) :
        self.energy_requirements = energy_requirements

    def get_hypervisor(self):
        return self.hypervisor

    def set_hypervisor(self, hypervisor) :
        self.hypervisor = hypervisor

    def get_configuration(self):
        return self.configuration

    def set_configuration(self, configuration) :
        self.configuration = configuration

    def get_io_ports(self):
        return self.io_ports

    def set_io_ports(self, io_ports) :
        self.io_ports = io_ports

    def get_interfaces(self):
        return self.interfaces

    def set_interfaces(self, interfaces) :
        self.interfaces = interfaces

    def get_connection_points(self):
        return self.connection_points

    def set_connection_points(self, connection_points) :
        self.connection_points = connection_points

    def get_depends_on(self):
        return self.depends_on

    def set_depends_on(self, depends_on) :
        self.depends_on = depends_on

    def __str__(self):
        return "Name : {} ID: {}".format(self.name, self.id)
