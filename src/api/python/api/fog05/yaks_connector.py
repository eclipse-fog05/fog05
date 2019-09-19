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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc.
# Connector and helper for YAKS


import json
import concurrent.futures
from threading import Thread
from fog05.interfaces import Constants
from yaks import Yaks, Value, Encoding, Change



class GAD(object):
    def __init__(self, workspace, prefix):
        self.ws = workspace
        self.prefix = prefix
        self.listeners = []
        self.evals = []

    def unsubscribe(self, subid):
        if subid in self.listeners:
            self.ws.unsubscribe(subid)
            self.listeners.remove(subid)

    def unregister_eval(self, path):
        if path in self.evals:
            self.ws.unregister_eval(path)
            self.evals.remove(path)

    def close(self):
        for s in self.listeners:
            self.ws.unsubscribe(s)
        for ep in self.evals:
            self.ws.unregister_eval(ep)

    # SYSTEM

    def get_sys_info_path(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'info'])

    def get_sys_configuration_path(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'configuration'])

    def get_all_users_selector(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'users', '*'])

    def get_user_info_path(self, sysid, userid):
        return Constants.create_path(
            [self.prefix, sysid, 'users', userid, 'info'])

    # TENANTS

    def get_all_tenants_selector(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'tenants', '*'])

    def get_tenant_info_path(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'info'])

    def get_tenant_configuration_path(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'configuration'])

    # CATALOG

    def get_catalog_atomic_entity_info_path(self, sysid, tenantid, aeid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'atomic-entities', aeid, 'info'])

    def get_catalog_all_atomic_entities_selector(self, sysid, tenantid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'atomic-entities', '*', 'info'])

    def get_catalog_fdu_info_path(self, sysid, tenantid, fduid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'fdu', fduid, 'info'])

    def get_catalog_all_fdu_selector(self, sysid, tenantid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'fdu', '*', 'info'])

    def get_catalog_entity_info_path(self, sysid, tenantid, aeid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'entities', aeid, 'info'])

    def get_catalog_all_entities_selector(self, sysid, tenantid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'entities', '*', 'info'])

    # RECORDS

    def get_records_atomic_entity_instance_info_path(self, sysid, tenantid, aeid, instanceid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'records', 'atomic-entities', aeid, 'instances', instanceid, 'info'])

    def get_records_all_atomic_entity_instances_selector(self, sysid, tenantid, aeid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'records', 'atomic-entities', aeid, 'instances','*', 'info'])

    def get_records_all_atomic_entities_instances_selector(self, sysid, tenantid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'atomic-entities', '*', 'instances', '*' ,'info'])

    def get_records_entity_instance_info_path(self, sysid, tenantid, aeid, instanceid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'records', 'entities', aeid, 'instances', instanceid, 'info'])

    def get_records_all_entity_instances_selector(self, sysid, tenantid, aeid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'records', 'entities', aeid, 'instances','*', 'info'])

    def get_records_all_entities_instances_selector(self, sysid, tenantid):
        return Constants.create_path([self.prefix, sysid, 'tenants',
            tenantid, 'catalog', 'entities', '*', 'instances', '*' ,'info'])

    # Nodes

    def get_all_nodes_selector(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'nodes', '*', 'info'])

    def get_node_info_path(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'info'])

    def get_node_configuration_path(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'configuration'])

    def get_node_status_path(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'status'])

    def get_node_plugins_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'plugins', '*', 'info'])

    def get_node_plugins_subscriber_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'plugins', '**'])

    def get_node_plugin_info_path(self, sysid, tenantid, nodeid, pluginid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'plugins',
                                      pluginid, 'info'])

    def get_node_plugin_eval_path(self, sysid, tenantid, nodeid, pluginid,
                                  func_name):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'plugins',
                                      pluginid, 'exec', func_name])

    # Node FDU or Records

    def get_node_fdu_info_path(self, sysid, tenantid, nodeid, fduid, instanceid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'fdu',fduid ,
                                      'instances', instanceid, 'info'])

    def get_node_fdu_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'fdu', '*', 'instances',
                                      '*', 'info'])

    def get_node_fdu_instances_selector(self, sysid, tenantid, nodeid, fduid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'fdu', fduid, 'instances',
                                      '*', 'info'])

    def get_node_fdu_instance_selector(self, sysid, tenantid, nodeid, instid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'fdu', '*', 'instances',
                                      instid, 'info'])

    def get_fdu_instance_selector(self, sysid, tenantid, instid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', '*', 'fdu', '*', 'instances',
                                      instid, 'info'])

    # Networks

    def get_all_networks_selector(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'networks', '*', 'info'])

    def get_entity_all_instances_selector(self, sysid, tenantid, entityid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
             'entities',  entityid, 'instances', '*'])

    def get_entity_info_path(self, sysid, tenantid, entityid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'entities', entityid, 'info'])

    def get_network_info_path(self, sysid, tenantid, networkid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'networks', networkid, 'info'])

    def get_network_port_info_path(self, sysid, tenantid, portid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'networks', 'ports', portid, 'info'])

    def get_all_ports_selector(self, sysid, tenantid):
        return Constants.create_path([
            self.prefix,sysid ,'tenants', tenantid,'networks','ports',
            '*', 'info'])

    def get_network_router_info_path(self, sysid, tenantid, routerid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'networks', 'routers', routerid, 'info'])

    def get_all_routers_selector(self, sysid, tenantid):
        return Constants.create_path([
            self.prefix,sysid ,'tenants', tenantid,'networks','routers',
            '*', 'info'])

    # Images

    def get_image_info_path(self, sysid, tenantid, imageid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'image', imageid, 'info'
        ])

    def get_all_image_selector(self, sysid, tenantid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'image', '*', 'info'
        ])

    # Node Images

    def get_node_image_info_path(self, sysid, tenantid, nodeid, imageid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'nodes', nodeid,
             'image', imageid, 'info'
        ])

    def get_all_node_image_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'nodes', nodeid,
            'image', '*', 'info'
        ])

    # Flavor

    def get_flavor_info_path(self, sysid, tenantid, flavorid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'flavor', flavorid, 'info'
        ])

    def get_all_flavor_selector(self, sysid, tenantid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'flavor', '*', 'info'
        ])

    # Node Flavor

    def get_node_flavor_info_path(self, sysid, tenantid, nodeid, flavorid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'nodes', nodeid,
             'flavor', flavorid, 'info'
        ])

    def get_all_node_flavor_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'nodes', nodeid,
            'flavor', '*', 'info'
        ])

    # Node Network

    def get_node_network_floating_ip_info_path(self, sysid, tenantid, nodeid, ipid):
         return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'nodes', nodeid,
            'networks', 'floating-ips', ipid, 'info'])

    def get_node_all_network_floating_ips_selector(self, sysid, tenantid, nodeid):
         return Constants.create_path([
            self.prefix, sysid, 'tenants', tenantid, 'nodes', nodeid,
            'networks', 'floating-ips', '*', 'info'])

    def get_node_network_ports_selector(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
            'nodes', '*', 'networks', 'ports', '*', 'info'])

    def get_node_network_port_info_path(self, sysid, tenantid, nodeid, portid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
            'nodes', nodeid, 'networks', 'ports', portid, 'info'])

    def get_node_network_routers_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
            'nodes', nodeid, 'networks', 'routers', '*', 'info'])

    def get_node_network_router_info_path(self, sysid, tenantid, nodeid, routerid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
            'nodes', nodeid, 'networks', 'routers', routerid, 'info'])

    def get_node_network_info_path(self, sysid, tenantid, nodeid, networkid):
        return Constants.create_path([
            self.prefix,sysid ,'tenants', tenantid,
            'nodes', nodeid, 'networks', networkid, 'info'])


    # Evals

    def dict2args(self, d):
        i = 0
        b = ''
        for k in d:
            v = d.get(k)
            if isinstance(v,(dict, list)):
                v = json.dumps(v)
            if i == 0:
                b = b + '{}={}'.format(k, v)
            else:
                b = b + ';{}={}'.format(k, v)
            i = i + 1
        return '('+b+')'

    def get_agent_exec_path(self, sysid, tenantid, nodeid, func_name):
        return Constants.create_path([self.prefix, sysid, 'tenants',
        tenantid, 'nodes', nodeid, 'agent', 'exec', func_name])

    def get_agent_exec_path_with_params(self, sysid, tenantid, nodeid, func_name, params):
        if len(params) > 0:
            p = self.dict2args(params)
            f = func_name + '?' + p
        else:
            f = func_name
        return Constants.create_path([self.prefix, sysid, 'tenants',
        tenantid, 'nodes', nodeid, 'agent', 'exec',f])

    # ID Extraction

    def extract_userid_from_path(self, path):
        return path.split('/')[4]

    def extract_tenantid_from_path(self, path):
        return path.split('/')[4]

    def extract_entityid_from_path(self, path):
        return path.split('/')[7]

    def extract_aeid_from_path(self, path):
        return path.split('/')[7]

    def extract_atomic_entity_instanceid_from_path(self, path):
        return path.split('/')[9]

    def extract_entity_id_from_path(self, path):
        return path.split('/')[7]

    def extract_entity_instanceid_from_path(self, path):
        return path.split('/')[9]

    def extract_fduid_from_path(self, path):
        return path.split('/')[7]

    def extract_nodeid_from_path(self, path):
        return path.split('/')[6]

    def extract_plugin_from_path(self, path):
        return path.split('/')[8]

    def extract_node_fduid_from_path(self, path):
        return path.split('/')[8]

    def extract_node_instanceid_from_path(self, path):
        return path.split('/')[10]

    def extract_node_port_id_from_path(self, path):
        return path.split('/')[9]

    def extract_node_router_id_from_path(self, path):
        return path.split('/')[9]

    def extract_node_floatingid_from_path(self, path):
        return path.split('/')[9]

    # System

    def get_sys_info(self, sysid):
        s = self.get_sys_info_path(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_sys_info')
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_sys_config(self, sysid):
        s = self.get_sys_configuration_path(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_sys_config')
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_all_users_ids(self, sysid):
        s = self.get_all_users_selector(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: self.extract_userid_from_path(x[0]), res)
        return list(xs)

    # Tenants

    def get_all_tenants_ids(self, sysid):
        s = self.get_all_tenants_selector(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: self.extract_tenantid_from_path(x[0]), res)
        return list(xs)

    def get_all_nodes(self, sysid, tenantid):
        s = self.get_all_nodes_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: self.extract_nodeid_from_path(x[0]), res)
        return list(xs)

    def get_node_info(self, sysid, tenantid, nodeid):
        s = self.get_node_info_path(sysid, tenantid, nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_node_info')
        v = res[0][1]
        return json.loads(v.get_value())

    def add_node_info(self, sysid, tenantid, nodeid, nodeinfo):
        p = self.get_node_info_path(sysid, tenantid, nodeid)
        v = Value(json.dumps(nodeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_info(self, sysid, tenantid, nodeid):
        p = self.get_node_info_path(sysid, tenantid, nodeid)
        self.ws.remove(p)

    def get_node_status(self, sysid, tenantid, nodeid):
        s = self.get_node_status_path(sysid, tenantid, nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_node_status')
        v = res[0][1]
        return json.loads(v.get_value())

    def add_node_status(self, sysid, tenantid, nodeid, nodestatus):
        p = self.get_node_status_path(sysid, tenantid, nodeid)
        v = Value(json.dumps(nodestatus), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def observe_node_status(self, sysid, tenantid, nodeid, callback):
        s = self.get_node_status_path(sysid, tenantid, nodeid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def remove_node_status(self, sysid, tenantid, nodeid):
        p = self.get_node_status_path(sysid, tenantid, nodeid)
        self.ws.remove(p)

    def add_node_configuration(self, sysid, tenantid, nodeid, nodeconf):
        p = self.get_node_configuration_path(sysid, tenantid, nodeid)
        v = Value(json.dumps(nodeconf), encoding=Encoding.STRING)
        return self.ws.put(p, v)


    # Catalog

    def get_catalog_all_entities(self, sysid, tenantid):
        s = self.get_catalog_all_entities_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: self.extract_entity_id_from_path(x[0]), res)
            return list(xs)

    def get_catalog_entity_info(self, sysid, tenantid, eid):
        p = self.get_catalog_entity_info_path(sysid, tenantid, eid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        v = res[0][1]
        return json.loads(v.get_value())

    def add_catalog_entity_info(self, sysid, tenantid, eid, einfo):
        p = self.get_catalog_entity_info_path(sysid, tenantid, eid)
        v = Value(json.dumps(einfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_catalog_entity_info(self, sysid, tenantid, eid):
        p = self.get_catalog_entity_info_path(sysid, tenantid, eid)
        self.ws.remove(p)

    def observe_catalog_entities(self, sysid, tenantid, callback):
        s = self.get_catalog_all_entities_selector(sysid, tenantid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_catalog_all_atomic_entities(self, sysid, tenantid):
        s = self.get_catalog_all_atomic_entities_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: self.extract_aeid_from_path(x[0]), res)
            return list(xs)

    def get_catalog_atomic_entity_info(self, sysid, tenantid, aeid):
        p = self.get_catalog_atomic_entity_info_path(sysid, tenantid, aeid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        v = res[0][1]
        return json.loads(v.get_value())

    def add_catalog_atomic_entity_info(self, sysid, tenantid, aeid, aeinfo):
        p = self.get_catalog_atomic_entity_info_path(sysid, tenantid, aeid)
        v = Value(json.dumps(aeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_catalog_atomic_entity_info(self, sysid, tenantid, aeid):
        p = self.get_catalog_atomic_entity_info_path(sysid, tenantid, aeid)
        self.ws.remove(p)

    def observe_catalog_atomic_entities(self, sysid, tenantid, callback):
        s = self.get_catalog_all_atomic_entities_selector(sysid, tenantid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def observe_catalog_fdu(self, sysid, tenantid, fduid,callback):
        s = self.get_catalog_fdu_info_path(sysid, tenantid, fduid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid


    def get_catalog_all_fdus(self, sysid, tenantid):
        s = self.get_catalog_all_fdu_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: self.extract_fduid_from_path(x[0]), res)
            return list(xs)

    def get_catalog_fdu_info(self, sysid, tenantid, fduid):
        p = self.get_catalog_fdu_info_path(sysid, tenantid, fduid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        v = res[0][1]
        return json.loads(v.get_value())

    def add_catalog_fdu_info(self, sysid, tenantid, fduid, fduinfo):
        p = self.get_catalog_fdu_info_path(sysid, tenantid, fduid)
        v = Value(json.dumps(fduinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_catalog_fdu_info(self, sysid, tenantid, fduid):
        p = self.get_catalog_fdu_info_path(sysid, tenantid, fduid)
        self.ws.remove(p)

    def observe_catalog_fdus(self, sysid, tenantid, callback):
        s = self.get_catalog_all_fdu_selector(sysid, tenantid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    # Records


    def get_records_all_entities_instances(self, sysid, tenantid):
        s = self.get_records_all_entities_instances_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: (self.extract_entity_id_from_path(x[0]),self.extract_entity_instanceid_from_path(x[0])), res)
            return list(xs)

    def get_records_all_entity_instances(self, sysid, tenantid, eid):
        s = self.get_records_all_entity_instances_selector(sysid, tenantid, eid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: self.extract_entity_instanceid_from_path(x[0]), res)
            return list(xs)

    def get_records_entity_info(self, sysid, tenantid, eid, instanceid):
        p = self.get_records_entity_instance_info_path(sysid, tenantid, eid, instanceid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        v = res[0][1]
        return json.loads(v.get_value())

    def add_records_entity_info(self, sysid, tenantid, eid, instanceid, aeinfo):
        p = self.get_records_entity_instance_info_path(sysid, tenantid, eid, instanceid)
        v = Value(json.dumps(aeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_records_entity_info(self, sysid, tenantid, eid, instanceid):
        p = self.get_records_entity_instance_info_path(sysid, tenantid, eid, instanceid)
        self.ws.remove(p)

    def observe_records_entities(self, sysid, tenantid, callback):
        s = self.get_records_all_entities_instances_selector(sysid, tenantid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_records_all_atomic_entities_instances(self, sysid, tenantid):
        s = self.get_records_all_atomic_entities_instances_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: (self.extract_aeid_from_path(x[0]),self.extract_atomic_entity_instanceid_from_path(x[0])), res)
            return list(xs)

    def get_records_all_atomic_entity_instances(self, sysid, tenantid, aeid):
        s = self.get_records_all_atomic_entity_instances_selector(sysid, tenantid, aeid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: self.extract_atomic_entity_instanceid_from_path(x[0]), res)
            return list(xs)

    def get_records_atomic_entity_info(self, sysid, tenantid, aeid, instanceid):
        p = self.get_records_atomic_entity_instance_info_path(sysid, tenantid, aeid, instanceid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        v = res[0][1]
        return json.loads(v.get_value())

    def add_records_atomic_entity_info(self, sysid, tenantid, aeid, instanceid, aeinfo):
        p = self.get_records_atomic_entity_instance_info_path(sysid, tenantid, aeid, instanceid)
        v = Value(json.dumps(aeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_records_atomic_entity_info(self, sysid, tenantid, aeid, instanceid):
        p = self.get_records_atomic_entity_instance_info_path(sysid, tenantid, aeid, instanceid)
        self.ws.remove(p)

    def observe_records_atomic_entities(self, sysid, tenantid, callback):
        s = self.get_records_all_atomic_entities_instances_selector(sysid, tenantid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid


    # Node FDU

    def add_node_fdu(self, sysid, tenantid, nodeid, fduid, instanceid ,fduinfo):
        p = self.get_node_fdu_info_path(sysid, tenantid, nodeid, fduid, instanceid)
        v = Value(json.dumps(fduinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def observe_node_fdu(self, sysid, tenantid, nodeid, fduid, instanceid, callback):
        s = self.get_node_fdu_info_path(sysid, tenantid, nodeid, fduid, instanceid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_node_fdus(self, sysid, tenantid, nodeid):
        s = self.get_node_fdu_selector(sysid, tenantid, nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        else:
            xs = map(lambda x: self.extract_node_fduid_from_path(x[0]), res)
            return list(xs)

    def get_node_fdu_instances(self, sysid, tenantid, nodeid, fduid):
        p = self.get_node_fdu_info_path(sysid, tenantid, nodeid, fduid, '*')
        kvs = self.ws.get(p)
        if len(kvs) == 0:
            return []
        xs = map(lambda x: (self.extract_nodeid_from_path(x[0]),
                    self.extract_node_fduid_from_path(x[0]),
                    self.extract_node_instanceid_from_path(x[0]),
                    json.loads(kvs[0][1].get_value())), kvs)
        return list(xs)

    def get_node_fdu_instance(self, sysid, tenantid, nodeid, instanceid):
        p = self.get_node_fdu_info_path(sysid, tenantid, nodeid, '*', instanceid)
        kvs = self.ws.get(p)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def get_fdu_instance_node(self, sysid, tenantid, instanceid):
        p = self.get_node_fdu_info_path(sysid, tenantid, '*', '*', instanceid)
        kvs = self.ws.get(p)
        if len(kvs) == 0:
            return None
        return self.extract_nodeid_from_path(kvs[0][0])

    def get_node_fdu(self, sysid, tenantid, nodeid, fduid, instanceid):
        p = self.get_node_fdu_info_path(sysid, tenantid, nodeid, fduid, instanceid)
        kvs = self.ws.get(p)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def remove_node_fdu(self, sysid, tenantid, nodeid, fduid, instanceid):
        p = self.get_node_fdu_info_path(sysid, tenantid, nodeid, fduid, instanceid)
        return self.ws.remove(p)

    def get_fdu_nodes(self, sysid, tenantid, fduid):
        s = self.get_node_fdu_info_path(sysid, tenantid, '*', fduid, '*')
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: self.extract_nodeid_from_path(x[0]), res)
        return list(xs)

    # Plugins

    def get_all_plugins_ids(self, sysid, tenantid, nodeid):
        s = self.get_node_plugins_selector(sysid, tenantid, nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: self.extract_plugin_from_path(x[0]), res)
        return list(xs)

    def get_plugin_info(self, sysid, tenantid, nodeid, pluginid):
        s = self.get_node_plugin_info_path(sysid, tenantid, nodeid, pluginid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        v = res[0][1]
        return json.loads(v.get_value())

    def add_node_plugin(self, sysid, tenantid, nodeid, pluginid, plugininfo):
        p = self.get_node_plugin_info_path(sysid, tenantid, nodeid, pluginid)
        v = Value(json.dumps(plugininfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def observe_node_plugins(self, sysid, tenantid, nodeid, callback):
        s = self.get_node_plugins_subscriber_selector(sysid, tenantid, nodeid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def add_plugin_eval(self, sysid, tenantid, nodeid, pluginid,
                        func_name, func):
        p = self.get_node_plugin_eval_path(
            sysid, tenantid, nodeid, pluginid, func_name)

        def cb(path, props):
            v = Value(json.dumps(func(**props)), encoding=Encoding.STRING)
            return v
        r = self.ws.register_eval(p, cb)
        self.evals.append(p)
        return r

    # Network

    def get_network_port(self, sysid, tenantid, portid):
        s = self.get_network_port_info_path(sysid, tenantid, portid)
        kvs = self.ws.get(s)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def add_network_port(self, sysid, tenantid, portid, portinfo):
        p = self.get_network_port_info_path(sysid, tenantid, portid)
        v = Value(json.dumps(portinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_network_port(self, sysid, tenantid, portid):
        p = self.get_network_port_info_path(sysid, tenantid, portid)
        return self.ws.remove(p)

    def get_all_network_ports(self, sysid, tenantid):
        p = self.get_all_ports_selector(sysid, tenantid)
        kvs = self.ws.get(p)
        d = []
        for k in kvs:
            d.append(json.loads(k[1].get_value()))
        return d

    def get_network_router(self, sysid, tenantid, routerid):
        s = self.get_network_router_info_path(sysid, tenantid, routerid)
        kvs = self.ws.get(s)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def add_network_router(self, sysid, tenantid, routerid, routerinfo):
        p = self.get_network_router_info_path(sysid, tenantid, routerid)
        v = Value(json.dumps(routerinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_network_router(self, sysid, tenantid, routerid):
        p = self.get_network_router_info_path(sysid, tenantid, routerid)
        return self.ws.remove(p)

    def get_all_network_router(self, sysid, tenantid):
        p = self.get_all_routers_selector(sysid, tenantid)
        kvs = self.ws.get(p)
        d = []
        for k in kvs:
            d.append(json.loads(k[1].get_value()))
        return d

    def get_network(self, sysid, tenantid, netid):
        s = self.get_network_info_path(sysid, tenantid, netid)
        kvs = self.ws.get(s)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def get_all_networks (self, sysid, tenantid):
        p = self.get_all_networks_selector(sysid, tenantid)
        kvs = self.ws.get(p)
        d = []
        for k in kvs:
            d.append(json.loads(k[1].get_value()))
        return d

    def add_network(self, sysid, tenantid, netid, netinfo):
        p = self.get_network_info_path(sysid, tenantid, netid)
        v = Value(json.dumps(netinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_network(self, sysid, tenantid, netid):
        p = self.get_network_info_path(sysid, tenantid, netid)
        return self.ws.remove(p)

    # Images

    def add_image(self, sysid, tenantid, imageid, imginfo):
        p = self.get_image_info_path(sysid, tenantid, imageid)
        v = Value(json.dumps(imginfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_image(self, sysid, tenantid, imageid):
        p = self.get_image_info_path(sysid, tenantid, imageid)
        return self.ws.remove(p)

    def get_image(self, sysid, tenantid, imageid):
        p = self.get_image_info_path(sysid, tenantid, imageid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_all_images(self, sysid, tenantid):
        s = self.get_all_image_selector(sysid, tenantid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    # Node Images

    def add_node_image(self, sysid, tenantid, nodeid,imageid, imginfo):
        p = self.get_node_image_info_path(sysid, tenantid, nodeid, imageid)
        v = Value(json.dumps(imginfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_image(self, sysid, tenantid, nodeid,imageid):
        p = self.get_node_image_info_path(sysid, tenantid, nodeid, imageid)
        return self.ws.remove(p)

    def get_node_image(self, sysid, tenantid, nodeid,  imageid):
        p = self.get_node_image_info_path(sysid, tenantid, nodeid, imageid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_all_node_images(self, sysid, tenantid, nodeid):
        s = self.get_all_node_images(sysid, tenantid, nodeid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(n[0][1].get_value()))
        return d


    # Flavor

    def add_flavor(self, sysid, tenantid, flavorid, flvinfo):
        p = self.get_flavor_info_path(sysid, tenantid, flavorid)
        v = Value(json.dumps(flvinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_flavor(self, sysid, tenantid, flavorid):
        p = self.get_flavor_info_path(sysid, tenantid, flavorid)
        return self.ws.remove(p)

    def get_flavor(self, sysid, tenantid, flavorid):
        p = self.get_flavor_info_path(sysid, tenantid, flavorid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_all_flavors(self, sysid, tenantid):
        s = self.get_all_flavor_selector(sysid, tenantid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(n[0][1].get_value()))
        return d

    # Node Flavor

    def add_node_flavor(self, sysid, tenantid, nodeid,flavorid, flvinfo):
        p = self.get_node_flavor_info_path(sysid, tenantid, nodeid, flavorid)
        v = Value(json.dumps(flvinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_flavor(self, sysid, tenantid, nodeid,flavorid):
        p = self.get_node_flavor_info_path(sysid, tenantid, nodeid, flavorid)
        return self.ws.remove(p)

    def get_node_flavor(self, sysid, tenantid, nodeid,  flavorid):
        p = self.get_node_flavor_info_path(sysid, tenantid, nodeid, flavorid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_all_node_flavors(self, sysid, tenantid, nodeid):
        s = self.get_all_node_flavors(sysid, tenantid, nodeid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    # Node Network

    def add_node_network(self, sysid, tenantid, nodeid, netid, netinfo):
        p = self.get_node_network_info_path(sysid, tenantid, nodeid, netid)
        v = Value(json.dumps(netinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_network(self, sysid, tenantid, nodeid, netid):
        s = self.get_node_network_info_path(sysid, tenantid, nodeid, netid)
        kvs = self.ws.get(s)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def remove_node_network(self, sysid, tenantid, nodeid, netid):
        s = self.get_node_network_info_path(sysid, tenantid, nodeid, netid)
        return self.ws.remove(s)


    def add_node_floating_ip(self, sysid, tenantid, nodeid,floatingid, ip_info):

        p = self.get_node_network_floating_ip_info_path(sysid, tenantid, nodeid, floatingid)
        v = Value(json.dumps(ip_info), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_floating_ip(self, sysid, tenantid, nodeid, floatingid):
        p = self.get_node_network_floating_ip_info_path(sysid, tenantid, nodeid, floatingid)
        return self.ws.remove(p)

    def get_node_floating_ip(self, sysid, tenantid, nodeid,  floatingid):
        p = self.get_node_network_floating_ip_info_path(sysid, tenantid, nodeid, floatingid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_all_node_floating_ips(self, sysid, tenantid, nodeid):
        s = self.get_node_all_network_floating_ips_selector(sysid, tenantid, nodeid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    def get_all_nodes_network_ports(self, sysid, tenantid):
        s = self.get_node_network_ports_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x:
         (self.extract_nodeid_from_path(x[0]),
         self.extract_node_port_id_from_path(x[0]))
         ,res)
        return list(xs)

    def get_node_network_port(self, sysid, tenantid, nodeid,  portid):
        p = self.get_node_network_port_info_path(sysid, tenantid, nodeid, portid)
        res = self.ws.get(p)
        if len(res) == 0:
            return None
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def get_node_network_router(self, sysid, tenantid, nodeid, routerid):
        s = self.get_node_network_router_info_path(sysid, tenantid, nodeid, routerid)
        kvs = self.ws.get(s)
        if len(kvs) == 0:
            return None
        return json.loads(kvs[0][1].get_value())

    def add_node_network_router(self, sysid, tenantid, nodeid, routerid, routerinfo):
        p = self.get_node_network_router_info_path(sysid, tenantid, nodeid, routerid)
        v = Value(json.dumps(routerinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_network_router(self, sysid, tenantid, nodeid, routerid):
        p = self.get_node_network_router_info_path(sysid, tenantid, nodeid, routerid)
        return self.ws.remove(p)

    def get_all_node_network_routers(self, sysid, tenantid, nodeid):
        p = self.get_node_network_routers_selector(sysid, tenantid, nodeid)
        kvs = self.ws.get(p)
        d = []
        for k in kvs:
            d.append(json.loads(k[1].get_value()))
        return d

    def observe_node_routers(self, sysid, tenantid, nodeid, callback):
        s = self.get_node_network_routers_selector(sysid, tenantid, nodeid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty datas')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    # Agent Evals

    def add_node_port_to_network(self, sysid, tenantid,  nodeid, portid, network_id):
        fname = 'add_port_to_network'
        params = {'cp_uuid': portid, 'network_uuid':network_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def remove_node_port_from_network(self, sysid, tenantid, nodeid, portid):
        fname = 'remove_port_from_network'
        params = {'cp_uuid': portid}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def add_node_floatingip(self, sysid, tenantid, nodeid):
        fname = 'create_floating_ip'
        s = self.get_agent_exec_path(sysid, tenantid, nodeid, fname)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def remove_node_floatingip(self, sysid, tenantid, nodeid, ipid):
        fname = 'delete_floating_ip'
        params = {'floating_uuid': ipid}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def assign_node_floating_ip(self, sysid, tenantid, nodeid, ipid, cpid):
        fname = 'assign_floating_ip'
        params = {'floating_uuid': ipid, 'cp_uuid': cpid}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def retain_node_floating_ip(self, sysid, tenantid, nodeid, ipid, cpid):
        fname = 'remove_floating_ip'
        params = {'floating_uuid': ipid, 'cp_uuid': cpid}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def add_port_to_router(self, sysid, tenantid, nodeid, router_id, port_type, vnet_id=None, ip_address=None):
        fname = 'add_router_port'
        params = {'router_id': router_id, "port_type": port_type}
        if vnet_id is not None and vnet_id is not '':
            params.update({'vnet_id': vnet_id})
        if ip_address is not None and ip_address is not '':
            params.update({'ip_address': ip_address})
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def remove_port_from_router(self, sysid, tenantid, nodeid, router_id, vnet_id):
        fname = 'remove_router_port'
        params = {'router_id': router_id, "vnet_id": vnet_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def onboard_fdu_from_node(self, sysid, tenantid, nodeid, fdu_id, fdu_info):
        fname = 'onboard_fdu'
        params = {'descriptor': fdu_info}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def define_fdu_in_node(self, sysid, tenantid, nodeid, fdu_id):
        fname = 'define_fdu'
        params = {'fdu_id': fdu_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def onboard_ae_from_node(self, sysid, tenantid, nodeid, ae_info):
        fname = 'onboard_ae'
        params = {'descriptor': ae_info}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def instantiate_ae_from_node(self, sysid, tenantid, nodeid, ae_id):
        fname = 'instantiate_ae'
        params = {'ae_id': ae_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def offload_ae_from_node(self, sysid, tenantid, nodeid, ae_id):
        fname = 'offload_ae'
        params = {'ae_id': ae_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def terminate_ae_from_node(self, sysid, tenantid, nodeid, ae_inst_id):
        fname = 'terminate_ae'
        params = {'instance_id': ae_inst_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def onboard_entity_from_node(self, sysid, tenantid, nodeid, e_info):
        fname = 'onboard_entity'
        params = {'descriptor': e_info}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def instantiate_entity_from_node(self, sysid, tenantid, nodeid, e_id):
        fname = 'instantiate_entity'
        params = {'entity_id': e_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def offload_entity_from_node(self, sysid, tenantid, nodeid, e_id):
        fname = 'offload_entity'
        params = {'entity_id': e_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def terminate_entity_from_node(self, sysid, tenantid, nodeid, e_inst_id):
        fname = 'terminate_entity'
        params = {'instance_id': e_inst_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())


    def create_network_in_node(self, sysid, tenantid, nodeid, net_info):
        fname = 'create_node_network'
        params = {'descriptor': json.dumps(net_info)}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def remove_network_from_node(self, sysid, tenantid, nodeid, net_id):
        fname = 'remove_node_netwotk'
        params = {'net_id': net_id}
        s = self.get_agent_exec_path_with_params(sysid, tenantid, nodeid, fname, params)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())


class LAD(object):
    def __init__(self, workspace, prefix):
        self.ws = workspace
        self.prefix = prefix
        self.listeners = []
        self.evals = []

    def unsubscribe(self, subid):
        if subid in self.listeners:
            self.ws.unsubscribe(subid)
            self.listeners.remove(subid)

    def unregister_eval(self, path):
        if path in self.evals:
            self.ws.unregister_eval(path)
            self.evals.remove(path)

    def close(self):
        for s in self.listeners:
            self.ws.unsubscribe(s)
        for ep in self.evals:
            self.ws.unregister_eval(ep)

    # TODO: this should be in the YAKS api in the creation of a selector
    def dict2args(self, d):
        i = 0
        b = ''
        for k in d:
            v = d.get(k)
            if isinstance(v,(dict, list)):
                v = json.dumps(v)
            if i == 0:
                b = b + '{}={}'.format(k, v)
            else:
                b = b + ';{}={}'.format(k, v)
            i = i + 1
        return '('+b+')'

    # Node

    def get_node_info_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'info'])

    def get_node_configuration_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'configuration'])

    def get_node_status_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'status'])

    def get_node_plugins_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid,
                                      'plugins', '*', 'info'])

    def get_node_plugins_subscriber_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'plugins', '**'])

    def get_node_plugin_info_path(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid, 'info'])

    def get_node_runtimes_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'runtimes', '**'])

    def get_node_network_managers_selector(self, nodeid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers', '*'])

    # Node FDU

    def get_node_runtime_fdus_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid,
                'fdu', '*','instances','*', 'info'])

    def get_node_runtime_fdus_subscriber_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', '*',
            'instances','*','info'])

    def get_node_fdu_info_path(self, nodeid, pluginid, fduid, instanceid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', fduid,
                'instances', instanceid, 'info'])

    def get_node_fdu_instances_selector(self, nodeid, fduid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', '*', 'fdu', fduid,
                'instances', '*', 'info'])

    def get_node_fdu_instance_selector(self, nodeid, instanceid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', '*', 'fdu', '*',
                'instances', instanceid, 'info'])

    def get_node_all_fdus_instances_selector(self, nodeid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', '*', 'fdu', '*',
            'instances','*','info'])

    # Node Images

    def get_node_image_info_path(self, nodeid, pluginid, imgid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid,
             'images', imgid, 'info'])

    # Node Flavors

    def get_node_flavor_info_path(self, nodeid, pluginid, flvid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid,
             'flavors', flvid, 'info'])

    # Node Networks

    def get_node_netwoks_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'networks', '*', 'info'])

    def get_node_netwoks_find_selector(self, nodeid, netid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             '*', 'networks', netid, 'info'])

    def get_node_network_info_path(self, nodeid, pluginid, networkid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'networks', networkid, 'info'])

    def get_node_network_port_info_path(self, nodeid, pluginid,
                                        portid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'ports', portid, 'info'])

    def get_node_networks_port_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'ports', '*','info'])

    def get_node_network_router_info_path(self, nodeid, pluginid,
                                        routerid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'routers', routerid, 'info'])

    def get_node_network_routers_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'routers', '*','info'])

    def get_node_network_floating_ip_info_path(self, nodeid, pluginid, ipid):
        return Constants.create_path([self.prefix, nodeid,
            'network_managers',pluginid , 'floating-ips', ipid, 'info'])

    def get_node_all_network_floating_ips_selector(self, nodeid, pluginid):
        return Constants.create_path([self.prefix, nodeid,
            'network_managers', pluginid , 'floating-ips', '*', 'info'])

    # Node Evals

    def get_agent_exec_path(self, nodeid, func_name):
        return Constants.create_path([self.prefix, nodeid, 'agent', 'exec',
        func_name])

    def get_agent_exec_path_with_params(self, nodeid, func_name, params):
        if len(params) > 0:
            p = self.dict2args(params)
            f = func_name + '?' + p
        else:
            f = func_name
        return Constants.create_path([self.prefix, nodeid, 'agent', 'exec',
        f])

    def get_node_os_exec_path(self, nodeid, func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'exec', func_name])

    def get_node_nw_exec_path(self, nodeid, net_manager_uuid , func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
            net_manager_uuid , 'exec', func_name])

    def get_node_nw_exec_path_with_params(self, nodeid, net_manager_uuid,
        func_name, params):
        p = self.dict2args(params)
        f = func_name + '?' + p
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
            net_manager_uuid , 'exec', f])

    def get_node_os_exec_path_with_params(self, nodeid, func_name, params):
        if len(params) > 0:
            p = self.dict2args(params)
            f = func_name + '?' + p
        else:
            f = func_name
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'exec', f])

    def get_node_os_info_path(self, nodeid):
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'info'])

    def get_node_plugin_eval_path(self, nodeid, pluginid, func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid, 'exec', func_name])

    def get_node_plugin_eval_path_with_params(self, nodeid, pluginid,
                                              func_name, params):
        p = self.dict2args(params)
        f = func_name + '?' + p
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid,
             'exec', f])


    # ID Extraction

    def extract_nodeid_from_path(self, path):
        return path.split('/')[2]

    def extract_plugin_from_path(self, path):
        return path.split('/')[4]

    def extract_node_fduid_from_path(self, path):
        return path.split('/')[6]

    def extract_node_instanceid_from_path(self, path):
        return path.split('/')[8]

    def extract_node_routerid_from_path(self, path):
        return path.split('/')[6]


    # Node Evals

    def add_os_eval(self, nodeid, func_name, func):
        p = self.get_node_os_exec_path(nodeid, func_name)

        def cb(path, **props):
            v = Value(json.dumps(func(**props)), encoding=Encoding.STRING)
            return v
        r = self.ws.register_eval(p, cb)
        self.evals.append(p)
        return r

    def exec_agent_eval(self, nodeid, func_name, parameters):
        s = self.get_agent_exec_path_with_params(
            nodeid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())

    def exec_os_eval(self, nodeid, func_name, parameters):
        s = self.get_node_os_exec_path_with_params(
            nodeid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_os_eval')
        else:
            return json.loads(res[0][1].get_value())

    def add_nw_eval(self, nodeid, nm_uuid, func_name, func):
        p = self.get_node_nw_exec_path(nodeid, nm_uuid, func_name)

        def cb(path, **props):
            v = Value(json.dumps(func(**props)), encoding=Encoding.STRING)
            return v
        r = self.ws.register_eval(p, cb)
        self.evals.append(p)
        return r

    def exec_nw_eval(self, nodeid, nm_uuid, func_name, parameters):
        s = self.get_node_nw_exec_path_with_params(
            nodeid, nm_uuid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_os_eval')
        else:
            return json.loads(res[0][1].get_value())

    def exec_plugin_eval(self, nodeid, pluginid, func_name, parameters):
        s = self.get_node_plugin_eval_path_with_params(
            nodeid, pluginid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_os_eval')
        else:
            return json.loads(res[0][1].get_value())

    def add_plugin_eval(self, nodeid, pluginid, func_name, func):
        p = self.get_node_plugin_eval_path(nodeid, pluginid, func_name)

        def cb(path, **props):
            v = Value(json.dumps(func(**props)), encoding=Encoding.STRING)
            return v
        r = self.ws.register_eval(p, cb)
        self.evals.append(p)
        return r

    # Node

    def add_node_plugin(self, nodeid, pluginid, plugininfo):
        p = self.get_node_plugin_info_path(nodeid, pluginid)
        v = Value(json.dumps(plugininfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_all_plugins(self, nodeid):
        s = self.get_node_plugins_selector(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: json.loads(x[1].get_value()), res)
        return list(xs)

    def add_node_information(self, nodeid, nodeinfo):
        p = self.get_node_info_path(nodeid)
        v = Value(json.dumps(nodeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_information(self, nodeid):
        p = self.get_node_info_path(nodeid)
        self.ws.remove(p)

    def get_node_status(self, nodeid):
        p = self.get_node_status_path(nodeid)
        res = self.ws.get(p)
        if len(res) == 0:
            raise ValueError('Empty message list on get_node_status')
        v = res[0][1]
        return json.loads(v.get_value())

    def add_node_status(self, nodeid, nodestatus):
        p = self.get_node_status_path(nodeid)
        v = Value(json.dumps(nodestatus), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def observe_node_status(self, nodeid, callback):
        s = self.get_node_status_path(nodeid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def remove_node_status(self, nodeid):
        p = self.get_node_status_path(nodeid)
        self.ws.remove(p)

    def get_node_configuration(self, nodeid):
        s = self.get_node_configuration_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on get_node_configuration')
        return json.loads(res[0][1].get_value())

    def observe_node_plugins(self, nodeid, callback):
        s = self.get_node_plugins_subscriber_selector(nodeid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def observe_node_runtime_fdus(self, nodeid, pluginid, callback):
        s = self.get_node_runtime_fdus_subscriber_selector(nodeid, pluginid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_node_info(self, nodeid):
        s = self.get_node_info_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on get_node_info')
        return json.loads(res[0][1].get_value())

    def get_node_os_info(self, nodeid):
        s = self.get_node_os_info_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on get_node_os_info')
        return json.loads(res[0][1].get_value())

    def add_node_os_info(self, nodeid, osinfo):
        p = self.get_node_os_info_path(nodeid)
        v = Value(json.dumps(osinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    # Node FDU

    def add_node_fdu(self, nodeid, pluginid, fduid, instanceid, fduinfo):
        p = self.get_node_fdu_info_path(nodeid, pluginid, fduid, instanceid)
        v = Value(json.dumps(fduinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_fdu(self, nodeid, pluginid, fduid, instanceid):
        s = self.get_node_fdu_info_path(nodeid, pluginid, fduid, instanceid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def remove_node_fdu(self, nodeid, pluginid, fduid, instanceid):
        p = self.get_node_fdu_info_path(nodeid, pluginid, fduid, instanceid)
        return self.ws.remove(p)

    def get_node_fdu_instances(self, nodeid, fduid):
        p = self.get_node_fdu_instances_selector(nodeid, fduid)
        res = self.ws.get(p)
        if len(res) == 0:
            return []
        return list(map(lambda x: self.extract_node_instanceid_from_path(x[0]), res))

    def get_node_all_fdus_instances(self, nodeid):
        p = self.get_node_all_fdus_instances_selector(nodeid)
        res = self.ws.get(p)
        if len(res) == 0:
            return []
        return list(map (lambda x: json.loads(x[1].get_value()), res))

    # Node Images

    def add_node_image(self, nodeid, pluginid, imgid, imginfo):
        p = self.get_node_image_info_path(nodeid, pluginid, imgid)
        v = Value(json.dumps(imginfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_image(self, nodeid, pluginid, imgid):
        s = self.get_node_image_info_path(nodeid, pluginid, imgid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def remove_node_image(self, nodeid, pluginid, imgid):
        p = self.get_node_image_info_path(nodeid, pluginid, imgid)
        return self.ws.remove(p)

    # Node Flavor

    def add_node_flavor(self, nodeid, pluginid, flvid, flvinfo):
        p = self.get_node_flavor_info_path(nodeid, pluginid, flvid)
        v = Value(json.dumps(flvinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_flavor(self, nodeid, pluginid, flvid):
        s = self.get_node_flavor_info_path(nodeid, pluginid, flvid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def remove_node_flavor(self, nodeid, pluginid, flvid):
        p = self.get_node_flavor_info_path(nodeid, pluginid, flvid)
        return self.ws.remove(p)

    #  Node Network

    def observe_node_networks(self, nodeid, pluginid, callback):
        s = self.get_node_netwoks_selector(nodeid, pluginid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def add_node_network(self, nodeid, pluginid, netid, netinfo):
        p = self.get_node_network_info_path(nodeid, pluginid, netid)
        v = Value(json.dumps(netinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_network(self, nodeid, pluginid, netid):
        s = self.get_node_network_info_path(nodeid, pluginid, netid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def find_node_network(self, nodeid, netid):
        s = self.get_node_netwoks_find_selector(nodeid, netid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def remove_node_network(self, nodeid, pluginid, netid):
        p = self.get_node_network_info_path(nodeid, pluginid, netid)
        return self.ws.remove(p)

    def get_all_node_networks(self, nodeid, pluginid):
        s = self.get_node_netwoks_selector(nodeid, pluginid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    def add_node_port(self, nodeid, pluginid, portid, portinfo):
        p = self.get_node_network_port_info_path(nodeid, pluginid, portid)
        v = Value(json.dumps(portinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_port(self, nodeid, pluginid, portid):
        p = self.get_node_network_port_info_path(nodeid, pluginid, portid)
        return self.ws.remove(p)

    def get_node_port(self, nodeid, pluginid, portid):
        s = self.get_node_network_port_info_path(nodeid, pluginid, portid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def observe_node_ports(self, nodeid, pluginid, callback):
        s = self.get_node_networks_port_selector(nodeid, pluginid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_all_node_ports(self, nodeid, pluginid):
        s = self.get_node_networks_port_selector(nodeid, pluginid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    def add_node_router(self, nodeid, pluginid, routerid, routerinfo):
        p = self.get_node_network_router_info_path(nodeid, pluginid, routerid)
        v = Value(json.dumps(routerinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_router(self, nodeid, pluginid, routerid):
        p = self.get_node_network_router_info_path(nodeid, pluginid, routerid)
        return self.ws.remove(p)

    def get_node_router(self, nodeid, pluginid, routerid):
        s = self.get_node_network_router_info_path(nodeid, pluginid, routerid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def observe_node_routers(self, nodeid, pluginid, callback):
        s = self.get_node_network_routers_selector(nodeid, pluginid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty datas')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_all_node_routers(self, nodeid, pluginid):
        s = self.get_node_network_routers_selector(nodeid, pluginid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    def add_node_floating_ip(self, nodeid, pluginid, ipid, ipinfo):
        p = self.get_node_network_floating_ip_info_path(nodeid, pluginid, ipid)
        v = Value(json.dumps(ipinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def remove_node_floating_ip(self, nodeid, pluginid, ipid):
        p = self.get_node_network_floating_ip_info_path(nodeid, pluginid, ipid)
        return self.ws.remove(p)

    def get_node_floating_ip(self, nodeid, pluginid, ipid):
        s = self.get_node_network_floating_ip_info_path(nodeid, pluginid, ipid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def get_all_node_floating_ips(self, nodeid, pluginid):
        s = self.get_node_all_network_floating_ips_selector(nodeid, pluginid)
        kvs = self.ws.get(s)
        d = []
        for n in kvs:
            d.append(json.loads(kvs[0][1].get_value()))
        return d

    def observe_node_floating_ip(self, nodeid, pluginid, callback):
        s = self.get_node_all_network_floating_ips_selector(nodeid, pluginid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty datas')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid


class CLAD(object):
    def __init__(self, workspace, prefix):
        self.ws = workspace
        self.prefix = prefix
        self.listeners = []
        self.evals = []

    def unsubscribe(self, subid):
        if subid in self.listeners:
            self.ws.unsubscribe(subid)
            self.listeners.remove(subid)

    def unregister_eval(self, path):
        if path in self.evals:
            self.ws.unregister_eval(path)
            self.evals.remove(path)

    def close(self):
        for s in self.listeners:
            self.ws.unsubscribe(s)
        for ep in self.evals:
            self.ws.unregister_eval(ep)

    # TODO: this should be in the YAKS api in the creation of a selector
    def dict2args(self, d):
        i = 0
        b = ''
        for k in d:
            v = d.get(k)
            if isinstance(v,(dict, list)):
                v = json.dumps(v)
            if i == 0:
                b = b + '{}={}'.format(k, v)
            else:
                b = b + ';{}={}'.format(k, v)
            i = i + 1
        return '('+b+')'

    # Node

    def get_node_selector(self):
        return Constants.create_path([self.prefix, '*', 'info'])

    def get_node_info_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'info'])

    def get_node_status_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'status'])

    def get_node_configuration_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'configuration'])

    def get_node_plugins_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid,
                                      'plugins', '*', 'info'])

    def get_node_plugins_subscriber_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'plugins', '**'])

    def get_node_plugin_info_path(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid, 'info'])

    def get_node_runtimes_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'runtimes', '**'])

    def get_node_runtime_fdus_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', '*', 'info'])

    def get_node_runtime_fdus_subscriber_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', '**'])

    def get_node_status(self, nodeid):
        p = self.get_node_status_path(nodeid)
        res = self.ws.get(p)
        if len(res) == 0:
            raise ValueError('Empty message list on get_node_status')
        else:
            v = res[0][1]
            return json.loads(v.get_value())

    def add_node_status(self, nodeid, nodestatus):
        p = self.get_node_status_path(nodeid)
        v = Value(json.dumps(nodestatus), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def observe_node_status(self, nodeid, callback):
        s = self.get_node_status_path(nodeid)
        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def remove_node_status(self, nodeid):
        p = self.get_node_status_path(nodeid)
        self.ws.remove(p)

    # Node FDU

    def get_node_fdu_info_path(self, nodeid, pluginid, fduid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', fduid, 'info'])

    # Agent Evals

    def get_agent_exec_path(self, nodeid, func_name):
        return Constants.create_path([self.prefix, nodeid, 'agent', 'exec',
        func_name])

    def get_agent_exec_path_with_params(self, nodeid, func_name, params):
        p = self.dict2args(params)
        f = func_name + '?' + p
        return Constants.create_path([self.prefix, nodeid, 'agent', 'exec',
        f])

    def exec_agent_eval(self, nodeid, func_name, parameters):
        s = self.get_agent_exec_path_with_params(
            nodeid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_agent_eval')
        else:
            return json.loads(res[0][1].get_value())


    # Node Evals

    def get_node_os_exec_path(self, nodeid, func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'exec', func_name])

    def get_node_os_exec_path_with_params(self, nodeid, func_name, params):
        p = self.dict2args(params)
        f = func_name + '?' + p
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'exec', f])

    def get_node_os_info_path(self, nodeid):
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'info'])

    def get_node_plugin_eval_path(self, nodeid, pluginid, func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid, 'exec', func_name])

    def get_node_plugin_eval_path_with_params(self, nodeid, pluginid,
                                              func_name, params):
        p = self.dict2args(params)
        f = func_name + '?' + p
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid,
             'exec', f])

    def add_os_eval(self, nodeid, func_name, func):
        p = self.get_node_os_exec_path(nodeid, func_name)

        def cb(path, **props):
            v = Value(json.dumps(func(**props)), encoding=Encoding.STRING)
            return v
        r = self.ws.register_eval(p, cb)
        self.evals.append(p)
        return r

    def exec_os_eval(self, nodeid, func_name, parameters):
        s = self.get_node_os_exec_path_with_params(
            nodeid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_os_eval')
        else:
            return json.loads(res[0][1].get_value())

    def exec_plugin_eval(self, nodeid, pluginid, func_name, parameters):
        s = self.get_node_plugin_eval_path_with_params(
            nodeid, pluginid, func_name, parameters)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on exec_os_eval')
        else:
            return json.loads(res[0][1].get_value())

    def add_plugin_eval(self, nodeid, pluginid, func_name, func):
        p = self.get_node_plugin_eval_path(nodeid, pluginid, func_name)

        def cb(path, props):
            v = Value(json.dumps(func(**props)), encoding=Encoding.STRING)
            return v
        r = self.ws.register_eval(p, cb)
        self.evals.append(p)
        return r

    def add_node_plugin(self, nodeid, pluginid, plugininfo):
        p = self.get_node_plugin_info_path(nodeid, pluginid)
        v = Value(json.dumps(plugininfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_all_plugins(self, nodeid):
        s = self.get_node_plugins_selector(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            return []
        xs = map(lambda x: json.loads(x[1].get_value()), res)
        return list(xs)

    def add_node_information(self, nodeid, nodeinfo):
        p = self.get_node_info_path(nodeid)
        v = Value(json.dumps(nodeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_configuration(self, nodeid):
        s = self.get_node_configuration_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on get_node_configuration')
        return json.loads(res[0][1].get_value())

    def observe_node_plugins(self, nodeid, callback):
        s = self.get_node_plugins_subscriber_selector(nodeid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    # Node FDU

    def add_node_fdu(self, nodeid, pluginid, fduid, fduinfo):
        p = self.get_node_fdu_info_path(nodeid, pluginid, fduid)
        v = Value(json.dumps(fduinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_fdu(self, nodeid, pluginid, fduid):
        s = self.get_node_fdu_info_path(nodeid, pluginid, fduid)
        res = self.ws.get(s)
        if len(res) == 0:
            return None
        return json.loads(res[0][1].get_value())

    def remove_node_fdu(self, nodeid, pluginid, fduid):
        p = self.get_node_fdu_info_path(nodeid, pluginid, fduid)
        return self.ws.remove(p)

    def observe_node_runtime_fdus(self, nodeid, pluginid, callback):
        s = self.get_node_runtime_fdus_subscriber_selector(nodeid, pluginid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty data')
            else:
                v = kvs[0][1].get_value()
                if v is not None:
                    callback(json.loads(v.value))
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    # Node

    def get_node_info(self, nodeid):
        s = self.get_node_info_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on get_node_info')
        return json.loads(res[0][1].get_value())

    def get_node_os_info(self, nodeid):
        s = self.get_node_os_info_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty data on get_node_os_info')
        return json.loads(res[0][1].get_value())

    def add_node_os_info(self, nodeid, osinfo):
        p = self.get_node_os_info_path(nodeid)
        v = Value(json.dumps(osinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)


class Global(object):
    def __init__(self, workspace):
        self.ws = workspace
        self.actual = GAD(workspace, Constants.global_actual_prefix)
        self.desired = GAD(workspace, Constants.global_desired_prefix)

    def close(self):
        self.actual.close()
        self.desired.close()


class Local(object):
    def __init__(self, workspace):
        self.ws = workspace
        self.actual = LAD(workspace, Constants.local_actual_prefix)
        self.desired = LAD(workspace, Constants.local_desired_prefix)

    def close(self):
        self.actual.close()
        self.desired.close()



class Yaks_Connector(object):
    def __init__(self, locator):
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.yaks_client = Yaks.login(locator)
        self.yaks_admin = self.yaks_client.admin()
        self.ws = self.yaks_client.workspace(Constants.global_actual_prefix, self.executor)
        self.glob = Global(self.ws)
        self.loc = Local(self.ws)

    def close(self):
        self.glob.close()
        self.loc.close()
        self.yaks_client.logout()

class Yaks_Constraint_Connector(object):
    def __init__(self, locator):
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.yaks_client = Yaks.login(locator)
        self.yaks_admin = self.yaks_client.admin()
        self.ws = self.yaks_client.workspace(Constants.local_constraint_actual_prefix, self.executor)
        self.actual = CLAD(self.ws, Constants.local_constraint_actual_prefix)
        self.desired = CLAD(self.ws, Constants.local_constaint_desired_prefix)

    def close(self):
        self.actual.close()
        self.desired.close()
        self.yaks_client.logout()
