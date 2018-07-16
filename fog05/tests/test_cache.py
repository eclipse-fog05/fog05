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
sys.path.append(os.path.join(sys.path[0].rip('tests')))

import uuid
from fog05.DStore import *
from fog05.DController import *
import json
import time

class TestCache():

    def __init__(self):
        self.uuid = uuid.uuid4()
        sid = (self.uuid)


        # Desidered Store. containing the desidered state
        self.droot = 'dfos://<sys-id>'
        self.dhome = 'dfos://<sys-id>/{}'.format(sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        # Actual Store, containing the Actual State
        self.aroot = 'afos://<sys-id>'
        self.ahome = 'afos://<sys-id>/{}'.format(sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

        self.nodes = {}

        self.populateNodeInformation()

    def populateNodeInformation(self):

        node_info = {}

        node_info.update({'name': 'develop node'})
        uri = '{}/'.format(self.ahome)
        self.astore.put(uri, json.dumps(node_info))

    def test_observer_actual(self, key, value,v):
        print('##################################')
        print('##### I\'M an Observer ACTUAL #####')
        print('## Key: {}'.format(key))
        print('## Value: {}'.format(value))
        print('## V: {}'.format(v))
        print('##################################')
        print('##################################')

    def test_observer_desidered(self, key, value,v):
        print('#####################################')
        print('##### I\'M an Observer DESIDERED #####')
        print('## Key: {}'.format(key))
        print('## Value: {}'.format(value))
        print('## V: {}'.format(v))
        print('#####################################')
        print('#####################################')


    def nodeDiscovered(self, uri, value, v = None):
        value = json.loads(value)
        if uri != 'fos://<sys-id>/{}/'.format(self.uuid):
            print('###########################')
            print('###########################')
            print('### New Node discovered ###')
            print('UUID: {}'.format(value.get('uuid')))
            print('Name: {}'.format(value.get('name')))
            print('###########################')
            print('###########################')
            self.nodes.update({len(self.nodes)+1: {value.get('uuid'): value}})

    def show_nodes(self):
        for k in self.nodes.keys():
            n = self.nodes.get(k)
            id = list(n.keys())[0]
            print('{} - {} : {}'.format(k, n.get(id).get('name'), id))

    def main(self):
        uri = 'afos://<sys-id>/*/'
        self.astore.observe(uri, self.nodeDiscovered)

        print('Putting on dstore')
        val = {'value': 'some value'}
        uri = '{}/test1'.format(self.dhome)
        self.dstore.put(uri, json.dumps(val))

        val = {'value2': 'some value2'}
        uri = '{}/test2'.format(self.dhome)
        self.dstore.put(uri, json.dumps(val))

        val = {'value3': 'some value3'}
        uri = '{}/test3'.format(self.dhome)
        self.dstore.put(uri, json.dumps(val))

        print('Putting on astore')
        val = {'actual value': 'some value'}
        uri = '{}/test1'.format(self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'actual value2': 'some value2'}
        uri = '{}/test2'.format(self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'actual value32': 'some value3'}
        uri = '{}/test3'.format(self.ahome)
        self.astore.put(uri, json.dumps(val))

        uri = '{}/test3'.format(self.ahome)
        self.astore.put(uri, json.dumps(val))

        while len(self.nodes) < 1:
            time.sleep(2)

        self.show_nodes()

        print('My UUID is {}' % self.uuid)

        print('###################################### Desidered Store ######################################')
        print(self.dstore)
        print('#############################################################################################')
        print('###################################### Actual Store #########################################')
        print(self.astore)
        print('#############################################################################################')
        input()

        uri = '{}/test3'.format(self.ahome)
        self.astore.remove(uri)

        print('###################################### Actual Store #########################################')
        print(self.astore)
        print('#############################################################################################')

        input()
        exit(0)


if __name__ == '__main__':
    agent = TestCache()
    agent.main()

