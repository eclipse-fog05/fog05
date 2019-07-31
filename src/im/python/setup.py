#!/usr/bin/env python3

# Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set
#
# This API is part of EU H2020 5GCity Project Platform
#


from setuptools import setup

setup(
    name='fog05_im',
    version='0.2.0',
    python_requires='>=3',
    author='ADLINK',
    packages=['fog05_im'],
    install_requires=['jsonschema'],
    include_package_data=True
)
