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
# Contributors: Luca Cominardi, University Carlos III of Madrid.

import f0rce
import json


class Acceleration(object):
    def __init__(self):
        self.accelerator = {}

    def add_accelerator(self, accelerator):
        assert isinstance(accelerator, f0rce.property.Accelerator)
        self.accelerator[accelerator.type] = accelerator

    def del_accelerator(self, accelerator):
        assert isinstance(accelerator, f0rce.property.Accelerator)
        del self.accelerator[accelerator.type]

    def from_dict(self, d):
        for v in d.values():
            accelerator = f0rce.property.Accelerator()
            accelerator.from_dict(v)
            self.add_accelerator(accelerator)

    def to_dict(self):
        d = {c.id:c.to_dict() for c in self.accelerator.values()}
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            set(self.accelerator.keys()) == set(other.accelerator.keys()) and
            all((self.accelerator[k] == other.accelerator[k] for k in self.accelerator.keys()))
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            h for h in self.accelerator.values()
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Accelerator(object):
    def __init__(self, type = None):
        self.type = None
        self.set_type(type)

    def set_type(self, type):
        self.type = type

    def from_dict(self, d):
        self.set_type(d['type'])

    def to_dict(self):
        d = {}
        d['type'] = self.type
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.type == other.type
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.type)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Core(object):
    def __init__(self, id = None, arch = None, freq = None, model = None):
        self.arch = None
        self.freq = None
        self.id = None
        self.model = None
        self.set_arch(arch)
        self.set_freq(freq)
        self.set_id(id)
        self.set_model(model)

    def set_arch(self, arch):
        self.arch = arch

    def set_freq(self, freq):
        self.freq = freq

    def set_id(self, id):
        self.id = id

    def set_model(self, model):
        self.model = model

    def from_dict(self, d):
        self.set_id(d['id'])
        self.set_arch(d['arch'])
        self.set_freq(d['freq'])
        self.set_model(d['model'])

    def to_dict(self):
        d = {}
        d['id'] = self.id
        d['arch'] = self.arch
        d['freq'] = self.freq
        d['model'] = self.model
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.id == other.id and
            self.arch == other.arch and
            self.freq == other.freq and
            self.model == other.model
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.id,
            self.arch,
            self.freq,
            self.model
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class CPU(object):
    def __init__(self):
        self.core = {}

    def add_core(self, core):
        assert isinstance(core, f0rce.property.Core)
        self.core[core.id] = core

    def del_core(self, core):
        assert isinstance(core, f0rce.property.Core)
        del self.core[core.id]

    def from_dict(self, d):
        for v in d.values():
            core = f0rce.property.Core()
            core.from_dict(v)
            self.add_core(core)

    def to_dict(self):
        d = {c.id:c.to_dict() for c in self.core.values()}
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            set(self.core.keys()) == set(other.core.keys()) and
            all((self.core[k] == other.core[k] for k in self.core.keys()))
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            h for h in self.core.values()
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Disk(object):
    def __init__(self, device = None, size = 0, mountpoint = None, filesystem = None):
        self.device = None
        self.filesystem = None
        self.mountpoint = None
        self.size = None
        self.set_device(device)
        self.set_filesystem(filesystem)
        self.set_mountpoint(mountpoint)
        self.set_size(size)

    def set_device(self, device):
        self.device = device

    def set_filesystem(self, filesystem):
        self.filesystem = filesystem

    def set_mountpoint(self, mountpoint):
        self.mountpoint = mountpoint

    def set_size(self, size):
        assert size >= 0
        self.size = size

    def from_dict(self, d):
        self.set_device(d['device'])
        self.set_size(d['size'])
        self.set_mountpoint(d['mountpoint'])
        self.set_filesystem(d['filesystem'])

    def to_dict(self):
        d = {}
        d['device'] = self.device
        d['size'] = self.size
        d['mountpoint'] = self.mountpoint
        d['filesystem'] = self.filesystem
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.device == other.device and
            self.size == other.size and
            self.mountpoint == other.mountpoint and
            self.filesystem == other.filesystem
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.device,
            self.size,
            self.mountpoint,
            self.filesystem
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Execution(object):
    def __init__(self):
        self.runtime = {}

    def add_runtime(self, runtime):
        assert isinstance(runtime, f0rce.property.Runtime)
        self.runtime[runtime.name] = runtime

    def del_runtime(self, runtime):
        assert isinstance(runtime, f0rce.property.Runtime)
        del self.runtime[runtime.name]

    def from_dict(self, d):
        for v in d.values():
            runtime = f0rce.property.Runtime()
            runtime.from_dict(v)
            self.add_runtime(runtime)

    def to_dict(self):
        d = {runtime.name:runtime.to_dict() for runtime in self.runtime.values()}
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            set(self.runtime.keys()) == set(other.runtime.keys()) and
            all((self.runtime[k] == other.runtime[k] for k in self.runtime.keys()))
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            h for h in self.runtime.values()
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Image(object):
    def __init__(self, uri = None, format = None, checksum = None):
        self.uri = None
        self.format = None
        self.checksum = None
        self.set_uri(uri)
        self.set_format(format)
        self.set_checksum(checksum)

    def set_uri(self, uri):
        self.uri = uri

    def set_format(self, format):
        self.format = format

    def set_checksum(self, checksum):
        self.checksum = checksum

    def from_dict(self, d):
        self.set_uri(d['uri'])
        self.set_format(d['format'])
        self.set_checksum(d['checksum'])

    def to_dict(self):
        d = {}
        d['uri'] = self.uri
        d['format'] = self.format
        d['checksum'] = self.checksum
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.uri == other.uri and
            self.format == other.format and
            self.checksum == other.checksum
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.checksum)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Interface(object):
    def __init__(self, name = None, type = f0rce.enum.InterfaceType.UNKNOWN):
        self.ipv4 = set()
        self.ipv6 = set()
        self.mac = f0rce.property.InterfaceMAC()
        self.name = None
        self.type = None
        self.set_name(name)
        self.set_type(type)

    def set_mac(self, mac):
        assert isinstance(mac, f0rce.property.InterfaceMAC)
        self.mac = mac

    def set_name(self, name):
        self.name = name

    def set_type(self, type):
        assert isinstance(type, f0rce.enum.InterfaceType)
        self.type = type.name

    def add_ipv4(self, ipv4):
        assert isinstance(ipv4, f0rce.property.IPv4)
        self.ipv4.add(ipv4)
        return ipv4

    def del_ipv4(self, ipv4):
        assert isinstance(ipv4, f0rce.property.IPv4)
        self.ipv4.remove(ipv4)

    def add_ipv6(self, ipv6):
        assert isinstance(ipv6, f0rce.property.IPv6)
        self.ipv6.add(ipv6)
        return ipv6

    def del_ipv6(self, ipv6):
        assert isinstance(ipv6, f0rce.property.IPv6)
        self.ipv6.remove(ipv6)

    def from_dict(self, d):
        for v in d['ipv4']:
            ipv4 = f0rce.property.IPv4()
            ipv4.from_dict(v)
            self.add_ipv4(ipv4)
        for v in d['ipv6']:
            ipv6 = f0rce.property.IPv6()
            ipv6.from_dict(v)
            self.add_ipv6(ipv6)
        mac = f0rce.property.InterfaceMAC()
        mac.from_dict(d['mac'])
        self.set_mac(mac)
        self.set_name(d['name'])
        self.set_type(f0rce.enum.InterfaceType[d['type']])

    def to_dict(self):
        d = {}
        d['ipv4'] = [ipv4.to_dict() for ipv4 in self.ipv4]
        d['ipv6'] = [ipv6.to_dict() for ipv6 in self.ipv6]
        d['mac'] = self.mac.to_dict()
        d['name'] = self.name
        d['type'] = self.type
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.ipv4 == other.ipv4 and
            self.ipv6 == other.ipv6 and
            self.mac == other.mac and
            self.name == other.name and
            self.type == other.type
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class InterfaceMAC(object):
    def __init__(self, address = None, bus = None, mtu = 1500, speed = 0, type = f0rce.enum.InterfaceMACType.UNKNOWN):
        self.address = None
        self.bus = None
        self.mtu = None
        self.speed = None
        self.type = None
        self.set_address(address)
        self.set_bus(bus)
        self.set_mtu(mtu)
        self.set_speed(speed)
        self.set_type(type)

    def set_address(self, address):
        self.address = address

    def set_bus(self, bus):
        self.bus = bus

    def set_mtu(self, mtu):
        assert mtu >= 0
        self.mtu = mtu

    def set_speed(self, speed):
        assert speed >= 0
        self.speed = speed

    def set_type(self, type):
        assert isinstance(type, f0rce.enum.InterfaceMACType)
        self.type = type.name

    def from_dict(self, d):
        self.set_address(d['address'])
        self.set_mtu(d['mtu'])
        self.set_speed(d['speed'])
        self.set_type(f0rce.enum.InterfaceMACType[d['type']])

    def to_dict(self):
        d = {}
        d['address'] = str(self.address)
        d['mtu'] = self.mtu
        d['speed'] = self.speed
        d['type'] = str(self.type)
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.address == other.address and
            self.mtu == other.mtu and
            self.speed == other.speed and
            self.type == other.type
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.hwaddr)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())



