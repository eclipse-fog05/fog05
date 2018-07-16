# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
# 
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
# 
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0
# 
# SPDX-License-Identifier: EPL-2.0
#
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Initial implementation and API

import sys, os

sys.path.append(os.path.join(sys.path[0].rstrip("tests")))
import unittest

def resolve_dependencies(components):
    '''
    The return list contains component's name in the order that can be used to deploy
     @TODO: should use less cycle to do this job
    :rtype: list
    :param components: list like [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]

    no_dependable_components -> list like [[{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}], [{'name': 'c3', 'need': []}], [{'name': 'c2', 'need': []}], [{'name': 'c1', 'need': []}], []]
    :return: list like ['c4', 'c5', 'c3', 'c2', 'c1']
    '''
    c = list(components)
    no_dependable_components = []
    for i in range(0, len(components)):
        no_dependable_components.append([x for x in c if len(x.get('need')) == 0])
        # print (no_dependable_components)
        c = [x for x in c if x not in no_dependable_components[i]]
        for y in c:
            n = y.get('need')
            n = [x for x in n if x not in [z.get('name') for z in no_dependable_components[i]]]
            y.update({"need": n})

    order = []
    for i in range(0, len(no_dependable_components)):
        n = [x.get('name') for x in no_dependable_components[i]]
        order.extend(n)
    return order


def dot2dict(dot_notation, value=None):
    ld = []

    tokens = dot_notation.split('.')
    n_tokens = len(tokens)
    for i in range(n_tokens, 0, -1):
        if i == n_tokens and value is not None:
            ld.append({tokens[i - 1]: value})
        else:
            ld.append({tokens[i - 1]: ld[-1]})

    return ld[-1]


def args2dict(values):
    data = {}
    uri_values = values.split('&')
    for tokens in uri_values:
        v = tokens.split('=')[-1]
        k = tokens.split('=')[0]
        if len(k.split('.')) < 2:
            data.update({k: v})
        else:
            d = dot2dict(k, v)
            data.update(d)
    return data

def data_merge(base, updates):
    if base is None or isinstance(base, int) or isinstance(base, str) or isinstance(base, float):
        base = updates
    elif isinstance(base, list):
        if isinstance(updates, list):
            names = [x.get('name') for x in updates]
            item_same_name = [item for item in base if item.get('name') in [x.get('name') for x in updates]]
            print (names)
            print (item_same_name)
            if all(isinstance(x, dict) for x in updates) and len(
                    [item for item in base if item.get('name') in [x.get('name') for x in updates]]) > 0:
                for e in base:
                    for u in updates:
                        if e.get('name') == u.get('name'):
                            data_merge(e, u)
            else:
                base.extend(updates)
        else:
            base.append(updates)
    elif isinstance(base, dict):
        if isinstance(updates, dict):
            for k in updates.keys():
                if k in base.keys():
                    base.update({k: data_merge(base.get(k), updates.get(k))})
                else:
                    base.update({k: updates.get(k)})
    return base
def is_metaresource(uri):
    u = uri.split('/')[-1]
    if u.endswith('~') and u.startswith('~'):
        return True
    return False

class DependenciesTests(unittest.TestCase):
    def test_resolve_dependencies_with_dependable_components(self):

        input_data = [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']},
                       {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]
        output_data = ['c4', 'c5', 'c3', 'c2', 'c1']
        self.assertEqual(resolve_dependencies(input_data), output_data)

    def test_resolve_dependencies_with_no_dependable_components(self):
        input_data = [{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}, {'name': 'c3', 'need': []},
                       {'name': 'c2', 'need': []}, {'name': 'c1', 'need': []}]
        output_data = ['c4', 'c5', 'c3', 'c2', 'c1']
        self.assertEqual(resolve_dependencies(input_data), output_data)

    def test_dotnotation_to_dict_conversion(self):
        input_data = "par=1&val2.val3=4"
        output_data = {'par': '1', 'val2': {'val3': '4'}}
        self.assertEqual(args2dict(input_data), output_data)

    def test_complex_data_merge(self):
        input_data_one = {'key1': 1, 'key2': {'subkey1': 1, 'subkey2': 1}}
        input_data_two = {'key1': 2}
        output_data = {'key1': 2, 'key2': {'subkey1': 1, 'subkey2': 1}}
        self.assertEqual(data_merge(input_data_one, input_data_two), output_data)

    def test_complex_data_merge_two(self):
        input_data_one = {'key1': 1, 'key2': {'subkey1': 1, 'subkey2': 1}}
        input_data_two = {'key2': {'subkey1': 2}}
        output_data = {'key1': 1, 'key2': {'subkey1': 2, 'subkey2': 1}}
        self.assertEqual(data_merge(input_data_one, input_data_two), output_data)

    def test_is_metaresource_one(self):
        input_data_one = 'afos://0/123/~keys~'
        output_data = True
        self.assertEqual(is_metaresource(input_data_one), output_data)

    def test_is_metaresource_two(self):
        input_data_one = 'afos://0/123/~stores~'
        output_data = True
        self.assertEqual(is_metaresource(input_data_one), output_data)

    def test_is_metaresource_three(self):
        input_data_one = 'afos://0/123/456'
        output_data = False
        self.assertEqual(is_metaresource(input_data_one), output_data)

def main():
    unittest.main()


if __name__ == '__main__':
    main()
