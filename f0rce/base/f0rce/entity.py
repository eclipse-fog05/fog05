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




def build(edict):
    e = f0rce.Entity(uuid = UUID(edict['uuid']), name = edict['name'])
    e.from_dict(edict)
    return e


def get(component, domain, entity = None):
    assert isinstance(component, ykon.Component)
    if entity is None:
        entity = '*'
    else:
        assert isinstance(entity, UUID)
        entity = str(entity)
    pkw = {'domain': domain, 'entity': entity}
    path = f0rce.path.entity.format(**pkw)
    return [build(n[1]) for n in component.yaks.get(path)]


def add(component, domain, entity):
    assert isinstance(component, ykon.Component)
    assert isinstance(entity, Entity)
    pkw = {'domain': domain, 'entity': str(entity.uuid)}
    path = f0rce.path.entity.format(**pkw)
    component.yaks.publish(path, entity.to_dict())
    return entity


def remove(component, domain, entity):
    assert isinstance(component, ykon.Component)
    assert isinstance(entity, f0rce.Entity)
    pkw = {'domain': domain, 'entity': str(entity.uuid)}
    path = f0rce.path.entity.format(**pkw)
    component.yaks.remove(path)
    return entity


def update(component, domain, entity):
    assert isinstance(entity, ykon.network.Node)
    pkw = {'domain': domain, 'entity': str(entity.uuid)}
    path = f0rce.path.entity_upd.format(**pkw)
    component.yaks.publish(path, entity.to_dict())
    return entity



class Requirement(object):
    def __init__(self):
        self.acceleration = f0rce.property.Acceleration()
        self.cpu = f0rce.property.CPU()
        self.disk = f0rce.property.Disk()
        self.entity = set()
        self.io = f0rce.property.IO()
        self.ram = f0rce.property.RAM()
        self.runtime = f0rce.property.Runtime()

    def add_entity(self, entity_uuid):
        assert isinstance(entity_uuid, UUID)
        self.entity.add(str(entity_uuid))

    def from_dict(self, d):
        self.acceleration.from_dict(d['acceleration'])
        self.cpu.from_dict(d['cpu'])
        self.disk.from_dict(d['disk'])
        self.io.from_dict(d['io'])
        self.ram.from_dict(d['ram'])
        self.runtime.from_dict(d['runtime'])

    def to_dict(self):
        d = {}
        d['acceleration'] = self.acceleration.to_dict()
        d['cpu'] = self.cpu.to_dict()
        d['disk'] = self.disk.to_dict()
        d['io'] = self.io.to_dict()
        d['ram'] = self.ram.to_dict()
        d['runtime'] = self.runtime.to_dict()
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.cpu == other.cpu and
            self.ram == other.ram and
            self.disk == other.disk and
            self.runtime == other.runtime
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.cpu,
            self.ram,
            self.disk,
            self.runtime
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Configuration(object):
    def __init__(self):
        self.image = f0rce.property.Image()
        self.migration = f0rce.property.Migration()
        self.network = f0rce.property.Network()

    def from_dict(self, d):
        self.image.from_dict(d['image'])
        self.migration.from_dict(d['migration'])
        self.network.from_dict(d['network'])

    def to_dict(self):
        d = {}
        d['image'] = self.image.to_dict()
        d['migration'] = self.migration.to_dict()
        d['network'] = self.network.to_dict()
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.network == other.network and
            self.image == other.image and
            self.migration == other.migration
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.network,
            self.image,
            self.migration
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())


class Entity(object):
    def __init__(self, uuid, name):
        assert isinstance(uuid, UUID)
        self.uuid = uuid
        self.name = name
        self.requirement = f0rce.entity.Requirement()
        self.configuration = f0rce.entity.Configuration()

    def from_dict(self, d):
        self.uuid = UUID(d['uuid'])
        self.name = d['name']
        self.requirement.from_dict(d['requirement'])
        self.configuration.from_dict(d['configuration'])

    def to_dict(self):
        d = {}
        d['uuid'] = str(self.uuid)
        d['name'] = self.name
        d['requirement'] =self.requirement.to_dict()
        d['configuration'] = self.configuration.to_dict()
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.uuid == other.uuid and
            self.name == other.name and
            self.requirement == other.requirement and
            self.configuration == other.configuration
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.uuid)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())
