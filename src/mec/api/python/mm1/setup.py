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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc.
# OCaml implementation and API

#!/usr/bin/env python

from setuptools import setup

setup(
    name='fog05mm1',
    version='0.0.1',
    author='ADLINK',
    packages=['fog05mm1'],
    install_requires=['requests'],
    include_package_data=True,
    description='Eclipse fog05 Mm1 REST Client API',
    url='https://github.com/eclipse/fog05',
    authon_email='gabriele.baldoni@adlinktech.com',
    license='Apache 2.O or EPL 2.0',
    classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Intended Audience :: Developers',
          'Intended Audience :: Telecommunications Industry',
          'License :: OSI Approved :: Apache Software License',
          'License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3'
    ],
)
