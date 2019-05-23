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
import ykon
from uuid import UUID
from yaks import ChangeKind




class Stack(object):
    def __init__(self, component, domain):
        assert isinstance(component, ykon.Component)
        self.component = component
        self.domain = domain
        self.entity = {}
        self.instance = {}

    def __entity(self, path, value, event):
        uuid = f0rce.util.path_to_vars(template = f0rce.path.entity, path = path)
        if event is ChangeKind.PUT:
            self.__add_entity(f0rce.entity.build(value))
        elif event is ChangeKind.UPDATE and uuid['entity'] in self.entity:
            self.__upd_entity(f0rce.entity.build(value))
        elif event is ChangeKind.REMOVE and uuid['entity'] in self.entity:
            self.__del_entity(self.entity[uuid['entity']])

    def __instance(self, path, value, event):
        uuid = f0rce.util.path_to_vars(template = f0rce.path.instance, path = path)
        if event is ChangeKind.PUT:
            self.__add_instance(f0rce.instance.build(value))
        elif event is ChangeKind.UPDATE and uuid['instance'] in self.instance:
            self.__upd_instance(f0rce.instance.build(value))
        elif event is ChangeKind.REMOVE and uuid['instance'] in self.instance:
            self.__del_instance(self.instance[uuid['instance']])

    def register(self):
        entities = f0rce.entity.get(self.component, self.domain)
        for e in entities:
            self.__add_entity(e)
        instances = f0rce.instance.get(self.component, self.domain)
        for i in instances:
            self.__add_instance(i)
        pkw = {'domain': self.domain, 'entity': '*'}
        self.component.subscription.add(f0rce.path.entity.format(**pkw), self.__entity)
        pkw = {'domain': self.domain, 'entity': '*', 'instance': '*'}
        self.component.subscription.add(f0rce.path.instance.format(**pkw), self.__instance)

    def unregister(self):
        for e in list(self.entity.values()):
            self.del_entity(e)
        for i in list(self.instance.values()):
            self.del_instance(i)

    def __add_instance(self, instance):
        assert isinstance(instance, f0rce.Instance)
        if str(instance.entity) in self.entity:
            self.component.log.info('Adding instance: {}'.format(str(instance.uuid)))
            self.instance[str(instance.uuid)] = instance
            return instance
        return None

    def __add_entity(self, entity):
        assert isinstance(entity, f0rce.Entity)
        self.component.log.info('Adding entity: {}'.format(str(entity.uuid)))
        self.entity[str(entity.uuid)] = entity
        return entity

    def __del_instance(self, instance):
        assert isinstance(instance, f0rce.Instance)
        if str(instance.uuid) in self.instance:
            self.component.log.info('Removing instance: {}'.format(str(instance.uuid)))
            del self.instance[str(instance.uuid)]
            return instance
        return None

    def __del_entity(self, entity):
        assert isinstance(entity, f0rce.Entity)
        if str(entity.uuid) in self.entity:
            self.component.log.info('Removing entity: {}'.format(str(entity.uuid)))
            del self.entity[str(entity.uuid)]
            return entity
        return None

    def __upd_instance(self, instance):
        assert isinstance(instance, f0rce.Instance)
        if str(instance.uuid) in self.instance:
            self.component.log.info('Updating instance: {}'.format(str(instance.uuid)))
            # TO FIX
            return self.__add_instance(self, instance)
        return None

    def __upd_entity(self, entity):
        assert isinstance(entity, f0rce.Entity)
        if str(entity.uuid) in self.entity:
            self.component.log.info('Updating entity: {}'.format(str(entity.uuid)))
            # TO FIX
            return self.__add_entity(entity)
        return None

    def add_instance(self, instance):
        assert isinstance(instance, f0rce.Instance)
        f0rce.instance.add(self.component, self.domain, instance)
        return instance

    def add_entity(self, entity):
        assert isinstance(entity, f0rce.Entity)
        f0rce.entity.add(self.component, self.domain, entity)
        return entity

    def del_entity(self, entity):
        assert isinstance(entity, f0rce.Entity)
        if str(entity.uuid) in self.entity:
            f0rce.entity.remove(self.component, self.domain, entity)
            return entity
        return None

    def del_instance(self, instance):
        assert isinstance(instance, f0rce.Instance)
        if str(instance.uuid) in self.instance:
            f0rce.instance.remove(self.component, self.domain, instance)
            return instance
        return None

    def upd_entity(self, entity):
        assert isinstance(entity, f0rce.Entity)
        if str(entity.uuid) in self.entity:
            f0rce.entity.update(self.component, self.domain, entity)
            return entity
        return None

    def upd_instance(self, instance):
        assert isinstance(instance, f0rce.Instance)
        if str(instance.uuid) in self.instance:
            f0rce.instance.update(self.component, self.domain, instance)
            return instance
        return None

    def get_entity(self, uuid):
        assert isinstance(uuid, UUID)
        if str(uuid) in self.entity:
            return self.entity[str(uuid)]
        return None

    def get_instance(self, uuid):
        assert isinstance(uuid, UUID)
        if str(uuid) in self.instance:
            return self.instance[str(uuid)]
        return None
