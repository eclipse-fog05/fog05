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

import ykon
import threading


class Announce:
    def __init__(self, component):
        assert isinstance(component, ykon.Component)
        self.component = component
        self.path = []
        self.interval = 5
        self.__timer = None

    def add(self, path):
        """
        Add a path for the component's announcement
        """
        if path not in self.path:
            self.path.append(path)

    def remove(self, path):
        """
        Remove a path from the component's announcement
        """
        if path in self.path:
            self.path.remove(path)

    def start(self):
        """
        Periodically announce the presence of the component on YAKS
        """
        for p in self.path:
            self.component.yaks.publish(p, self.component._info())
        self.__timer = threading.Timer(self.interval, self.start)
        self.__timer.start()

    def stop(self):
        """
        Stop the periodic announcment
        """
        if not self.__timer:
            return
        self.__timer.cancel()
        self.__timer = None
        path = ykon.path.leave.format(**{'package': self.component.package})
        self.component.yaks.publish(path, self.component._info())

    def register(self):
        path = ykon.path.announce.format(**{'package': self.component.package})
        self.add(path)

    def unregister(self):
        self.stop()
        for p in list(self.path):
            self.remove(p)
