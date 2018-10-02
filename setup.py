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

#!/usr/bin/env python3

from setuptools import setup

setup(
    name='fog05',
    version='0.1.6',
    python_requires='>=3',
    author='ADLINK',
    packages=['fog05', 'fog05/interfaces'],
    install_requires=['networkx', 'jsonschema', 'netifaces', 'websockets', 'colorama', 'urllib3', 'requests', 'psutil', 'flask'],
    scripts=['bin/fos', 'bin/fos-get', 'bin/fos-agent', 'bin/fos.bat', 'bin/fos-get.bat', 'bin/f05ws', 'bin/f05log.bat',
             'bin/f05log', 'bin/f05ws.bat', 'bin/f05wc', 'bin/f05wc.bat', 'bin/f05api', 'bin/f05api.bat'],
    include_package_data=True
)