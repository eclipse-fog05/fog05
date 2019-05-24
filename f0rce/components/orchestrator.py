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

import f0rce
import json
import random
import threading
import traceback
from uuid import uuid4,UUID




class Orchestrator(f0rce.Orchestrator):
    def __init__(self, endpoint, name, uuid, domains):
        super().__init__(endpoint, name, uuid, domains.split(','))


    def __place(self, entity):
        assert isinstance(entity, f0rce.Entity)
        self.log.info('Placing: {}'.format(entity.uuid))

        target = None
        nodes = []
        for net in self.network.values():
            for node in net.node.values():
                check = []
                if entity.requirement.runtime.name in node.execution.runtime:
                    check.append(True)
                else:
                    check.append(False)

                if entity.requirement.ram.size <= node.ram.size:
                    check.append(True)
                else:
                    check.append(False)

                tmp = False
                for d in node.storage.disk.values():
                    if entity.requirement.disk.size <= d.size:
                        tmp = True
                        break
                if tmp:
                    check.append(True)
                else:
                    check.append(False)

                cn = [c.arch for c in node.cpu.core.values()]
                ce = [c.arch for c in entity.requirement.cpu.core.values()]
                tmp = []
                for c in ce:
                    try:
                        tmp.append(cn.pop(cn.index(c)))
                    except ValueError:
                        continue
                if tmp == ce:
                    check.append(True)
                else:
                    check.append(False)

                if all(check):
                    nodes.append(node)

        if nodes:
            target = random.choice(nodes)
        return target


    def __instance(self, entity, node):
        instance = f0rce.Instance(uuid = uuid4(), entity = entity.uuid,
                node = node.uuid, network = f0rce.property.Network())
        if entity.requirement.runtime.name == f0rce.enum.RuntimeCode.LXD.name:
            intf = None
            for i in node.network.intf.values():
                if i.mac.type == f0rce.enum.InterfaceMACType.BRIDGED.name:
                    intf = f0rce.property.Interface(
                            name = i.name,
                            type = f0rce.enum.InterfaceType.VIRTUAL)
                    intf.mac.set_type(f0rce.enum.InterfaceMACType.BRIDGED)
                    break
            if intf:
                instance.network.add_intf(intf)

        return instance


    def Oo1onboard(self, entity):
        if isinstance(entity, str):
            entity = f0rce.entity.build(json.loads(entity))
        elif isinstance(entity, dict):
            entity = f0rce.entity.build(entity)
        elif not isinstance(entity, f0rce.Entity):
            return {"status": "error", "description": "Invalid object"}

        self.log.info('Onboarding: {}'.format(entity.uuid))
        try:
            node = self.__place(entity)
        except Exception as e:
            self.log.error(e)

        if not node:
            return {"status": "error", "description": "No node available"}

        try:
            instance = self.__instance(entity, node)
        except Exception as e:
            traceback.print_exc()

        try:
            if instance:
                for domain,vim in self.vim.items():
                    self.log.info('Onboarding on {}...'.format(domain))
                    vim.O4onboard(entity = entity.to_dict(), instance = instance.to_dict())
                    self.log.info('Instantiting on {}...'.format(domain))
                    vim.O4instantiate(entity = entity.to_dict(), instance = instance.to_dict())
        except Exception as e:
            traceback.print_exc()
        self.log.critical("EXITING")
        return {"status": "ok", "description": "Invalid object"}


    def Oo1offload(self, entity):
        self.log.info('Offnboarding: {}'.format(entity))
        pass

    def Oo1instantiate(self, entity):
        pass

    def Oo1terminate(self, entity):
        pass

    def Oo1list(self):
        pass

# Do NOT remove
component = lambda *args, **kwargs: Orchestrator(*args, **kwargs)
