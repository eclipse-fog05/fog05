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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Initial implementation and API


import uuid
from fog05.interfaces.Plugin import Plugin


class RuntimePlugin(Plugin):

    def __init__(self, version, plugin_uuid=None):
        super(RuntimePlugin, self).__init__(version, plugin_uuid)
        self.pid = -1
        self.name = ''
        self.current_entities = {}

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

    def get_entities(self):
        raise NotImplementedError('This is and interface!')

    def define_entity(self, *args, **kwargs):
        '''
        Define entity from args of from manifest file passed within parameters
        return the entity uuid
        :args: dict
        :return: String
        '''

        raise NotImplementedError('This is and interface!')

    def undefine_entity(self, enitity_uuid):
        '''
        Undefine the entity identified by entity_uuid
        if the entity state do not allow transition to UNDEFINED
        should throw an exception

        :entity_uuid: String
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def run_entity(self, enitity_uuid, instance_uuid=None):
        '''
        Start the entity identified by entity_uuid
        if the entity state do not allow transition to RUN (eg is non CONFIGURED)
        should throw an exception

        :entity_uuid: String
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def stop_entity(self, enitity_uuid, instance_uuid=None):
        '''
        Stop the entity identified by entity_uuid
        if the entity state do not allow transition to CONFIGURED (in this case is not in RUNNING)
        should throw an exception

        :entity_uuid: String
        :return: bool

        '''
        raise NotImplementedError('This is and interface!')

    def migrate_entity(self, entity_uuid, dst=False, instance_uuid=None):
        '''
        Migrate the entity identified by entity_uuid to the new FogNode identified by fognode_uuid
        The migration depend to the nature of the entity (native app, µSvc, VM, Container)
        if the entity state do not allow transition to MIGRATE (eg a native app can't be migrated)
        should throw an exception
        if the destination node can't handle the migration an exception should be throwed

        To help migration should use the two methods:

        - beforeMigrateEntityActions()
        - afterMigrateEntiryActions()

        After the migration the entity on the source node has to be undefined
        the one on the destination node has to be in RUNNING


        :entity_uuid: String
        :fognode_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def before_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        '''
        Action to be taken before a migration
        eg. copy disks of vms, save state of µSvc

        :entity_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def after_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        '''
        Action to be taken after a migration
        eg. delete disks of vms, delete state of µSvc, undefine entity

        :entity_uuid: String
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def scale_entity(self, entity_uuid, instance_uuid=None):
        '''
        Scale an entity
        eg. give more cpu/ram/disk, maybe passed by parameter the new scale value?

        if the entity state do not allow transition to SCALE (in this case is not in RUNNING)
        should throw an exception

        :entity_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def pause_entity(self, entity_uuid, instance_uuid=None):
        '''
        Pause an entity

        if the entity state do not allow transition to PAUSED (in this case is not in RUNNING)
        should throw an exception

        :entity_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def resume_entity(self, entity_uuid, instance_uuid=None):
        '''
        Resume an entity

        if the entity state do not allow transition to RUNNING (in this case is not in PAUSED)
        should throw an exception

        :entity_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def configure_entity(self, entity_uuid, instance_uuid=None):
        '''
        Configure an entity

        This should create an entity instance that can be addressed by .../entity/<entity_uuid>/instance/<instance_uuid>
        not clear at the time if instance uuid should be generated by this method or came as a paramenter
        This state is the separation from entity and entity instances, because here we create the files

        if the entity state do not allow transition to CONFIGURED (in this case is not in DEFINED)
        should throw an exception

        :entity_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def clean_entity(self, entity_uuid, instance_uuid=None):
        '''
        Clean an entity

        this mode destroy the entity instance


        if the entity state do not allow transition to DEFINED (in this case is not in CONFIGURED)
        should throw an exception

        :entity_uuid: String
        :return: bool


        '''
        raise NotImplementedError('This is and interface!')

    def is_uuid(self, uuid_string):
        try:
            val = uuid.UUID(uuid_string, version=4)
        except ValueError:
            return False
        return True


class EntityNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(EntityNotExistingException, self).__init__(message)
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
