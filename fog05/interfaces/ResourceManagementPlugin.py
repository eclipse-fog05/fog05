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

from fog05.interfaces.Plugin import Plugin


class ResourceManagementPlugin(Plugin):

    def __init__(self, version, plugin_uuid=None):
        super(ResourceManagementPlugin, self).__init__(version, plugin_uuid)

    def configure_application(self, application_uuid, application_manifest):
        raise NotImplementedError

    def get_application_configuration(self, application_uuid):
        raise NotImplementedError
