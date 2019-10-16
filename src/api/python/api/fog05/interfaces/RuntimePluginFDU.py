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


import uuid
import time
from fog05.interfaces.Plugin import Plugin
from fog05 import Yaks_Connector
from fog05 import Yaks_Connector
from fog05.DLogger import DLogger
from fog05.interfaces.InfraFDU import InfraFDU

class RuntimePluginFDU(Plugin):
    '''
    Class: RuntimePluginFDU

    This class is an interface for plugins that implements the FDU lifecycle management,
    and provides an abstraction layer
    for virtualisation capabilities
    '''

    def __init__(self,name, version, plugin_uuid, manifest):
        super(RuntimePluginFDU, self).__init__(version, plugin_uuid)
        self.pid = -1
        self.name = name
        loc = manifest.get('configuration').get('ylocator').split('/')[1]
        self.connector = Yaks_Connector(loc)
        self.logger = DLogger(debug_flag=True)
        self.node = manifest.get('configuration').get('nodeid')
        self.manifest = manifest
        self.configuration = manifest.get('configuration',{})

        self.current_fdus = {}

    def wait_destination_ready(self, fduid, instanceid, destinationid):
        '''
        Waits the destination node of a migration to be ready

        parameters
        ----------
        fduid : string
            UUID of the FDU
        instanceid : string
            UUID of the instance
        destinationid : string
            UUID of the destination node

        returns
        -------
        bool
        '''
        flag = False
        while not flag:
            try:
                res = self.agent.get_node_fdu_info(fduid, instanceid, destinationid)
                while res.get('status') != 'LAND':
                    time.sleep(0.250)
                    res = self.agent.get_node_fdu_info(fduid, instanceid, destinationid)
                flag = True
            except:
                pass
        return flag


    def wait_dependencies(self):
        '''
        Waits fot the Agent, OS and NM plugin to be up
        '''
        self.get_agent()
        os = None
        while os is None:
            try:
                os = self.get_os_plugin()
            except (RuntimeError, ValueError):
                time.sleep(1)
        nm = None
        while nm is None:
            try:
                nm = self.get_nm_plugin()
            except (RuntimeError, ValueError):
                time.sleep(1)
        return


    def write_fdu_error(self, fdu_uuid, instance_uuid, errno, errmsg):
        '''
        Writes the given error for the given FDU instance in YAKS

        parameters
        ----------
        fdu_uuid : string
            UUID of the FDU
        instance_uuid : string
            UUID of the instance
        errno : int
            Error number
        errmsg : string
            Error message
        '''
        record = self.connector.loc.actual.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        if record is None:
            record = self.connector.loc.desired.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        record = InfraFDU(record)
        record.set_status('ERROR')
        record.set_error_code(errno)
        record.set_error_msg('{}'.format(errmsg))
        self.connector.loc.actual.add_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid, record.to_json())

    def update_fdu_status(self, fdu_uuid, instance_uuid, status):
        '''
        Updates the status of the given FDU instance in YAKS

        parameters
        ----------
        fdu_uuid : string
            UUID of the FDU
        instance_uuid : string
            UUID of the instance
        status : string
            New status of the instance
        '''
        record = self.connector.loc.actual.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        if record is None:
            record = self.connector.loc.desired.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        record = InfraFDU(record)
        record.set_status(status)
        self.connector.loc.actual.add_node_fdu(self.node, self.uuid, fdu_uuid,instance_uuid, record.to_json())

    def get_local_instances(self, fdu_uuid):
        '''
        Gets all the local instances from YAKS

        returns
        -------
        string list
        '''
        return self.connector.loc.actual.get_node_fdu_instances(self.node, fdu_uuid)

    def start_runtime(self):
        '''
        Starts the plugin
        '''
        raise NotImplementedError('This is and interface!')

    def stop_runtime(self):
        '''
        Stops the plugin
        '''
        raise NotImplementedError('This is and interface!')

    def get_fdus(self):
        '''
        Gets all FDU and instances information

        returns
        -------
        dictionary
        '''
        raise NotImplementedError('This is and interface!')

    def define_fdu(self, fdu_record):
        '''
        Defines an FDU instance from the given record

        parameters
        ----------
        fdu_record : dictionary
            FDU instance record

        '''

        raise NotImplementedError('This is and interface!')

    def undefine_fdu(self, instance_uuid):
        '''
        Undefines the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def run_fdu(self, instance_uuid):
        '''
        Starts the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def stop_fdu(self, instance_uuid):
        ''''
        Stops the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def migrate_fdu(self, instance_uuid):
        '''
        Migrates the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''

        raise NotImplementedError('This is and interface!')

    def before_migrate_fdu_actions(self, instance_uuid, dst=False):
        '''
        Actions to be taken before migration of the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''

        raise NotImplementedError('This is and interface!')

    def after_migrate_fdu_actions(self, instance_uuid, dst=False):
        ''''
        Actions to be taken after the migration of the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''

        raise NotImplementedError('This is and interface!')

    def scale_fdu(self, instance_uuid):
        '''
        Scales the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def pause_fdu(self, instance_uuid):
        '''
        Pauses the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def resume_fdu(self, instance_uuid):
        '''
        Resumes the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def configure_fdu(self, instance_uuid):
        '''
        Configures the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def clean_fdu(self, instance_uuid):
        '''
        Cleans the given FDU instance

        parameters
        ----------
        instance_uuid : string
            UUID of the instance

        '''
        raise NotImplementedError('This is and interface!')

    def is_uuid(self, uuid_string):
        '''
        Verifies if the given string is a correct UUID4

        parameters
        ----------
        uuid_string : string
            the string to be verified

        returns
        -------
        bool
        '''
        try:
            val = uuid.UUID(uuid_string, version=4)
        except ValueError:
            return False
        return True


class FDUNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(FDUNotExistingException, self).__init__(message)
        self.errors = errors


class MigrationNotPossibleException(Exception):
    def __init__(self, message, errors=0):

        super(MigrationNotPossibleException, self).__init__(message)
        self.errors = errors


class MigrationNotAllowedException(Exception):
    def __init__(self, message, errors=0):

        super(MigrationNotAllowedException, self).__init__(message)
        self.errors = errors


class StateTransitionNotAllowedException(Exception):
    def __init__(self, message, errors=0):

        super(StateTransitionNotAllowedException, self).__init__(message)
        self.errors = errors
