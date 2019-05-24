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

from enum import Enum


class RuntimeCode(Enum):
    UNKNOWN = 0
    LXD = 1
    KVM = 2
    NATIVE = 3

class ComponentCode(Enum):
    UNKNOWN = 0
    VIM = 1
    ORC = 2
    LCM = 3

class InstanceState(Enum):
    UNKNOWN = 0
    UNDEFINED = 1
    DEFINED = 2
    CONFIGURED = 3
    RUNNING = 4
    SCALING = 5
    MIGRATING = 6
    TAKING_OFF = 7
    LANDING = 8
    PAUSED = 9
    ONCONFIGURE = 10
    ONCLEAN = 11
    ONSTART = 12
    ONSTOP = 13
    ONPAUSE = 14
    ONDEFINE = 15
    ONUNDEFINE = 16

class InterfaceType(Enum):
    UNKNOWN = 0
    PHYSICAL = 1
    VIRTUAL = 2

class InterfaceMACType(Enum):
    UNKNOWN = 0
    PARAVIRT = 1
    PCI_PASSTHROUGH = 2
    SR_IOV = 3
    VIRTIO = 4
    E1000 = 5
    RTL8139 = 6
    PCNET = 7
    BRIDGED = 8
