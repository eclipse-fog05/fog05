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




def build(ldict):
    link = f0rce.Link(
            uuid = UUID(ldict['uuid']),
            src_node_uuid = UUID(ldict['src']['node']),
            src_intf_name = ldict['src']['intf'],
            dst_node_uuid = UUID(ldict['dst']['node']),
            dst_intf_name = ldict['dst']['intf'])
    return link


def get(component, domain = None, node = None, link = None):
    assert isinstance(component, ykon.Component)
    domain = '*' if domain is None else str(domain)
    if node is None:
        node = '*'
    else:
        assert isinstance(node, UUID)
        node = str(node)
    if link is None:
        link = '*'
    else:
        assert isinstance(link, UUID)
        link = str(link)
    pkw = {'domain': domain, 'node': node, 'link': link}
    path = f0rce.path.link.format(**pkw)
    return [build(l[1]) for l in component.yaks.get(path)]


def add(component, domain, link):
    assert isinstance(component, ykon.Component)
    assert isinstance(link, f0rce.Link)
    pkw = {'domain': domain, 'node': str(link.src_node_uuid), 'link': str(link.uuid)}
    path = f0rce.path.link.format(**pkw)
    component.yaks.publish(path, link.to_dict())
    return link


def remove(component, domain, link):
    assert isinstance(component, ykon.Component)
    assert isinstance(link, f0rce.Link)
    pkw = {'domain': domain, 'node': str(link.src_node_uuid), 'link': str(link.uuid)}
    path = f0rce.path.link.format(**pkw)
    component.yaks.remove(path)
    return link


def update(component, domain, link):
    assert isinstance(component, ykon.Component)
    assert isinstance(link, f0rce.Link)
    pkw = {'domain': domain, 'node': str(link.src_node_uuid), 'link': str(link.uuid)}
    path = f0rce.path.link.format(**pkw)
    component.yaks.publish(path, link.to_dict())
    return link


def get_domain(component, link):
    assert isinstance(component, ykon.Component)
    assert isinstance(link, UUID)
    pkw = {'domain': '*', 'node': '*', 'link': str(link)}
    path = f0rce.path.link.format(**pkw)
    res = component.yaks.get(path)
    var = f0rce.util.path_to_vars(f0rce.path.node, res[1])
    return var['domain']




class Link:
    def __init__(self, uuid, src_node_uuid, src_intf_name, dst_node_uuid, dst_intf_name):
        assert isinstance(uuid, UUID)
        assert isinstance(src_node_uuid, UUID)
        assert isinstance(src_intf_name, str)
        assert isinstance(dst_node_uuid, UUID)
        assert isinstance(dst_intf_name, str)
        self.uuid = uuid
        self.src_node_uuid = src_node_uuid
        self.src_intf_name = src_intf_name
        self.dst_node_uuid = dst_node_uuid
        self.dst_intf_name = dst_intf_name

    def from_dict(self, d):
        self.uuid = UUID(d['uuid'])
        self.src_node_uuid = UUID(d['src']['node'])
        self.src_intf_name = d['src']['intf']
        self.dst_node_uuid = UUID(d['dst']['node'])
        self.dst_intf_name = d['dst']['intf']

    def to_dict(self):
        d = {}
        d['uuid'] = str(self.uuid)
        d['src'] = {
                'node': str(self.src_node_uuid),
                'intf': self.src_intf_name
                }
        d['dst'] = {
                'node': str(self.dst_node_uuid),
                'intf': self.dst_intf_name
                }
        return d

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__ and
            self.src_node_uuid == other.src_node_uuid and
            self.src_intf_name == other.src_intf_name and
            self.dst_node_uuid == other.dst_node_uuid and
            self.dst_intf_name == other.dst_intf_name and
            self.uuid == other.uuid
            )

    def __ne__(self, other):
        return not self == other

    def hash(self):
        return hash(self.uuid)

    def __repr__(self):
        return f0rce.util.dict_to_str(self.to_dict())
