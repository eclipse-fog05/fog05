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




def build(idict):
    i = f0rce.Instance(
            uuid = UUID(idict['uuid']),
            entity = UUID(idict['entity']),
            node = UUID(idict['node']))
    i.from_dict(idict)
    return i


def get(component, domain = None, entity = None, instance = None):
    assert isinstance(component, ykon.Component)
    domain = '*' if domain is None else str(domain)
    if entity is None:
        entity = '*'
    else:
        assert isinstance(entity, UUID)
        entity = str(entity)
    if instance is None:
        instance = '*'
    else:
        assert isinstance(instance, UUID)
        instance = str(instance)
    pkw = {'domain': domain, 'entity': entity, 'instance': instance}
    path = f0rce.path.instance.format(**pkw)
    return [build(i[1]) for i in component.yaks.get(path)]


def add(component, domain, instance):
    assert isinstance(component, ykon.Component)
    assert isinstance(instance, Instance)
    pkw = {'domain': str(domain), 'entity': str(instance.entity), 'instance': str(instance.uuid)}
    path = f0rce.path.instance.format(**pkw)
    component.yaks.publish(path, instance.to_dict())
    return instance


def remove(component, domain, instance):
    assert isinstance(component, ykon.Component)
    assert isinstance(instance, f0rce.Instance)
    pkw = {'domain': str(domain), 'entity': str(instance.entity), 'instance': str(instance.uuid)}
    path = f0rce.path.instance.format(**pkw)
    component.yaks.remove(path)
    return instance


def update(component, domain, instance):
    return f0rce.instance.add(component, domain, instance)




class Instance(object):
    def __init__(self, uuid = None, entity = None, network = f0rce.property.Network(), node = None, state = f0rce.enum.InstanceState.UNDEFINED):
        self.entity = None
        self.network = None
        self.node = None
        self.state = None
        self.uuid = None
        self.set_entity(entity)
        self.set_network(network)
        self.set_node(node)
        self.set_state(state)
        self.set_uuid(uuid)

    def set_entity(self, entity):
        assert isinstance(entity, UUID)
        self.entity = entity

    def set_network(self, network):
        assert isinstance(network, f0rce.property.Network)
        self.network = network

    def set_node(self, node):
        assert isinstance(node, UUID)
        self.node = node

    def set_state(self, state):
        assert isinstance(state, f0rce.enum.InstanceState)
        self.state = state.name

    def set_uuid(self, uuid):
        assert isinstance(uuid, UUID)
        self.uuid = uuid

    def from_dict(self, d):
        self.set_entity(UUID(d['entity']))
        self.set_node(UUID(d['node']))
        self.network.from_dict(d['network'])
        self.set_state(f0rce.enum.InstanceState[d['state']])
        self.set_uuid(UUID(d['uuid']))

    def to_dict(self):
        d = {}
        d['entity'] = str(self.entity)
        d['network'] = self.network.to_dict() if self.network else str(self.network)
        d['node'] = str(self.node)
        d['state'] = str(self.state)
        d['uuid'] = str(self.uuid)
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.state == other.state and
            self.node == other.node
            )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((
            self.network,
            self.node,
            self.state
            ))

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())
