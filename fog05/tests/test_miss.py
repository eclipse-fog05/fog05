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

import uuid
import sys
import os
sys.path.append(os.path.join(sys.path[0].rstrip('tests')))
from fog05.DStore import *
import dds
import json
import time

###
def test_miss(sid, root, home):

    sroot = 'afos://{}'.format(root)
    shome = 'afos://{}/{}'.format(root, home)

    store = DStore(sid, sroot, home, 1024)

    uri_prefix = 'afos://{0}/{1}-{2}'.format(root, home, sid)
    id = 100 + int(sid)
    val = {'id': id, 'kind': 'info', 'value': 'am a store afos://{0}/{1}-{2}!'.format(root, home, sid)}
    store.put(uri_prefix, json.dumps(val))

    test_uri = uri_prefix+'/savia'
    tid = 200 + int(sid)
    tval = {'id': tid, 'value': 'A Test URI'}
    store.put(test_uri, json.dumps(tval))


    dval = {'pasticceria': '{0}-Cannoli!'.format(sid)}
    store.dput(test_uri, json.dumps(dval))

    delta_tag = '#rosticceria={0}-Arancini!'.format(sid)
    test_uri = test_uri+delta_tag
    store.dput(test_uri)

    print('Store written, press a key to continue')
    input()
    # local get
    v = store.get(uri_prefix)
    vt = store.get(test_uri)
    print('=========> store[{0}] = {1}'.format(uri_prefix, v))
    print('=========> store[{0}] = {1}'.format(test_uri, vt))
    print('\nStore get exectured, press a key to continue')
    input()
    # try get that need resolving
    for id in store.discovered_stores:
       uri = 'afos://{0}/{1}-{2}/savia'.format(root, home, id)
       v = store.get(uri)
       print('=========> store[{0}] = {1}'.format(uri, v))

    print('\nStore remote get exectured, press a key to continue')
    input()
    # try to get them in a single shot -- locally:

    uri = 'afos://{0}/*'.format(root, home)
    vs = store.getAll(uri)
    print('=========> store[{0}] = {1}'.format(uri, vs))

    print('\nStore local get-all exectured, press a key to continue')
    input()

    vs = store.resolveAll(uri)
    print('=========> store[{0}] = {1}'.format(uri, vs))

    print('\nStore remote resolve-all exectured, press a key to continue')
    input()



if __name__ == '__main__':
    argc = len(sys.argv)

    if argc > 3:
        test_miss(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print('USAGE:\n\tpython3 test_miss.py <sid> <store-root> <store-home>')
        print('\nExample:\n\ttpython3 test_miss.py 1 root home')
        print('\n\ttpython3 test_miss.py 2 root home')
        print('\n\ttpython3 test_miss.py 3 root home')
