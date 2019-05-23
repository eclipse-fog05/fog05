#!/usr/bin/env python3

# Copyright (c) 2014,2019 Contributors to the Eclipse Foundation
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
# Contributors: Luca Cominardi, University Carlos III of Madrid.

from setuptools import setup

setup(
    name='ykon',
    version='0.0.1',
    python_requires='>=3',
    author='UC3M, ADLINK',
    packages=['ykon'],
    install_requires=['yaks'],
    include_package_data=True
)
#    install_requires=['yaks==0.2.4.post1'],
