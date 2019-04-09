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


class RuntimePluginFDU(Plugin):

    def __init__(self, version, plugin_uuid=None):
        super(RuntimePluginFDU, self).__init__(version, plugin_uuid)
        self.pid = -1
        self.name = ''
        self.current_fdus = {}

    def get_nm_plugin(self):
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        nms = [x for x in pls if x.get('type') == 'network']
        if len(nms) == 0:
            raise RuntimeError('No network_manager present in the node!!')
        nm = nms[0]
        return nm

    def call_nw_plugin_function(self, fname, fparameters):
        nm = self.get_nm_plugin().get('uuid')
        res = self.connector.loc.actual.exec_nw_eval(
            self.node, nm, fname, fparameters)
        if res.get('error'):
            raise ValueError('NM Eval returned {}'.format(res.get('error')))
            # return None
        return res.get('result')

    def get_fdu_descriptor(self, fduid):
        parameters = {'fdu_uuid': fduid}
        fname = 'get_fdu_info'
        return self.call_agent_function(fname, parameters)

    def wait_destination_ready(self, fduid, destinationid):
        parameter = {
            'fdu_uuid':fduid,
            'node_uuid':destinationid
        }
        fname = 'get_node_fdu_info'
        flag = False
        while not flag:
            try:
                res = self.call_agent_function(fname, parameter)
                while res.get('status') != 'LAND':
                    time.sleep(0.250)
                    res = self.call_agent_function(fname, parameter)
                flag = True
            except:
                pass
        return flag


    def get_destination_node_mgmt_net(self, destinationid):
        parameters = {
            'node_uuid': destinationid
        }
        fname = 'get_image_info'
        return self.call_agent_function(fname, parameters)


    def get_image_info(self, imageid):
        parameters = {
            'image_uuid': imageid
        }
        fname = 'get_node_mgmt_address'
        return self.call_agent_function(fname, parameters)


    def get_local_mgmt_address(self):
        fname = 'local_mgmt_address'
        return self.call_os_plugin_function(fname,{})

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
