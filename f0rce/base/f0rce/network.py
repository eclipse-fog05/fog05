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
import networkx as nx
from uuid import UUID
from yaks import ChangeKind




class Network(object):
    def __init__(self, component, domain):
        assert isinstance(component, ykon.Component)
        self.component = component
        self.domain = domain
        self.graph = nx.DiGraph()
        self.node = {}
        self.link = {}

    def __link(self, path, value, event):
        uuid = f0rce.util.path_to_vars(template = f0rce.path.link, path = path)
        if event is ChangeKind.PUT:
            self.__add_link(f0rce.link.build(value))
        elif event is ChangeKind.UPDATE and uuid['link'] in self.link:
            self.__upd_link(f0rce.link.build(value))
        elif event is ChangeKind.REMOVE and uuid['link'] in self.link:
            self.__del_link(self.link[uuid['link']])

    def __node(self, path, value, event):
        uuid = f0rce.util.path_to_vars(template = f0rce.path.node, path = path)
        if event is ChangeKind.PUT:
            self.__add_node(f0rce.node.build(value))
        elif event is ChangeKind.UPDATE and uuid['node'] in self.node:
            self.__upd_node(f0rce.node.build(value))
        elif event is ChangeKind.REMOVE and uuid['node'] in self.node:
            self.__del_node(self.node[uuid['node']])

    def register(self):
        nodes = f0rce.node.get(self.component, self.domain)
        for n in nodes:
            self.__add_node(n)
        links = f0rce.link.get(self.component, self.domain)
        for l in links:
            self.__add_link(l)
        pkw = {'domain': self.domain, 'node': '*'}
        self.component.subscription.add(f0rce.path.node.format(**pkw), self.__node)
        pkw = {'domain': self.domain, 'node': '*', 'link': '*'}
        self.component.subscription.add(f0rce.path.link.format(**pkw), self.__link)

    def unregister(self):
        for l in list(self.link.values()):
            self.del_link(l)
        for n in list(self.node.values()):
            self.del_node(n)

    def __add_link(self, link):
        assert isinstance(link, f0rce.Link)
        if str(link.src_node_uuid) in self.node and str(link.dst_node_uuid) in self.node:
            src_node = self.node[str(link.src_node_uuid)]
            dst_node = str(link.dst_node_uuid)
            self.component.log.info('Adding link: {}'.format(str(link.uuid)))
            self.graph.add_edge(src_node, dst_node, link = link)
            self.link[str(link.uuid)] = link
            return link
        return None

    def __add_node(self, node):
        assert isinstance(node, f0rce.Node)
        self.component.log.info('Adding node: {}'.format(str(node.uuid)))
        self.graph.add_node(node)
        self.node[str(node.uuid)] = node
        return node

    def __del_link(self, link):
        assert isinstance(link, f0rce.Link)
        if str(link.uuid) in self.link:
            self.component.log.info('Removing link: {}'.format(str(link.uuid)))
            del self.link[str(link.uuid)]
            return link
        return None

    def __del_node(self, node):
        assert isinstance(node, f0rce.Node)
        if str(node.uuid) in self.node:
            self.component.log.info('Removing node: {}'.format(str(node.uuid)))
            del self.node[str(node.uuid)]
            return node
        return None

    def __upd_link(self, link):
        assert isinstance(link, f0rce.Link)
        if str(link.uuid) in self.link:
            self.component.log.info('Updating link: {}'.format(str(link.uuid)))
            # TO FIX
            return self.__add_link(self, link)
        return None

    def __upd_node(self, node):
        assert isinstance(node, f0rce.Node)
        if str(node.uuid) in self.node:
            self.component.log.info('Updating node: {}'.format(str(node.uuid)))
            # TO FIX
            return self.__add_node(node)
        return None

    def add_link(self, link):
        assert isinstance(link, f0rce.Link)
        f0rce.link.add(self.component, self.domain, link)
        return link

    def add_node(self, node):
        assert isinstance(node, f0rce.Node)
        f0rce.node.add(self.component, self.domain, node)
        return node

    def del_link(self, link):
        assert isinstance(link, f0rce.Link)
        if str(link.uuid) in self.link:
            f0rce.link.remove(self.component, self.domain, link)
            return link
        return None

    def del_node(self, node):
        assert isinstance(node, f0rce.Node)
        if str(node.uuid) in self.node:
            f0rce.node.remove(self.component, self.domain, node)
            return node
        return None

    def upd_link(self, link):
        assert isinstance(link, f0rce.Link)
        if str(link.uuid) in self.link:
            # TO FIX
            f0rce.link.add(self.component, self.domain, link)
            return link
        return None

    def upd_node(self, node):
        assert isinstance(node, f0rce.Node)
        if str(node.uuid) in self.node:
            f0rce.node.update(self.component, self.domain, node)
            return node
        return None

    def get_link(self, uuid):
        assert isinstance(uuid, UUID)
        if str(uuid) in self.link:
            return self.link[str(uuid)]
        return None

    def get_node(self, uuid):
        assert isinstance(uuid, UUID)
        if str(uuid) in self.node:
            return self.node[str(uuid)]
        return None

    def find_link(self, src = None, dst = None):
        assert src is not None or dst is not None
        links = []
        if src is None and dst is not None:
            assert isinstance(dst, UUID)
            for l in self.graph.in_edges(str(dst)):
                links.extend(self.find_link(UUID(l[0]), UUID(l[1])))
        elif src is not None and dst is None:
            assert isinstance(src, UUID)
            for l in self.graph.out_edges(str(src)):
                links.extend(self.find_link(UUID(l[0]), UUID(l[1])))
        else:
            assert isinstance(src, UUID)
            assert isinstance(dst, UUID)
            if self.graph.has_edge(str(src), str(dst)):
                links.append(self.graph.edges[str(src), str(dst)]['link'])
        return links

    def find_node(self, propdict):
        nodes = []
        for n in self.graph.nodes():
            found = False
            for name,value in propdict.items():
                if hasattr(n, 'find_'+name):
                    res = getattr(n, 'find_'+name)(**value)
                    if res:
                        found = True
                    else:
                        found = False
                        break
                else:
                    found = False
                    break
            if found:
                nodes.append(n)
        return nodes
