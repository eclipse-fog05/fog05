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

sudo ip netns exec  fosns-{{ net_id }} ip link add br-{{ net_id }}-ns type bridge

sudo ip link add l-{{ net_id }}-i type veth peer name l-{{ net_id }}-e
sudo ip link set l-{{ net_id }}-e netns fosns-{{ net_id }}
sudo ip link set l-{{ net_id }}-i master br-{{ net_id }}
sudo ip link set l-{{ net_id }}-i up


sudo ip netns exec  fosns-{{ net_id }} ip link set br-{{ net_id }}-ns up
sudo ip netns exec fosns-{{ net_id }} ip link set l-{{ net_id }}-e master br-{{ net_id }}-ns
sudo ip netns exec fosns-{{ net_id }} ip link set l-{{ net_id }}-e up

sudo ip link add name vxl-{{ net_id }} type vxlan id {{ group_id }} group {{ mcast_group_address }} dstport 4789 dev {{ wan }}
sudo ip link set dev vxl-{{ net_id }} master br-{{ net_id }}
sudo ip link set up dev br-{{ net_id }}
sudo ip link set up dev vxl-{{ net_id }}
sudo ethtool --offload br-{{ net_id }} rx off tx off
