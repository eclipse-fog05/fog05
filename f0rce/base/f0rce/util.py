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

import parse


def dict_to_str(dictionary):
    assert isinstance(dictionary, dict)
    s = '{'
    for k,v in dictionary.items():
        if len(s) > 1:
            s = s + ', '
        s = s + '\'' + str(k) + '\': ' + str(v)
    s = s + '}'
    return s

def path_to_vars(template, path):
    return parse.parse(template, path).named
