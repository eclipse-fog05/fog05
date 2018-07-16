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


def my_observer(key, value, version):
    print('Called Observer with Key: {0} Value: {1} Version {2}'.format(key, value, version))


def test_miss(sid, root, home):

    sroot = 'fos://{0}'.format(root)
    shome= 'fos://{0}-{1}'.format(root, home)

    store = DStore(sid, sroot, home, 1024)

    uri_prefix = 'fos://{0}/{1}-{2}'.format(root, home, sid)
    id = 100 + int(sid)
    val = {'id': id, 'kind': 'info', 'value': 'am a store fos://{0}/{1}-{2}!'.format(root, home, sid)}
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

    test_uri = uri_prefix + '/savia'
    store.observe(test_uri, my_observer)

    print('Store written, press a key to continue')
    input()

    for id in store.discovered_stores:
        uri = 'fos://{0}/{1}-{2}/savia'.format(root, home, id)
        store.remove(uri)
        #print('=========> store[{0}] = {1}'.format(uri, v))

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