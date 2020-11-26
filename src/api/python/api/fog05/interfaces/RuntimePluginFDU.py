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
        record = self.connector.loc.actual.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        if record is None:
            record = self.connector.loc.desired.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        record = InfraFDU(record)
        record.set_status('ERROR')
        record.set_error_code(errno)
        record.set_error_msg('{}'.format(errmsg))
        self.connector.loc.actual.add_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid, record.to_json())

    def update_fdu_status(self, fdu_uuid, instance_uuid, status):
        record = self.connector.loc.actual.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        if record is None:
            record = self.connector.loc.desired.get_node_fdu(self.node, self.uuid, fdu_uuid, instance_uuid)
        record = InfraFDU(record)
        record.set_status(status)
        self.connector.loc.actual.add_node_fdu(self.node, self.uuid, fdu_uuid,instance_uuid, record.to_json())

    def get_local_instances(self, fdu_uuid):
        return self.connector.loc.actual.get_node_fdu_instances(self.node, fdu_uuid)

    def start_runtime(self):
        '''
        start the runtime
        :return: runtime pid or runtime uuid?
        '''
        raise NotImplementedError('This is and interface!')

    def stop_runtime(self):
        '''
        stop this runtime
        '''
        raise NotImplementedError('This is and interface!')

    def get_fdus(self):
        raise NotImplementedError('This is and interface!')

    def define_fdu(self, fdu_manifest):
        '''
        Define fdu from args of from manifest file passed within parameters
        return the fdu uuid
        :args: manifest of the FDU

        ##### ASSUMING FDU MANIFEST = old ATOMIC ENTITY MANIFEST

        :return: String
        '''

        raise NotImplementedError('This is and interface!')

    def undefine_fdu(self, fdu_uuid):
        '''
        Undefine the fdu identified by fdu_uuid
        if the fdu state do not allow transition to UNDEFINED
        should throw an exception

        :fdu_uuid: String
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def run_fdu(self, fdu_uuid):
        '''
        Start the fdu identified by fdu_uuid
        if the fdu state do not allow transition to RUN (eg is non CONFIGURED)
        should throw an exception

        :fdu_uuid: String
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def stop_fdu(self, fdu_uuid):
        '''
        Stop the fdu identified by fdu_uuid
        if the fdu state do not allow transition to CONFIGURED
        (in this case is not in RUNNING)
        should throw an exception

        :fdu_uuid: String
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def migrate_fdu(self, fdu_uuid, dst=False):
        '''
        Migrate the fdu identified by fdu_uuid to the new FogNode
        identified by fognode_uuid
        The migration depend to the nature of the fdu
         (native app, µSvc, VM, Container)
        if the fdu state do not allow transition to
         MIGRATE (eg a native app can't be migrated)
        should throw an exception
        if the destination node can't handle the
         migration an exception should be throwed

        To help migration should use the two methods:

        - before_migrate_fdu_actions()
        - after_migrate_fdu_actions()

        After the migration the fdu on the source node has to be undefined
        the one on the destination node has to be in RUNNING


        :fdu_uuid: String
        :fognode_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def before_migrate_fdu_actions(self, fdu_uuid, dst=False):
        '''
        Action to be taken before a migration
        eg. copy disks of vms, save state of µSvc

        :fdu_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def after_migrate_fdu_actions(self, fdu_uuid, dst=False):
        '''
        Action to be taken after a migration
        eg. delete disks of vms, delete state of µSvc, undefine fdu

        :fdu_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def scale_fdu(self, fdu_uuid):
        '''
        Scale an fdu
        eg. give more cpu/ram/disk, maybe passed
         by parameter the new scale value?

        if the fdu state do not allow transition to
        SCALE (in this case is not in RUNNING)
        should throw an exception

        :fdu_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def pause_fdu(self, fdu_uuid):
        '''
        Pause an fdu

        if the fdu state do not allow transition
        to PAUSED (in this case is not in RUNNING)
        should throw an exception

        :fdu_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def resume_fdu(self, fdu_uuid):
        '''
        Resume an fdu

        if the fdu state do not allow transition to
         RUNNING (in this case is not in PAUSED)
        should throw an exception

        :fdu_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def configure_fdu(self, fdu_uuid):
        '''
        TBD

        :fdu_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def clean_fdu(self, fdu_uuid):
        '''
        Clean an fdu

        this mode destroy the fdu instance


        if the fdu state do not allow transition
        to DEFINED (in this case is not in CONFIGURED)
        should throw an exception

        :fdu_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def is_uuid(self, uuid_string):
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
