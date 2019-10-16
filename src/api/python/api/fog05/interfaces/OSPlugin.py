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

        parameters
        ----------

        file_path : string
            path to file

        root : bool
            if true it will use sudo cat to read the file

        returns
        --------
        dictionary
            {'result':bytes}


        '''

        raise NotImplementedError('This is and interface!')

    def get_neighbors(self):
        '''
        Gets LLDP neighbors

        retutns
        ------
        list of dictionaries

        '''
        raise NotImplementedError('This is and interface!')

    def read_binary_file(self, file_path):
        '''
        Reads binary file

        parameters
        ----------
        file_path : string
            path to file

        returns
        -------
        bytes

        '''
        raise NotImplementedError

    def download_file(self, url, file_path):
        '''
        Downloads the given file in the given path

        parameters
        ----------
        url : string
            url for the source file
        file_path : string
            path to destination file

        returns
        ------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError

    def get_CPU_level(self):
        '''
        Gets the current CPU usage

        returns
        -------
        float
        '''

        raise NotImplementedError('This is and interface!')

    def get_memory_level(self):
        '''
        Gets the current RAM usage

        returns
        -------
        float
        '''
        raise NotImplementedError('This is and interface!')

    def get_storage_level(self):
        '''
        Get the current root disk usage

        returns
        -------
        float
        '''
        raise NotImplementedError('This is and interface!')

    def get_network_level(self):
        '''
        Gets the current network usage statistics

        returns
        -------
        list of dictionaries
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

    def remove_package(self, packages):
        '''
        Removes the given packages

        parameters
        ---------
        packages : list of string
            packages to be removed

        returns
        -------
        list (string, bool)
            name of package, bool
        '''

        raise NotImplementedError('This is and interface!')

    def check_if_pid_exists(self, pid):
        '''
        Checks if a  given PID exists

        parameters
        ----------
        pid : int
            PID to be verified

        returns
        -------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError('This is and interface!')

    def send_signal(self, signal, pid):
        '''
        Sends a signal to the given pid

        parametes
        ---------
        signal : int
            signal to be sent
        pid : int
            PID to be signaled

        returns
        -------
        dictionary
            {'result':bool}

        '''

        raise NotImplementedError('This is and interface!')

    def send_sig_int(self, pid):
        '''
        Sends a SigKill (Ctrl+C) to the given PID

        parameters
        ----------
        pid : int
            pid to be signaled

        returns
        -------
        dictionary
            {'result':bool}
        '''

        raise NotImplementedError('This is and interface!')

    def send_sig_kill(self, pid):
        '''
        Sends a SigKill (kill the process) to the given pid
        throw an exception if pid not exits

        parameters
        ----------
        pid : int
            pid to be signaled

        returns
        -------
        dictionary
            {'result':bool}
        '''

        raise NotImplementedError('This is and interface!')

    def get_uuid(self):
        '''
        Gets the node UUID

        returns
        -------
        string
        '''
        raise NotImplementedError('This is and interface!')

    def get_processor_information(self):
        '''
        Gets information on the node CPU

        returns
        -------
        list of dictionaries
            {'model':string, 'frequency':float, 'arch':string}
        '''
        raise NotImplementedError

    def get_memory_information(self):
        '''
        Gets information on the node RAM

        returns
        -------
        dictionary
            {'size':float}

        '''
        raise NotImplementedError

    def get_disks_information(self):
        '''
        Gets information on the node disks usage

        returns
        -------
        list of dictionaries
            {'local_address':string, 'dimension':float, 'mount_point':string, 'filesystem':string}
        '''
        raise NotImplementedError

    def get_io_informations(self):
        '''
        Gets information about node IO ports

        returns
        -------
        list of dictionaries
            {'name':string, 'io_type':string, 'io_file':string, 'available':bool}
        '''
        raise NotImplementedError

    def get_accelerators_informations(self):
        '''
        Gets information about node hardware accelerators

        returns
        -------
        list of dictionaries
            {'hw_address':string, 'name':string, 'supported_library' string list, 'available':bool}

        '''
        raise NotImplementedError

    def get_network_informations(self):
        '''
        Gets information about node network interfaces

        returns
        -------
        list of dictionaties
            {
                'intf_name':string,
                'intf_mac_address':string,
                'intf_speed': int,
                'type':string,
                'available':bool,
                'default_gw':bool,
                'intf_configuration':
                {
                    'ipv4_address':string,
                    'ipv4_netmask':string,
                    'ipv4_gateway':string.
                    'ipv6_address':string,
                    'ipv6_netmask':string,
                    'ipv6_gateway':string.
                    'bus_address':string
                }
            }

        '''
        raise NotImplementedError

    def get_position_information(self):
        '''
        Gets information about mode position

        returns
        -------
        dictionary
            {'lat':float, 'lon':float}
        '''
        raise NotImplementedError

    def add_know_host(self, hostname, ip):
        '''
        Adds the given host in node ssh configuration

        parameters
        ----------
        hostname : string
            host to be added
        ip : string
            IP address of the host

        returns
        -------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError

    def remove_know_host(self, hostname):
        '''
        Removes the given host from node ssh configuration

        parameters
        ----------
        hostname : string
            host to be removed

        returns
        -------
        dictionary
            {'result':bool}
        '''
        raise NotImplementedError

    def get_intf_type(self, name):
        '''
        Gets the inteface type for the given interface

        parameters
        ----------
        name : string
            name of the interface

        returns
        -------
        dictionary
            {'result':string}
        '''
        raise NotImplementedError

    def set_io_unaviable(self, io_name):
        '''
        Sets a given IO device as unavailable

        paramters
        ---------
        io_name : string
            name of the IO device

        returns
        -------
        bool
        '''
        raise NotImplementedError

    def set_io_available(self, io_name):
        '''
        Sets a given IO device as available

        paramters
        ---------
        io_name : string
            name of the IO device

        returns
        -------
        bool
        '''
        raise NotImplementedError

    def set_accelerator_unaviable(self, acc_name):
        '''
        Sets a given accelerator device as unavailable

        paramters
        ---------
        acc_name : string
            name of the accelerator device

        returns
        -------
        bool
        '''
        raise NotImplementedError

    def set_accelerator_available(self, acc_name):
        '''
        Sets a given accelerator device as available

        paramters
        ---------
        acc_name : string
            name of the accelerator device

        returns
        -------
        bool
        '''
        raise NotImplementedError

    def set_interface_unaviable(self, intf_name):
        '''
        Sets a given network device as unavailable

        paramters
        ---------
        intf_name : string
            name of the network device

        returns
        -------
        bool
        '''
        raise NotImplementedError

    def set_interface_available(self, intf_name):
        '''
        Sets a given network device as available

        paramters
        ---------
        intf_name : string
            name of the network device

        returns
        -------
        bool
        '''
        raise NotImplementedError

    def get_hostname(self):
        '''
        Gets node hostname

        returns
        -------
        string
        '''
        raise NotImplementedError


class ProcessNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(ProcessNotExistingException, self).__init__(message)
        self.errors = errors


class FileNotExistingException(Exception):
    def __init__(self, message, errors=0):

        super(FileNotExistingException, self).__init__(message)
        self.errors = errors
