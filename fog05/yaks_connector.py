import json
from fog05.interfaces import Constants
from yaks import Yaks, Value, Encoding


class GAD(object):
    def __init__(self, workspace, prefix):
        self.ws = workspace
        self.prefix = prefix
        self.listeners = []
        self.evals = []

    def close(self):
        for s in self.listeners:
            self.ws.unsubscribe(s)
        for ep in self.evals:
            self.ws.unregister_eval(ep)

    def get_sys_info_path(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'info'])

    def get_sys_configuration_path(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'configuration'])

    def get_all_users_selector(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'users', '*'])

    def get_user_info_path(self, sysid, userid):
        return Constants.create_path(
            [self.prefix, sysid, 'users', userid, 'info'])

    def get_all_tenants_selector(self, sysid):
        return Constants.create_path([self.prefix, sysid, 'tenants', '*'])

    def get_tenant_info_path(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'info'])

    def get_tenant_configuration_path(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'configuration'])

    def get_all_nodes_selector(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid, 'nodes', '*'])

    def get_node_info_path(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'info'])

    def get_node_configuration_path(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'configuration'])

    def get_node_plugins_selector(self, sysid, tenantid, nodeid):
        return Constants.create_path([self.prefix, sysid, 'tenants', tenantid,
                                      'nodes', nodeid, 'plugins', '*'])

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

    def get_all_entities_selector(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, 'tenants', tenantid, 'entities', '*'])

    def get_all_networks_selector(self, sysid, tenantid):
        return Constants.create_path(
            [self.prefix, 'tenants', tenantid, 'networks', '*'])

    def get_entity_all_instances_selector(self, sysid, tenantid, entityid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
             'entities',  entityid, 'instances', '*'])

    def get_network_all_ports_selector(self, sysid, tenantid, networkid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants', tenantid,
             'networks', networkid, 'ports', '*'])

    def get_entity_info_path(self, sysid, tenantid, entityid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'entities', entityid, 'info'])

    def get_network_info_path(self, sysid, tenantid, networkid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'networks', networkid, 'info'])

    def get_entity_instance_info_path(self, sysid, tenantid, entityid,
                                      instanceid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'entities', entityid, 'instances', instanceid, 'info'])

    def get_network_port_info_path(self, sysid, tenantid, networkid, portid):
        return Constants.create_path(
            [self.prefix, sysid, 'tenants',
             tenantid, 'networks', networkid, 'ports', portid, 'info'])

    def extract_userid_from_path(self, path):
        return path.split('/')[4]

    def extract_tenantid_from_path(self, path):
        return path.split('/')[4]

    def extract_nodeid_from_path(self, path):
        return path.split('/')[6]

    def extract_plugin_from_path(self, path):
        return path.split('/')[8]

    def get_sys_info(self, sysid):
        s = self.get_sys_info_path(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_sys_info')
        else:
            v = res[0][1]
            return json.loads(v.value)

    def get_sys_config(self, sysid):
        s = self.get_sys_configuration_path(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_sys_config')
        else:
            v = res[0][1]
            return json.loads(v.value)

    def get_all_users_ids(self, sysid):
        s = self.get_all_users_selector(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_all_users_ids')
        else:
            xs = map(lambda x: self.extract_userid_from_path(x[0]), res)
            return xs

    def get_all_tenants_ids(self, sysid):
        s = self.get_all_tenants_selector(sysid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_all_tenants_ids')
        else:
            xs = map(lambda x: self.extract_tenantid_from_path(x[0]), res)
            return xs

    def get_all_nodes(self, sysid, tenantid):
        s = self.get_all_nodes_selector(sysid, tenantid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_all_nodes')
        else:
            xs = map(lambda x: self.extract_nodeid_from_path(x[0]), res)
            return xs

    def get_node_info(self, sysid, tenantid, nodeid):
        s = self.get_node_info_path(sysid, tenantid, nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_node_info')
        else:
            v = res[0][1]
            return json.loads(v.value)

    def get_all_plugins_ids(self, sysid, tenantid, nodeid):
        s = self.get_node_plugins_selector(sysid, tenantid, nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_all_tenants_ids')
        else:
            xs = map(lambda x: self.extract_plugin_from_path(x[0]), res)
            return xs

    def get_plugin_info(self, sysid, tenantid, nodeid, pluginid):
        s = self.get_node_plugin_info_path(sysid, tenantid, nodeid, pluginid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError('Empty message list on get_plugin_info')
        else:
            v = res[0][1]
            return json.loads(v.value)

    def add_node_info(self, sysid, tenantid, nodeid, nodeinfo):
        p = self.get_node_info_path(sysid, tenantid, nodeid)
        v = Value(json.dumps(nodeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def add_node_configuration(self, sysid, tenantid, nodeid, nodeconf):
        p = self.get_node_configuration_path(sysid, tenantid, nodeid)
        v = Value(json.dumps(nodeconf), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def add_node_plugin(self, sysid, tenantid, nodeid, pluginid, plugininfo):
        p = self.get_node_plugin_info_path(sysid, tenantid, nodeid, pluginid)
        v = Value(json.dumps(plugininfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def observe_node_plugins(self, sysid, tenantid, nodeid, callback):
        s = self.get_node_plugins_subscriber_selector(sysid, tenantid, nodeid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty datas')
            else:
                v = json.loads(kvs[0][1])
                callback(v)
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


class LAD(object):
    def __init__(self, workspace, prefix):
        self.ws = workspace
        self.prefix = prefix
        self.listeners = []
        self.evals = []

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
            if i == 0:
                b = b + '{}={}'.format(k, v)
            else:
                b = b + ';{}={}'.format(k, v)
            i = i + 1
        return '('+b+')'

    def get_node_info_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'info'])

    def get_node_configuration_path(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'configuration'])

    def get_node_plugins_selector(self, nodeid):
        return Constants.create_path([self.prefix, nodeid, 'plugins', '*'])

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

    def get_node_runtime_fdus_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', '*'])

    def get_node_runtime_fdus_subscriber_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', '**'])

    def get_node_netwoks_selector(self, nodeid, pluginid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'networks', '*'])

    def get_node_networks_port_selector(self, nodeid, pluginid, networkid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'networks', networkid, 'ports'])

    def get_node_fdu_info_path(self, nodeid, pluginid, fduid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes', pluginid, 'fdu', fduid, 'info'])

    def get_node_fdu_atomic_entity_info(self, nodeid, pluginid, fduid,
                                        atomicid):
        return Constants.create_path(
            [self.prefix, nodeid, 'runtimes',
             pluginid, 'fdu', fduid, 'atomic_entity', atomicid, 'info'])

    def get_node_network_info_path(self, nodeid, pluginid, networkid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_manages',
             pluginid, 'networks', networkid, 'info'])

    def get_node_network_port_info_path(self, nodeid, pluginid, networkid,
                                        portid):
        return Constants.create_path(
            [self.prefix, nodeid, 'network_managers',
             pluginid, 'networks', networkid, 'ports', portid, 'info'])

    def get_node_os_exec_path(self, nodeid, func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'exec', func_name])

    def get_node_os_exec_path_with_params(self, nodeid, func_name, params):
        p = self.dict2args(params)
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'exec', func_name, '?', p])

    def get_node_os_info_path(self, nodeid):
        return Constants.create_path(
            [self.prefix, nodeid, 'os', 'info'])

    def get_node_plugin_eval_path(self, nodeid, pluginid, func_name):
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid, 'exec', func_name])

    def get_node_plugin_eval_path_with_params(self, nodeid, pluginid,
                                              func_name, params):
        p = self.dict2args(params)
        return Constants.create_path(
            [self.prefix, nodeid, 'plugins', pluginid,
             'exec', func_name, '?', p])

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
        res = self.ws.eval(s)
        if len(res) == 0:
            raise ValueError("Empty data on exec_os_eval")
        else:
            return json.loads(res[0][1].value)

    def exec_plugin_eval(self, nodeid, pluginid, func_name, parameters):
        s = self.get_node_plugin_eval_path_with_params(
            nodeid, pluginid, func_name, parameters)
        res = self.ws.eval(s)
        if len(res) == 0:
            raise ValueError("Empty data on exec_os_eval")
        else:
            return json.loads(res[0][1].value)

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

    def add_node_information(self, nodeid, nodeinfo):
        p = self.get_node_info_path(nodeid)
        v = Value(json.dumps(nodeinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_configuration(self, nodeid):
        s = self.get_node_configuration_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError("Empty data on get_node_configuration")
        else:
            return json.loads(res[0][1].value)

    def observe_node_plugins(self, nodeid, callback):
        s = self.get_node_plugins_subscriber_selector(nodeid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty datas')
            else:
                v = json.loads(kvs[0][1])
                callback(v)
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def observe_node_runtime_fdus(self, nodeid, pluginid, callback):
        s = self.get_node_runtime_fdus_subscriber_selector(nodeid, pluginid)

        def cb(kvs):
            if len(kvs) == 0:
                raise ValueError('Listener received empty datas')
            else:
                v = json.loads(kvs[0][1])
                callback(v)
        subid = self.ws.subscribe(s, cb)
        self.listeners.append(subid)
        return subid

    def get_node_os_info(self, nodeid):
        s = self.get_node_os_info_path(nodeid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError("Empty data on get_node_os_info")
        else:
            return json.loads(res[0][1].value)

    def add_node_os_info(self, nodeid, osinfo):
        p = self.get_node_os_info_path(nodeid)
        v = Value(json.dumps(osinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def add_node_fdu(self, nodeid, pluginid, fduid, fduinfo):
        p = self.get_node_fdu_info_path(nodeid, pluginid, fduid)
        v = Value(json.dumps(fduinfo), encoding=Encoding.STRING)
        return self.ws.put(p, v)

    def get_node_fdu(self, nodeid, pluginid, fduid):
        s = self.get_node_fdu_info_path(nodeid, pluginid, fduid)
        res = self.ws.get(s)
        if len(res) == 0:
            raise ValueError("Empty data on get_node_fdu")
        else:
            return json.loads(res[0][1].value)

    def remove_node_fdu(self, nodeid, pluginid, fduid):
        p = self.get_node_fdu_info_path(nodeid, pluginid, fduid)
        return self.ws.remove(p)


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
        self.yaks_client = Yaks.login(locator)
        self.yaks_admin = self.yaks_client.admin()
        self.ws = self.yaks_client.workspace(Constants.global_actual_prefix)
        self.glob = Global(self.ws)
        self.loc = Local(self.ws)

    def close(self):
        self.glob.close()
        self.loc.close()
        self.yaks_client.logout()
