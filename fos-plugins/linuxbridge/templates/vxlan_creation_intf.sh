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


sudo ip link add {{ bridge_name }} type bridge
sudo ip link add name {{ vxlan_intf_name }} type vxlan id {{ group_id }} group {{ mcast_group_address }} dstport 4789 dev {{ wan }}
sudo ip link set dev {{ vxlan_intf_name }} master {{ bridge_name }}
#sudo brctl addif  {{ bridge_name }} {{ vxlan_intf_name }}
#sudo brctl stp  {{ bridge_name }} off
sudo ip link set up dev {{ bridge_name }}
sudo ip link set up dev {{ vxlan_intf_name }}

#this should be done on all nodes, or all nodes that have entity on that network
#uses multicast how to do with nodes in differents subnets?
#


### use ip for bridge creation