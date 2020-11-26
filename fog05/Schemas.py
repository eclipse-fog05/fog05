# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Initial implementation and API

import json
import os
resource_package = 'fog05'
resource_path = '/'.join(('json_objects', 'network.schema'))


def read_file(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
    return data


network_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'network.schema')))
atomic_entity_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'atomic_entity_definition.schema')))
vm_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'vm.schema')))
native_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'native_define.schema')))
container_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'container.schema')))
ros2_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'ros2_define.schema')))
entity_schema = json.loads(read_file(os.path.join(os.path.dirname(__file__), 'json_objects', 'entity_definition.schema')))
