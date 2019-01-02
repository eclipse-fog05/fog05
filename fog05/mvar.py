# Copyright (c) 2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Yaks API

from threading import Condition, Lock


class MVar(object):

    def __init__(self):
        self.__lock = Lock()
        self.__condition = Condition(lock=self.__lock)
        self.__value = None

    def get(self):
        self.__lock.acquire()
        if self.__value is None:
            self.__condition.wait()
        v = self.__value
        self.__value = None
        self.__condition.notify()
        self.__lock.release()
        return v

    def put(self, value):
        self.__lock.acquire()
        if self.__value is not None:
            self.__condition.wait()
        self.__value = value
        self.__condition.notify()
        self.__lock.release()
