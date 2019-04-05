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


sudo ip link add dhcp-{{ netid }}-i type veth peer name dhcp-{{ netid }}-e
sudo ip link set dhcp-{{ netid }}-i netns fosns-{{ netid }}
sudo ip link set dhcp-{{ netid }}-e master br-{{ netid }}
sudo ip link set dhcp-{{ netid }}-e up
# sudo ip link set dhcp-{{ netid }}-i up
# sudo ip netns exec {{ vnetns }} dnsmasq --no-hosts --no-resolv --stri-order --interface=dhcp-{{ netid }}-i --bind-interfaces --dhcp-range={{ dhcp_start }},{{ dhcp_end }}  -x  {{ pid_path }} --except-interface=lo
sudo ip netns exec fosns-{{ netid }} ifconfig dhcp-{{ netid }}-i {{ ip }} netmask {{ mask }}
sudo ip netns exec fosns-{{ netid }} dnsmasq -C {{ dhcp_conf_path }}