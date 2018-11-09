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

from yaks import YAKS


class MEAO_API(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.__yaks = YAKS(self.endpoint)

    def deploy_service(self, descriptor):
        pass

    def remove_service(self, service_uuid):
        pass

    def configure_service(self, service_uuid, configuration):
        pass

    def get_service_configuration(self, service_uuid):
        pass

    def stop_service(self, service_uuid):
        pass

    def restart_service(self, service_uuid):
        pass

    def get_services(self):
        pass

    def get_service(self, service_uuid):
        pass

    def deploy_app(self, descriptor):
        pass

    def remove_app(self, app_uuid):
        pass

    def get_platforms(self):
        pass

    def get_platform(self, platform_uuid):
        pass
