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
import ykon
from uuid import UUID




def build(ndict):
    n = f0rce.Node(UUID(ndict['uuid']), ndict['name'])
    n.from_dict(ndict)
    return n


def get(component, domain, node = None):
    assert isinstance(component, ykon.Component)
    if node is None:
        node = '*'
    else:
        assert isinstance(node, UUID)
        node = str(node)
    pkw = {'domain': domain, 'node': node}
    path = f0rce.path.node.format(**pkw)
    return [build(n[1]) for n in component.yaks.get(path)]


def add(component, domain, node):
    assert isinstance(component, ykon.Component)
    assert isinstance(node, Node)
    pkw = {'domain': domain, 'node': str(node.uuid)}
    path = f0rce.path.node.format(**pkw)
    component.yaks.publish(path, node.to_dict())
    return node


def remove(component, domain, node):
    assert isinstance(component, ykon.Component)
    assert isinstance(node, f0rce.Node)
    pkw = {'domain': domain, 'node': str(node.uuid)}
    path = f0rce.path.node.format(**pkw)
    component.yaks.remove(path)
    return node


def update(component, domain, node):
    return f0rce.node.add(component, domain, node)


def get_domain(component, node):
    assert isinstance(component, ykon.Component)
    assert isinstance(node, UUID)
    pkw = {'domain': '*', 'node': str(node)}
    path = f0rce.path.node.format(**pkw)
    res = component.yaks.get(path)
    var = f0rce.util.path_to_vars(f0rce.path.node, res[1])
    return var['domain']




class Node(object):
    def __init__(self, uuid, name):
        assert isinstance(uuid, UUID)
        assert isinstance(name, str)
        self.uuid = uuid
        self.name = name
        self.acceleration = f0rce.property.Acceleration()
        self.cpu = f0rce.property.CPU()
        self.execution = f0rce.property.Execution()
        self.io = f0rce.property.IO()
        self.network = f0rce.property.Network()
        self.os = f0rce.property.OS()
        self.storage = f0rce.property.Storage()
        self.ram = f0rce.property.RAM()

    def set_acceleration(self, acceleration):
        assert isinstance(acceleration, f0rce.property.Acceleration)
        self.acceleration = acceleration
        return self.acceleration

    def set_cpu(self, cpu):
        assert isinstance(cpu, f0rce.property.CPU)
        self.cpu = cpu
        return self.cpu

    def set_execution(self, execution):
        assert isinstance(execution, f0rce.property.Execution)
        self.execution = execution
        return self.execution

    def set_io(self, io):
        assert isinstance(io, f0rce.property.IO)
        self.io = io
        return self.io

    def set_network(self, network):
        assert isinstance(network, f0rce.property.Network)
        self.network = network
        return self.network

    def set_os(self, os):
        assert isinstance(os, f0rce.property.OS)
        self.os = os
        return self.os

    def set_storage(self, storage):
        assert isinstance(storage, f0rce.property.Storage)
        self.storage = storage
        return self.storage

    def set_ram(self, ram):
        assert isinstance(ram, f0rce.property.RAM)
        self.ram = ram
        return self.ram

    def from_dict(self, d):
        self.acceleration.from_dict(d['acceleration'])
        self.cpu.from_dict(d['cpu'])
        self.execution.from_dict(d['execution'])
        self.io.from_dict(d['io'])
        self.name = d['name']
        self.network.from_dict(d['network'])
        self.os.from_dict(d['os'])
        self.storage.from_dict(d['storage'])
        self.ram.from_dict(d['ram'])
        self.uuid = UUID(d['uuid'])

    def to_dict(self):
        d = {}
        d['acceleration'] = self.acceleration.to_dict()
        d['cpu'] = self.cpu.to_dict()
        d['execution'] = self.execution.to_dict()
        d['io'] = self.io.to_dict()
        d['name'] = self.name
        d['network'] = self.network.to_dict()
        d['os'] = self.os.to_dict()
        d['storage'] = self.storage.to_dict()
        d['ram'] = self.ram.to_dict()
        d['uuid'] = str(self.uuid)
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.acceleration == other.acceleration and
            self.cpu == other.cpu and
            self.execution == other.execution and
            self.io == other.io and
            self.name == other.name and
            self.network == other.network and
            self.os == other.os and
            self.storage == other.storage and
            self.ram == other.ram and
            self.uuid == other.uuid
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.uuid)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())
