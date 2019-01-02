import json
from yaks import YAKS
from yaks import Path
from yaks import Selector
from yaks import Value


class FOSStore(object):
    """
    Helper class to interact with the Store
    """

    def __init__(self, server, aroot, droot, sroot, home):
        '''

        Initialize the Store with root and home

        :param server: the address of the YAKS server
        :param aroot: actual store root
        :param droot: desired store root
        :param home: store home also used to generate store id
        '''

        self.y = YAKS.login(server)
        self.aroot = aroot  # '/dfos/{}'
        self.ahome = '{}/{}'.format(aroot, home)

        self.droot = droot  # '/dfos/{}'
        self.dhome = '{}/{}'.format(droot, home)

        self.sroot = sroot
        self.shome = '{}/{}'.format(sroot, home)

        self.actual = Store(self.y, self.aroot, self.ahome, 1024)
        self.desired = Store(self.y, self.droot, self.dhome, 1024)
        self.system = Store(self.y,  self.sroot, self.shome, 1024)

    def close(self):
        '''
        Close the store

        :return: None
        '''
        self.actual.close()
        self.desired.close()
        self.system.close()
        self.y.logout()


class Store(object):

    def __init__(self, api, root_path, home_path, cachesize):
        self.yaks = api
        self.root = root_path
        self.home = home_path
        self.cachesize = cachesize
        self.workspace = self.yaks.workspace(Path(root_path))
        self.subscriptions = []

    def get(self, k):
        r = self.workspace.get(Selector(k))
        if r is not None and len(r) > 0:
            v = r[0].get('value').get_value()
            return v
        return None

    def getAll(self, k):
        r = self.workspace.get(Selector(k))
        if r is not None and len(r) > 0:
            res = []
            for e in r:
                k, v = str(e.get('key')), e.get('value').get_value()
                res.append((k, v, 0))
            return res
        return []

    def resolve(self, k):
        return self.get(k)

    def resolveAll(self, k):
        return self.getAll(k)

    def put(self, k, v):
        return self.workspace.put(Path(k), Value(v))

    def dput(self, uri, value=None):
        data = self.get(uri)
        uri_values = ''
        if value is None:
            uri = uri.split('#')
            uri_values = uri[-1]
            uri = uri[0]
        if data is None or data == '':
            data = {}
        else:
            data = json.loads(data)

        if value is None:
            uri_values = uri_values.split('&')
            for tokens in uri_values:
                v = tokens.split('=')[-1]
                k = tokens.split('=')[0]
                d = self.dot2dict(k, v)
                data = self.data_merge(data, d)
        else:
            jvalues = json.loads(value)
            data = self.data_merge(data, jvalues)
        value = json.dumps(data)

        return self.workspace.put(Path(uri), Value(value))

    def remove(self, k):
        return self.workspace.remove(Path(k))

    def eval(self, k, callback):
        self.workspace.eval(k, callback)

    def observe(self, k, callback):
        def adapter_callback(values):
            key, value = str(values[0].get('key')), \
                values[0].get('value').get_value()
            callback(key, value, 0)
        subid = self.workspace.subscribe(Selector(k), adapter_callback)
        self.subscriptions.append(subid)
        return subid

    def overlook(self, subid):
        self.workspace.unsubscribe(subid)
        self.subscriptions.remove(subid)

    def close(self):
        for subid in self.subscriptions:
            self.workspace.unsubscribe(subid)
        self.workspace.dispose()

    def dot2dict(self, dot_notation, value=None):
        ld = []

        tokens = dot_notation.split('.')
        n_tokens = len(tokens)
        for i in range(n_tokens, 0, -1):
            if i == n_tokens and value is not None:
                ld.append({tokens[i - 1]: value})
            else:
                ld.append({tokens[i - 1]: ld[-1]})

        return ld[-1]

    def data_merge(self, base, updates):
        if base is None or isinstance(base, int) or isinstance(base, str) or isinstance(base, float):
            base = updates
        elif isinstance(base, list):
            if isinstance(updates, list):
                if all(isinstance(x, dict) for x in updates) and len(
                        [item for item in base if item.get('name') in [x.get('name') for x in updates]]) > 0:
                    for e in base:
                        for u in updates:
                            if e.get('name') == u.get('name'):
                                self.data_merge(e, u)
                else:
                    base.extend(updates)
            else:
                base.append(updates)
        elif isinstance(base, dict):
            if isinstance(updates, dict):
                for k in updates.keys():
                    if k in base.keys():
                        base.update(
                            {k: self.data_merge(base.get(k), updates.get(k))})
                    else:
                        base.update({k: updates.get(k)})
        return base
