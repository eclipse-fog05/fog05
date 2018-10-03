import json


class Store(object):

    def __init__(self, api, root_path, home_path, cachesize):
        self.yaks = api
        self.root = root_path
        self.home = home_path
        self.cachesize = cachesize
        self.access = self.yaks.create_access(root_path, cachesize)

    def get(self, k):
        r = self.access.get(k)
        if r is not None and len(r) > 0:
            v = r[0].get('value')
            return v
        return None

    def getAll(self, k):
        r = self.access.get(k)
        if r is not None and len(r) > 0:
            res = []
            for e in r:
                k, v = e.get('key'), e.get('value')
                res.append((k, v, 0))
            return res
        return None

    def resolve(self, k):
        return self.get(k)

    def resolveAll(self, k):
        return self.getAll(k)

    def put(self, k, v):
        return self.access.put(k, v)

    def dput(self, uri, value=None):
        data = self.get(uri)
        print('<<<< DPUT <<<< IN DATA: {}'.format(data))
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
        print('<<<< DPUT >>>> OUT DATA: {}'.format(data))
        value = json.dumps(data)
        return self.access.put(uri, value)

    def remove(self, k):
        return self.access.remove(k)

    def observe(self, k, callback):
        def adapter_callback(values):
            key, value = values[0].get('key'), values[0].get('value')
            callback(key, value, 0)
        self.access.subscribe(k, adapter_callback)

    def close(self):
        self.access.dispose()

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
                        base.update({k: self.data_merge(base.get(k), updates.get(k))})
                    else:
                        base.update({k: updates.get(k)})
        return base
