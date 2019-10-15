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
# Initial implementation and API

from fog05.interfaces.Plugin import Plugin
import uuid


class OSPlugin(Plugin):
    '''
    Interfaces for plugins that allow interaction with underlying operating
     systemprovide an abstraction layer for some management
      and monitoring functions

    '''

    def __init__(self, version, plugin_uuid=None):
        super(OSPlugin, self).__init__(version, plugin_uuid)
        self.requirements = []

    def get_base_path(self):
        raise NotImplementedError

    def execute_command(self, command, blocking, external):
        '''
        Executes a command on underlying os,

        parameters
        ---------

        command : string
            command to be executed

        blocking : bool
            true if the call has to block until the end of the command

        external : bool
            true if the command has to be executed in an external os shell

        returns
        ------
        dictionary

            {'result': string}

        '''

        raise NotImplementedError('This is and interface!')

    def install_package(self, packages):
        '''
        Installs all packages passed within the parameter, return a bool
        to know the retult of operation

        parameters
        ----------

        packages : string list

            name of the packages to be installed

        returns
        -------
        list (string, bool)

            name of package, bool
        '''

        raise NotImplementedError('This is and interface!')

    def store_file(self, content, file_path, filename):
        '''
        Stores a file in local disk, maybe can convert
         from windows dir separator to unix dir separator

        parameters
        ----------

        content : string
            base64 encoded and hexified bytes of the file content

        file_path : string
            path where the content will stored

        filename : string
            name of the file

        returns
        -------
        dictionary
            {'result':bool}
        '''

        raise NotImplementedError('This is and interface!')

    def file_exists(self, file_path):
        '''
        Checks if the given file exists

        parameters
        ----------
        file_path : string
            path to the file

        returns
        -------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError

    def dir_exists(self, path):
        '''
        Checks if the given directory exists

        parameters
        ----------
        path : string
            path to the directory

        returns
        -------
        dictionary
            {'result':bool}


        '''
        raise NotImplementedError

    def create_dir(self, path):
        '''
        Creates the given new directory

        parameters
        ----------
        path : string
            path to the directory

        returns
        -------
        dictionary
            {'result':bool}

        '''
        raise NotImplementedError

    def create_file(self, path):
        '''
        Creates the given new empty file

        parameters
        ----------
        path : string
            path to the file

        returns
        -------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError

    def remove_dir(self, path):
        '''
        Removes the given directory

        parameters
        ----------
        path : string
            path to the directory

        returns
        -------
        dictionary
            {'result':bool}

        '''
        raise NotImplementedError

    def remove_file(self, path):
        '''
        Removes the given file

        parameters
        ----------
        path : string
            path to the directory

        returns
        -------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError

    def read_file(self, file_path, root=False):
        '''
        Read the content from a file in the local disk,
         maybe can convert from windows dir separator to unix dir separator
        return the file content
        throw an exception if file not exits

        :file_path: String
        :return: byte

        '''

        raise NotImplementedError('This is and interface!')

    def get_neighbors(self):
        raise NotImplementedError('This is and interface!')

    def read_binary_file(self, file_path):
        raise NotImplementedError

    def download_file(self, url, file_path):
        raise NotImplementedError

    def get_CPUID(self):
        '''
        Return the underlying hw cpuid
        :return: String
        '''

        raise NotImplementedError('This is and interface!')

    def get_CPU_level(self):
        '''
        Return the current cpu usage level
        :return: float
        '''

        raise NotImplementedError('This is and interface!')

    def get_memory_level(self):
        '''
        Return the current memory usage level
        :return: float
        '''
        raise NotImplementedError('This is and interface!')

    def get_storage_level(self):
        '''
        Return the current local storage usage level
        :return: float
        '''
        raise NotImplementedError('This is and interface!')

    def get_network_level(self):
        '''
        Return the current network usage level
        :return: float
        '''
        raise NotImplementedError('This is and interface!')

    def remove_package(self, packages):
        '''
        Remove all packages passed within the parameter, return a bool
        to know the retult of operation

        :packages: tuple
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def check_if_pid_exists(self, pid):
        raise NotImplementedError('This is and interface!')

    def send_signal(self, signal, pid):
        '''
        Send a signal to the process identified by pid
        throw an exception if pid not exits

        :signal: int
        :pid: int
        :return: bool

        '''

        raise NotImplementedError('This is and interface!')

    def get_pid(self, process):
        '''
        Try to get the the pid from the process name
        :process: string
        :return: int
        '''
        raise NotImplementedError('This is and interface!')

    def send_sig_int(self, pid):
        '''
        Send a SigKill (Ctrl+C) to the process identified by pid
        throw an exception if pid not exits
        :pid: int
        :return: bool
        '''

        raise NotImplementedError('This is and interface!')

    def send_sig_kill(self, pid):
        '''
        Send a SigKill (kill the process) to the process identified by pid
        throw an exception if pid not exits
        :pid: int
        :return: bool
        '''

        raise NotImplementedError('This is and interface!')

    def get_uuid(self):
        return uuid.uuid4()

    def get_processor_information(self):
        raise NotImplementedError

    def get_memory_information(self):
        raise NotImplementedError

    def get_disks_information(self):
        raise NotImplementedError

    def get_io_informations(self):
        raise NotImplementedError

    def get_accelerators_informations(self):
        raise NotImplementedError

    def get_network_informations(self):
        raise NotImplementedError

    def get_position_information(self):
        raise NotImplementedError

    def add_know_host(self, hostname, ip):
        raise NotImplementedError

    def remove_know_host(self, hostname):
        raise NotImplementedError

    def get_intf_type(self, name):
        raise NotImplementedError

    def set_io_unaviable(self, io_name):
        raise NotImplementedError

    def set_io_available(self, io_name):
        raise NotImplementedError

    def set_accelerator_unaviable(self, acc_name):
        raise NotImplementedError

    def set_accelerator_available(self, acc_name):
        raise NotImplementedError

    def set_interface_unaviable(self, intf_name):
        raise NotImplementedError

    def set_interface_available(self, intf_name):
        raise NotImplementedError

    def get_hostname(self):
        raise NotImplementedError


class ProcessNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(ProcessNotExistingException, self).__init__(message)
        self.errors = errors


class FileNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(FileNotExistingException, self).__init__(message)
        self.errors = errors
