<!-- # Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Base plugins set -->


Linux os plugin

This plugin allow fog05 to run on top on linux

supported operation:
- execute command
- check that file exists
- save on file
- read from file
- get hw information (cp,ram,network,disks)
- get uuid from motherboard
- get hostname
- send signal
- check if a pid exists
- install packages
- remove packages

todo:

- get detailed i/o informations
- get hw accelerators informations
- get pid from process name
- get monitoring information about network
- get gps information about node

---


python dependencies:

- psutil
- netifaces

--

config dependencies:
- update the nodeid (result of `cat /etc/machine-id` ) in linux_plugin.json->configuration->nodeid, and in case the yaks server is not in the same machine, also linux_plugin.json->configuration->nodeid with the correct ip:port of the yaks server )

- user should be able to use sudo without password asking (`echo "username  ALL=(ALL) NOPASSWD: ALL"  >> /etc/sudoers`)

