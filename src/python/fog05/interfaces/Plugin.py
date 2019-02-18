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

import uuid


class Plugin(object):

    def __init__(self, version, plugin_uuid=None):
        self.version = version
        self.connector = None
        self.node = None
        if uuid is None:
            self.uuid = uuid.uuid4()
        else:
            self.uuid = plugin_uuid

    def get_nm_plugin(self):
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        nms = [x for x in pls if pls.get('type') == 'network']
        if len(nms) == 0:
            raise RuntimeError('No network_manager present in the node!!')
        nm = nms[0]
        return nm

    def call_os_plugin_function(self, fname, fparameters):
        res = self.connector.loc.actual.exec_os_eval(
            self.node, fname, fparameters)
        if res.get('error'):
            raise ValueError('OS Eval returned {}'.format(res.get('error')))
            # return None
        return res.get('result')

    def call_nw_plugin_function(self, fname, fparameters):
        pls = self.connector.loc.actual.get_all_plugins(self.node)
        nms = [x for x in pls if pls.get('type') == 'network']
        if len(nms) == 0:
            raise RuntimeError('No network_manager present in the node!!')
        nm = nms[0]
        res = self.connector.loc.actual.exec_nw_eval(
            self.node, nm, fname, fparameters)
        if res.get('error'):
            raise ValueError('NM Eval returned {}'.format(res.get('error')))
            # return None
        return res.get('result')

    def get_version(self):
        return self.version

    def react_to_cache(self, key, value, version):
        raise NotImplementedError