class IO(object):
    def __init__(self):
        self.device = {}

    def add_device(self, device):
        assert isinstance(device, f0rce.property.IOdevice)
        self.device[device.id] = device

    def del_device(self, device):
        assert isinstance(device, f0rce.property.IOdevice)
        del self.device[device.id]

    def from_dict(self, d):
        for v in d.values():
            device = f0rce.property.IOdevice()
            device.from_dict(v)
            self.add_device(device)

    def to_dict(self):
        d = {c.id:c.to_dict() for c in self.device.values()}
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            set(self.device.keys()) == set(other.device.keys()) and
            all((self.device[k] == other.device[k] for k in self.device.keys()))
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            h for h in self.device.values()
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class IOdevice(object):
    def __init__(self, type = None):
        self.type = None
        self.set_type(type)

    def set_type(self, type):
        self.type = type

    def from_dict(self, d):
        self.set_type(d['type'])

    def to_dict(self):
        d =  {}
        d['type'] = self.type
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.type == other.type
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.type
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class IPv4(object):
    def __init__(self, address = None, default = False, netmask = None):
        self.address = None
        self.default = None
        self.netmask = None
        self.set_address(address)
        self.set_default(default)
        self.set_netmask(netmask)

    def set_address(self, address):
        self.address = address

    def set_default(self, default):
        self.default = default

    def set_netmask(self, netmask):
        self.netmask = netmask

    def from_dict(self, d):
        self.set_address(d['address'])
        self.set_default(d['default'])
        self.set_netmask(d['netmask'])

    def to_dict(self):
        d = {}
        d['address'] = self.address
        d['default'] = self.default
        d['netmask'] = self.netmask
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.address == other.address and
            self.netmask == other.netmask
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.address,
            self.netmask
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class IPv6(object):
    def __init__(self, address = None, default = False, netmask = None):
        self.address = None
        self.default = None
        self.netmask = None
        self.set_address(address)
        self.set_default(default)
        self.set_netmask(netmask)

    def set_address(self, address):
        self.address = address

    def set_default(self, default):
        self.default = default

    def set_netmask(self, netmask):
        self.netmask = netmask

    def from_dict(self, d):
        self.set_address(d['address'])
        self.set_default(d['default'])
        self.set_netmask(d['netmask'])

    def to_dict(self):
        d = {}
        d['address'] = self.address
        d['default'] = self.default
        d['netmask'] = self.netmask
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.address == other.address and
            self.netmask == other.netmask
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.address,
            self.netmask
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Migration(object):
    def __init__(self, type = None):
        self.type = None
        self.set_type(type)

    def set_type(self, type):
        self.type = type

    def from_dict(self, d):
        self.set_type(d['type'])

    def to_dict(self):
        d = {}
        d['type'] = self.type
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.type == other.type
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.type
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Network(object):
    def __init__(self):
        self.intf = {}

    def add_intf(self, interface):
        assert isinstance(interface, f0rce.property.Interface)
        self.intf[interface.name] = interface
        return interface

    def del_intf(self, interface):
        assert isinstance(interface, f0rce.property.Interface)
        del self.intf[interface.name]

    def from_dict(self, d):
        for v in d.values():
            intf = f0rce.property.Interface()
            intf.from_dict(v)
            self.add_intf(intf)

    def to_dict(self):
        d = {intf.name:intf.to_dict() for intf in self.intf.values()}
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            set(self.intf.keys()) == set(other.intf.keys()) and
            all((self.intf[k] == other.intf[k] for k in self.intf.keys()))
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            i for i in self.intf.values()
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class OS(object):
    def __init__(self, name = None, status = None, version = None):
        self.name = None
        self.status = None
        self.version = None
        self.set_name(name)
        self.set_status(status)
        self.set_version(version)

    def set_name(self, name):
        self.name = name

    def set_status(self, status):
        self.status = status

    def set_version(self, version):
        self.version = version

    def from_dict(self, d):
        self.set_name(d['name'])
        self.set_status(d['status'])
        self.set_version(d['version'])

    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['status'] = self.status
        d['version'] = self.version
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.name == other.name and
            self.status == other.status and
            self.version == other.version
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.name,
            self.status,
            self.version
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Runtime(object):
    def __init__(self, name = None, status = None, version = None):
        self.name = None
        self.status = None
        self.version = None
        self.set_name(name)
        self.set_status(status)
        self.set_version(version)

    def set_name(self, name):
        self.name = name

    def set_status(self, status):
        self.status = status

    def set_version(self, version):
        self.version = version

    def from_dict(self, d):
        self.set_name(d['name'])
        self.set_status(d['status'])
        self.set_version(d['version'])

    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['status'] = self.status
        d['version'] = self.version
        return d


    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.name == other.name and
            self.status == other.status and
            self.version == other.version
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.name,
            self.status,
            self.version
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Storage(object):
    def __init__(self):
        self.disk = {}

    def add_disk(self, disk):
        assert isinstance(disk, f0rce.property.Disk)
        self.disk[disk.device] = disk

    def del_disk(self, disk):
        assert isinstance(disk, f0rce.property.Disk)
        del self.disk[disk.device]

    def from_dict(self, d):
        for v in d.values():
            disk = f0rce.property.Disk()
            disk.from_dict(v)
            self.add_disk(disk)

    def to_dict(self):
        d = {disk.device:disk.to_dict() for disk in self.disk.values()}
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            set(self.disk.keys()) == set(other.disk.keys()) and
            all((self.disk[k] == other.disk[k] for k in self.disk.keys()))
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            d for d in self.disk.values()
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class RAM(object):
    def __init__(self, size = 0):
        self.size = None
        self.set_size(size)

    def set_size(self, size):
        assert size >=0
        self.size = size

    def from_dict(self, d):
        self.set_size(d['size'])

    def to_dict(self):
        d = {}
        d['size'] = self.size
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.size == other.size
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.size)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())
