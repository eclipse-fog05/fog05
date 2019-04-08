#!/usr/bin/env bash


# Copyright (c) 2014,2019 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - OCamk plugins set



sudo ip netns add fosns-{{ net_id }}
sudo ip link add br-{{ net_id }} type bridge
sudo ip link set dev {{ vlan_intf }}  master br-{{ net_id }}
# sudo ip link set br-{{ net_id }} netns fosns-{{ net_id }}
sudo ip link set up dev br-{{ net_id }}
sudo ip link set up dev {{ vlan_intf }}
sudo ethtool --offload br-{{ net_id }} rx off tx off
