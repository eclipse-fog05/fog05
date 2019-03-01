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


from fog05.interfaces.States import State


class FDU(object):

    def __init__(self):
        self.state = State.UNDEFINED
        self.uuid = ''
        self.name = ''
        self.interfaces = None
        self.image = None
        self.cps = None

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def get_short_id(self):
        return ''.join([x[0] for x in self.uuid.split('-')])

    def get_image_uri(self):
        return self.image.get('uri')

    def get_image_checksum(self):
        return self.image.get('checksum')

    def get_image_format(self):
        return self.image.get('format')

    def get_interfaces(self):
        return self.interfaces

    def get_connection_points(self):
        return self.cps

    def on_defined(self):
        raise NotImplementedError('This is and interface!')

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

    def __str__(self):
        return "Name : {0} UUID: {1}".format(self.name, self.uuid)
