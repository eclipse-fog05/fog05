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

import json
import pkg_resources
import os
resource_package = 'fog05'  # Could be any module/package name
resource_path = '/'.join(('json_objects', 'network.schema'))


def readFile(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
    return data


network_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'network.schema')))
atomic_entity_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'atomic_entity_definition.schema')))
vm_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'vm.schema')))
native_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'native_define.schema')))
container_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'container.schema')))
ros2_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'ros2_define.schema')))
entity_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'entity_definition.schema')))