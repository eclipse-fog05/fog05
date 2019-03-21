#!/usr/bin/env bash

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



if [ -f {{ dnsmasq_pid_file }} ]; then
   sudo kill -9 $(cat {{ dnsmasq_pid_file }})
   sudo rm {{ dnsmasq_pid_file }}
fi

sudo ip link del {{ bridge }}
sudo ip link del {{ vxlan_intf_name }}


