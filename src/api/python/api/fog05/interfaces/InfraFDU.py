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
from fog05_im import infra_fdu
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.serialise import pybindJSONEncoder
from collections import OrderedDict

class InfraFDU(object):

    def __init__(self, data=None):
        '''

        Constructor for the FDU Record
        :param data dictionary containing the FDU Record

        :return the FDU object

        '''
        self.fdu = infra_fdu.infra_fdu()
        self.encoder = pybindJSONEncoder()
        self.uuid = None
        self.fdu_id = None
        self.status = None
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
        self.error_code = None
        self.error_msg = None
        self.migration_properties = {}
        self.hypervisor_info = {}

        if data is not None:
            # data = json.loads(data)
            data.update({'hypervisor_info':json.dumps(data['hypervisor_info'])})
            pybindJSONDecoder.load_ietf_json({'fdu_record':data}, None, None, obj=self.fdu)
            self.enforce()
            self.uuid = self.fdu.fdu_record.uuid
            self.fdu_id = self.fdu.fdu_record.fdu_id
            self.image = data.get('image', None)
            self.command = data.get('command', None)
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
            self.error_code = data.get('error_code', None)
            self.error_msg = data.get('error_msg', None)
            self.migration_properties = data.get('migration_properties', None)
            self.hypervisor_info = data.get('hypervisor_info')




    def enforce(self):
        if self.fdu.fdu_record.uuid == '':
            raise ValueError('FDU.UUID cannot be empty')

        if self.fdu.fdu_record.fdu_id == '':
            raise ValueError('FDU.FDU_ID cannot be empty')

        if self.fdu.fdu_record.status == '':
            raise ValueError('FDU.Status cannot be empty')

        if self.fdu.fdu_record.computation_requirements.cpu_arch == '':
            raise ValueError('FDU.Computation_Requirements.CPU_Arch cannot be empty')

        if self.fdu.fdu_record.hypervisor == '':
            raise ValueError('FDU.Hypervisor cannot be empty')

        if self.fdu.fdu_record.migration_kind == '':
            raise ValueError('FDU.Migration_Kind cannot be empty')

        if self.fdu.fdu_record.hypervisor_info == '':
            self.fdu.fdu_record.hypervisor_info = '{}'


    def to_json(self):
        data = {
            'uuid': self.uuid,
            'fdu_id': self.fdu_id,
            'status': self.status,
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
            'error_code': self.error_code,
            'error_msg': self.error_msg,
            'migration_properties': self.migration_properties,
            'hypervisor_info': self.hypervisor_info
        }
        check_obj = infra_fdu.infra_fdu()
        pybindJSONDecoder.load_ietf_json({'fdu_record':data}, None, None, obj=check_obj)
        return data

    def get_short_id(self):
        return ''.join([x[0] for x in self.uuid.split('-')])

    def get_status(self):
        return self.status

    def set_status(self, status) :
        self.status = status

    def get_uuid(self):
        return self.uuid

    def set_uuid(self, uuid) :
        self.uuid = uuid

    def get_fdu_id(self):
        return self.fdu_id

    def set_fdu_id(self, fdu_id) :
        self.fdu_id = fdu_id

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

    def get_error_code(self):
        return self.error_code

    def set_error_code(self, error_code) :
        self.error_code = error_code

    def get_error_msg(self):
        return self.error_msg

    def set_error_msg(self, error_msg):
        self.error_msg = error_msg

    def get_migration_properties(self):
        return self.migration_properties

    def set_migration_properties(self, source, destination) :
        self.migration_properties = {'source':source, 'destination': destination}

    def get_hypervisor_info(self):
        return self.hypervisor_info

    def set_hypervisor_info(self, hypervisor_info) :
        self.hypervisor_info = hypervisor_info


    def on_defined(self):
        raise NotImplementedError('This is and interface!')

    def on_configured(self, configuration):
        raise NotImplementedError('This is and interface!')

    def on_clean(self):
        raise NotImplementedError('This is and interface!')

    def on_start(self):
        raise NotImplementedError('This is and interface!')

    def on_stop(self):
        raise NotImplementedError('This is and interface!')

    def on_pause(self):
        raise NotImplementedError('This is and interface!')

    def on_resume(self):
        raise NotImplementedError('This is and interface!')

    def before_migrate(self):
        raise NotImplementedError('This is and interface!')

    def after_migrate(self):
        raise NotImplementedError('This is and interface!')

    def __str__(self):
        return "FDU Record UUID: {} FDU_ID: {}".format(self.uuid, self.fdu_id)
