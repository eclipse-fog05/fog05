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


import sys
import os
from fog05.interfaces.States import State

class EntityInstance(object):

    def __init__(self,uuid, entity_uuid):
        self.state=State.CONFIGURED
        self.uuid=uuid
        self.name=''
        self.entity_uuid = entity_uuid


    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def on_configured(self, configuration):
        raise NotImplementedError('This is and interface!')

    def on_clean(self):
        raise NotImplementedError('This is and interface!')

    def on_start(self):
        raise NotImplementedError('This is and interface!')

    def on_stop(self):
        raise NotImplementedError('This is and interface!')

    def on_pause(self):
        raise NotImplementedError('This is and interface!')

    def on_resume(self):
        raise NotImplementedError('This is and interface!')

    def before_migrate(self):
        raise NotImplementedError('This is and interface!')

    def after_migrate(self):
        raise NotImplementedError('This is and interface!')

    def __eq__(self, other):
        if isinstance(other, EntityInstance):
            return self.uuid == other.uuid
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result