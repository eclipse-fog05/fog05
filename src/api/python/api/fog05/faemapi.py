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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - API v2


import random
from fog05.yaks_connector import Yaks_Connector
from fog05.interfaces import Constants


class FAEMAPI(object):
    '''
        This class allow the interaction with fog05 FIM
    '''

    def __init__(self, locator='127.0.0.1:7887',
                 sysid=Constants.default_system_id,
                 tenantid=Constants.default_tenant_id):

        self.connector = Yaks_Connector(locator)
        self.sysid = sysid
        self.tenantid = tenantid
        self.atomic_entity = self.AtomicEntity(self.connector, self.sysid, self.tenantid)

    def close(self):
        self.connector.close()

    class AtomicEntity(object):

        def __init__(self, connector=None, sysid=Constants.default_system_id,
            tenantid=Constants.default_tenant_id):

            if connector is None:
                raise RuntimeError('Yaks connector cannot be none in API!')
            self.connector = connector
            self.sysid = sysid
            self.tenantid = tenantid

        def onboard(self, descriptor):
            nodes = self.connector.glob.actual.get_all_nodes(self.sysid, self.tenantid)
            if len(nodes) == 0:
                raise SystemError("No nodes in the system!")
            n = random.choice(nodes)
            res = self.connector.glob.actual.onboard_ae_from_node(self.sysid, self.tenantid, n, descriptor)
            if res.get('result') is None:
                raise SystemError('Error during onboarding {}'.format(res['error']))
            return res['result']


        def instantiate(self, ae_id):
            nodes = self.connector.glob.actual.get_all_nodes(self.sysid, self.tenantid)
            if len(nodes) == 0:
                raise SystemError("No nodes in the system!")
            n = random.choice(nodes)
            res =  self.connector.glob.actual.instantiate_ae_from_node(self.sysid, self.tenantid, n, ae_id)
            if res.get('result') is None:
                raise SystemError('Error during instantiation {}'.format(res['error']))
            return res['result']

        def offload(self, ae_id):
            nodes = self.connector.glob.actual.get_all_nodes(self.sysid, self.tenantid)
            if len(nodes) == 0:
                raise SystemError("No nodes in the system!")
            n = random.choice(nodes)
            res =  self.connector.glob.actual.offload_ae_from_node(self.sysid, self.tenantid, n, ae_id)
            if res.get('result') is None:
                raise SystemError('Error during offloading {}'.format(res['error']))
            return res['result']


        def terminate(self, ae_instance_id):
            nodes = self.connector.glob.actual.get_all_nodes(self.sysid, self.tenantid)
            if len(nodes) == 0:
                raise SystemError("No nodes in the system!")
            n = random.choice(nodes)
            res = self.connector.glob.actual.terminate_ae_from_node(self.sysid, self.tenantid, n, ae_instance_id)
            if res.get('result') is None:
                raise SystemError('Error during termination {}'.format(res['error']))
            return res['result']

        def get_atomic_entity_descriptor(self, ae_id):
            res = self.connector.glob.actual.get_catalog_atomic_entity_info(self.sysid, self.tenantid, ae_id)
            return res

        def get_atomic_entity_instance_info(self, instance_id):
            res = self.connector.glob.actual.get_records_atomic_entity_info(self.sysid, self.tenantid, "*", instance_id)
            return res


