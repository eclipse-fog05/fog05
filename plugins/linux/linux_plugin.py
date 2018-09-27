
# Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set

import uuid
import psutil
from fog05.interfaces.OSPlugin import OSPlugin
from subprocess import PIPE
import subprocess
import re
import platform
import netifaces
import shutil
import socket
import os
import sys
# platform.linux_distribution()



'''
        Redhat and friends: Test for /etc/redhat-release, check contents
        Debian: Test for /etc/debian_version, check contents
        Mandriva and friends: Test for /etc/version, check contents
        Slackware: Test for /etc/slackware-version, check contents
        Ubuntu: test fot /etc/lsb-release, check contents

'''

# TODO OS Plugin should not be aware of the Agent - The Agent is in OCaml no way to access his store and his logger

class Linux(OSPlugin):
    def __init__(self, name, version, agent, plugin_uuid):
        super(Linux, self).__init__(version, plugin_uuid)
        self.name = name
        self.pm = None
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from GNU\Linux Plugin')
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.distro = self.__check_distro()
        self.io_devices = []
        self.nw_devices = []
        self.accelerator_devices = []
        if self.distro == '':
            self.agent.logger.warning('__init__()', 'Distribution not recognized, cannot install packages')
        else:
            self.agent.logger.info('__init__()', ' Running on {}'.format(self.distro))
            self.pm = self.__get_package_manager(self.distro)
            self.agent.logger.info('__init__()', ' Package manger {} loaded! '.format(self.pm.name))

        self.io_devices = self.__get_io_devices()
        self.nw_devices = self.__get_nw_devices()
        self.accelerator_devices = self.__get_acc_devices()


    def get_base_path(self):
        return '/opt/fos'

    def execute_command(self, command, blocking=False, external=False):
        self.agent.logger.info('executeCommand()', 'OS Plugin executing command {}'.format(command))
        if external:
            os.system(command)
        else:
            cmd_splitted = command.split()
            p = psutil.Popen(cmd_splitted, stdout=PIPE)
            if blocking:
                p.wait()
        # for line in p.stdout:
        #     self.agent.logger.debug('executeCommand()', str(line))

    def add_know_host(self, hostname, ip):
        self.agent.logger.info('addKnowHost()', ' OS Plugin add to hosts file')
        add_cmd = 'sudo {} -a {} {}'.format(os.path.join(self.DIR, 'scripts', 'manage_hosts.sh'), hostname, ip)
        self.execute_command(add_cmd, True)

    def remove_know_host(self, hostname):
        self.agent.logger.info('removeKnowHost()', ' OS Plugin remove from hosts file')
        del_cmd = 'sudo {} -d {}'.format(os.path.join(self.DIR, 'scripts', 'manage_hosts.sh'), hostname)
        self.execute_command(del_cmd, True)

    def dir_exists(self, path):
        return os.path.isdir(path)

    def create_dir(self, path):
        if not self.dir_exists(path):
            os.makedirs(path)

    def create_file(self, path):
        if not self.file_exists(path):
            with open(path, 'a'):
                os.utime(path, None)

    def remove_dir(self, path):
        if self.dir_exists(path):
            shutil.rmtree(path)

    def remove_file(self, path):
        try:
            return os.remove(path)
        except FileNotFoundError as e:
            self.agent.logger.error('removeFile()', 'OS Plugin File Not Found {} so don\'t need to remove'.format(e.strerror))
            return

    def file_exists(self, file_path):
        return os.path.isfile(file_path)

    def store_file(self, content, file_path, filename):
        full_path = os.path.join(file_path, filename)
        f = open(full_path, 'w')
        f.write(content)
        f.flush()
        f.close()

    def read_file(self, file_path, root=False):
        data = ''
        if root:
            file_path = 'sudo cat {}'.format(file_path)
            process = subprocess.Popen(file_path.split(), stdout=subprocess.PIPE)
            # read one line at a time, as it becomes available
            for line in iter(process.stdout.readline, ''):
                data = data + '{}'.format(line)
        else:
            with open(file_path, 'r') as f:
                data = f.read()
        return data

    def read_binary_file(self, file_path):
        data = None
        with open(file_path, 'rb') as f:
            data = f.read()
        return data

    def download_file(self, url, file_path):
        wget_cmd = 'wget {} -O {}'.format(url, file_path)
        self.execute_command(wget_cmd, True)

    def get_CPU_level(self):
        return psutil.cpu_percent(interval=1)

    def get_memory_level(self):
        return psutil.virtual_memory().percent

    def get_storage_level(self):
        return psutil.disk_usage('/').percent

    def check_if_pid_exists(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def send_signal(self, signal, pid):
        if self.check_if_pid_exists(pid) is False:
            self.agent.logger.error('sendSignal()', 'OS Plugin Process not exists {}'.format(pid))
            #raise ProcessNotExistingException('Process %d not exists' % pid)
        else:
            psutil.Process(pid).send_signal(signal)
        return True

    def send_sig_int(self, pid):
        if self.check_if_pid_exists(pid) is False:
            self.agent.logger.error('sendSigInt()', 'OS Plugin Process not exists {}'.format(pid))
            #raise ProcessNotExistingException('Process %d not exists' % pid)
        else:
            psutil.Process(pid).send_signal(2)
        return True

    def send_sig_kill(self, pid):
        if self.check_if_pid_exists(pid) is False:
            self.agent.logger.error('sendSigInt()', 'OS Plugin Process not exists {}'.format(pid))
            #raise ProcessNotExistingException('Process %d not exists' % pid)
        else:
            psutil.Process(pid).send_signal(9)
        return True

    def get_network_level(self):
        raise NotImplementedError

    def install_package(self, packages):
        self.pm.installPackage(packages)

    def remove_package(self, packages):
        self.pm.removePackage(packages)

    def get_pid(self, process):
        raise NotImplementedError

    def get_processor_information(self):
        cpu = []
        num_cpu = psutil.cpu_count()
        if len(psutil.cpu_freq(percpu=True)) != 0:
            num_cpu = \
                min(psutil.cpu_count(), len(psutil.cpu_freq(percpu=True)))
        for i in range(0, num_cpu):
            model = self.__get_processor_name()
            try:
                frequency = psutil.cpu_freq(percpu=True)
                if len(frequency) == 0:
                    frequency = self.__get_frequency_from_cpuinfo()
                elif len(frequency) == 1:
                    frequency = frequency[0][2]
                else:
                    frequency = frequency[i][2]
            except AttributeError:
                frequency = self.__get_frequency_from_cpuinfo()
            arch = platform.machine()
            cpu.append({'model': model, 'frequency': frequency, 'arch': arch})
        return cpu

    def get_memory_information(self):
        # conversion to MB
        return {'size': psutil.virtual_memory()[0] / 1024 / 1024}

    def get_disks_information(self):
        disks = []
        for d in psutil.disk_partitions():
            dev = d[0]
            mount = d[1]
            dim = psutil.disk_usage(mount)[0] / 1024 / 1024 / 1024  # conversion to gb
            fs = d[2]
            disks.append({'local_address': dev, 'dimension': dim, 'mount_point': mount, 'filesystem': fs})
        return disks

    def get_io_informations(self):
        return self.io_devices

    def get_accelerators_informations(self):
        return self.accelerator_devices

    def get_network_informations(self):
        return self.nw_devices

    def get_uuid(self):
        # $ blkid / dev / sda1
        # /dev/sda1: LABEL = '/'  UUID = 'ee7cf0a0-1922-401b-a1ae-6ec9261484c0' SEC_TYPE = 'ext2' TYPE = 'ext3'
        # generate uuid from this or from cpuid or mb uuid from /sys/class/dmi/id/product_uuid
        '''

        uuid_regex = r"PARTUUID=\"(.{0,37})\""
        p = psutil.Popen('sudo blkid /dev/sda1'.split(), stdout=PIPE)
        res = ""
        for line in p.stdout:
            res = str(res+"%s" % line)
        m = re.search(uuid_regex, res)
        if m:
            found = m.group(1)
        return found
        :return:
        '''


        #p = psutil.Popen('sudo cat /sys/class/dmi/id/product_uuid'.split(), stdout=PIPE)
        p = psutil.Popen('sudo cat /etc/machine-id'.split(), stdout=PIPE)
        # p = psutil.Popen('sudo cat '.split(), stdout=PIPE)
        res = ''
        for line in p.stdout:
            res = res + '{}'.format(line.decode('utf-8'))
        return res.lower().strip()



    def get_hostname(self):
        res = ''
        p = psutil.Popen('hostname', stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            res = res + '{}'.format(line)
        return res.strip()

    def get_position_information(self):
        raise NotImplemented

    def get_intf_type(self, name):
        if name[:-1] in ['ppp', 'wvdial']:
            itype = 'ppp'
        elif name[:2] in ['wl', 'ra', 'wi', 'at']:
            itype = 'wireless'
        elif name[:2].lower() == 'br':
            itype = 'bridge'
        elif name[:5].lower() == 'virbr':
            itype = 'virtual bridge'
        elif name[:5].lower() == 'lxdbr':
            itype = 'container bridge'
        elif name[:3].lower() == 'tap':
            itype = 'tap'
        elif name[:2].lower() == 'tu':
            itype = 'tunnel'
        elif name.lower() == 'lo':
            itype = 'loopback'
        elif name[:2] in ['et', 'en']:
            itype = 'ethernet'
        elif name[:4] in ['veth' , 'vtap']:
            itype = 'virtual'
        else:
            itype = 'unknown'

        return itype

    def __get_processor_name(self):
        command = 'cat /proc/cpuinfo'.split()
        p = psutil.Popen(command, stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            if 'model name' in line:
                return re.sub('.*model name.*:', '', line, 1).strip()
        return ''

    def __get_frequency_from_cpuinfo(self):
        command = 'cat /proc/cpuinfo'.split()
        p = psutil.Popen(command, stdout=PIPE)
        for line in p.stdout:
            line = line.decode()
            if 'cpu MHz' in line:
                return float(re.sub('.*cpu MHz.*:', '', line, 1))
        return 0.0

    def __get_io_devices(self):
        dev = []
        gpio_path = '/sys/class/gpio' #gpiochip0
        gpio_devices = [f for f in os.listdir(gpio_path) if f not in ['export', 'unexport']]
        for d in gpio_devices:
            dev.append({'name': d, 'io_type': 'gpio', 'io_file': gpio_path+os.path.sep+d, 'available': True})

        return dev

    def __get_default_gw(self):
        cmd = 'sudo {}'.format(os.path.join(self.DIR, 'scripts', 'default_gw.sh'))
        p = psutil.Popen(cmd.split(), stdout=PIPE)
        p.wait()
        iface = ''
        for line in p.stdout:
            iface = line.decode().strip()

        return iface

    def __get_nw_devices(self):
        # {'default': {2: ('172.16.0.1', 'brq2376512c-13')}, 2: [('10.0.0.1', 'eno4', True), ('172.16.0.1', 'brq2376512c-13', True), ('172.16.1.1', 'brqf110e342-9b', False), ('10.0.0.1', 'eno4', False)]}

        nets = []
        intfs = psutil.net_if_stats().keys()
        gws = netifaces.gateways().get(2)
        if gws is None:
            gws = []

        default_gw = self.__get_default_gw()
        if default_gw == '':
            self.agent.logger.warning('__get_nw_devices()', 'Default gw not found!!')
        for k in intfs:
            intf_info = psutil.net_if_addrs().get(k)
            if intf_info is not None:
                ipv4_info = [x for x in intf_info if x[0] == socket.AddressFamily.AF_INET]
                ipv6_info = [x for x in intf_info if x[0] == socket.AddressFamily.AF_INET6]
                l2_info = [x for x in intf_info if x[0] == socket.AddressFamily.AF_PACKET]

                if len(ipv4_info) > 0:
                    ipv4_info = ipv4_info[0]
                    ipv4 = ipv4_info[1]
                    ipv4mask = ipv4_info[2]
                    search_gw = [x[0] for x in gws if x[1] == k]
                    if len(search_gw) > 0:
                        ipv4gateway = search_gw[0]
                    else:
                        ipv4gateway = ''

                else:
                    ipv4 = ''
                    ipv4gateway = ''
                    ipv4mask = ''

                if len(ipv6_info) > 0:
                    ipv6_info = ipv6_info[0]
                    ipv6 = ipv6_info[1]
                    ipv6mask = ipv6_info[2]
                else:
                    ipv6 = ''
                    ipv6mask = ''

                if len(l2_info) > 0:
                    l2_info = l2_info[0]
                    mac = l2_info[1]
                else:
                    mac = ''

                speed = psutil.net_if_stats().get(k)[2]
                inft_conf = {'ipv4_address': ipv4, 'ipv4_netmask': ipv4mask, 'ipv4_gateway': ipv4gateway, 'ipv6_address':
                    ipv6, 'ipv6_netmask': ipv6mask}

                iface_info = {'intf_name': k, 'inft_configuration': inft_conf, 'intf_mac_address': mac, 'intf_speed':
                              speed, 'type': self.get_intf_type(k), 'available': True, 'default_gw': False}
                if k == default_gw:
                    iface_info.update({'available': False})
                    iface_info.update({'default_gw': True})
                nets.append(iface_info)

        return nets

    def __get_acc_devices(self):
        return []

    def __find_interface_by_name(self, dev_name, dev_list):
        for i, dev in enumerate(dev_list):
            if dev.get('intf_name') == dev_name:
                return i, dev
        return None, None

    def set_interface_unaviable(self, intf_name):
        i, interface_info = self.__find_interface_by_name(intf_name, self.nw_devices)
        if i is not None and interface_info is not None:
            interface_info.update({'available': False})
            self.nw_devices[i] = interface_info
            return True
        return False

    def set_interface_available(self, intf_name):
        i, interface_info = self.__find_interface_by_name(intf_name, self.nw_devices)
        if i is not None and interface_info is not None:
            interface_info.update({'available': True})
            self.nw_devices[i] = interface_info
            return True
        return False

    def __find_dev_by_name(self, dev_name, dev_list):
        for i, dev in enumerate(dev_list):
            if dev.get('name') == dev_name:
                return i, dev
        return None, None

    def set_io_unaviable(self, io_name):
        i, io_info = self.__find_interface_by_name(io_name, self.io_devices)
        if i is not None and io_info is not None:
            io_info.update({'available': False})
            self.io_devices[i] = io_info
            return True
        return False

    def set_io_available(self, io_name):
        i, io_info = self.__find_interface_by_name(io_name, self.io_devices)
        if i is not None and io_info is not None:
            io_info.update({'available': True})
            self.io_devices[i] = io_info
            return True
        return False

    def set_accelerator_unaviable(self, acc_name):
        i, acc_info = self.__find_interface_by_name(acc_name, self.accelerator_devices)
        if i is not None and acc_info is not None:
            acc_info.update({'available': False})
            self.accelerator_devices[i] = acc_info
            return True
        return False

    def set_accelerator_available(self, acc_name):
        i, acc_info = self.__find_interface_by_name(acc_name, self.accelerator_devices)
        if i is not None and acc_info is not None:
            acc_info.update({'available': True})
            self.accelerator_devices[i] = acc_info
            return True
        return False

    def __check_distro(self):

        lsb = '/etc/lsb-release'
        deb = '/etc/debian_version'
        rh = '/etc/redhat-release'
        sw = '/etc/slackware-release'
        go = '/etc/gentoo-release'

        if os.path.exists(deb):
            if os.path.exists(lsb):
                return 'ubuntu'
            else:
                return 'debian'
        elif os.path.exists(rh):
            return 'redhat'
        elif os.path.exists(sw):
            return 'slackware'
        elif os.path.exists(go):
            return 'gentoo'
        else:
            return ''

    def __get_package_manager(self, distro):
        '''
        From distribution name to package manager wrapper
        :param distro: Linux distribution name
        :return: a wrapper for basic operation on package manager
        '''

        wr = {
            'debian': self.AptWrapper(),
            'ubuntu': self.AptWrapper(),
            'redhat': self.DnfWrapper()
        }

        return wr.get(distro, None)

    class AptWrapper(object):
        def __init__(self):
            self.name = 'apt'

        def update_packages(self):
            cmd = 'sudo apt update && sudo apt upgrade -y && sudo apt autoremove --purge'
            os.system(cmd)

        def install_package(self, pkg_name):
            cmd = 'sudo apt update && sudo apt install {}'.format(pkg_name)
            os.system(cmd)

        def remove_package(self, pkg_name):
            cmd = 'sudo apt update && sudo apt remove {}'.format(pkg_name)
            os.system(cmd)

        def purge_package(self, pkg_name):
            cmd = 'sudo apt update && sudo apt purge {}'.format(pkg_name)
            os.system(cmd)

        def packages_list(self):
            cmd = 'apt list --installed'
            p = psutil.Popen(cmd.split(), stdout=PIPE)
            p.wait()
            pkgs = []
            for l in p.stdout:
                pkgs.append(l.split(b'/')[0].decode('utf-8'))
            return pkgs

    class DnfWrapper(object):
        def __init__(self):
            self.name = 'dnf'

        def update_packages(self):
            cmd = 'sudo dnf update -y && sudo dnf autoremove'
            os.system(cmd)

        def install_package(self, pkg_name):
            cmd = 'sudo dnf install {}'.format(pkg_name)
            os.system(cmd)

        def remove_package(self, pkg_name):
            cmd = 'sudo dnf remove {}'.format(pkg_name)
            os.system(cmd)

        def purge_package(self, pkg_name):
            cmd = 'sudo dnf remove {}'.format(pkg_name)
            os.system(cmd)

        def packages_list(self):
            cmd = 'dnf list installed'
            p = psutil.Popen(cmd.split(), stdout=PIPE)
            p.wait()
            pkgs = []
            for l in p.stdout:
                pkgs.append(l.split()[0].split(b'.')[0].decode('utf-8'))
            return pkgs
