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


KVM Libvirt plugin

This plugin allow fog05 to manage vm

supported operation:
- deploy
- destroy
- stop
- pause
- resume

todo:
- migrate
- scale of vm

---
package dependencies:

- libvirt-bin
- libvirt-dev
- genisofs
- seabios
- python3-libvirt
- qemu-img
- wget
- libguestfs-tools

---

python dependencies:

- libvirt-python
- jinja2



---

config dependencies:

- in `/etc/libvirt/qemu.conf` user and group should be set in a way that the agent can read log files (user =
fos, group = libvirtd)
- in `/etc/default/libvirt-bin` uncomment libvirtd_opts and modity to libvirtd_opts="-l -d"
- in `/etc/libvirt/libvirtd.conf` set and uncomment listen_tls = 0 and listen_tcp = 1
- restart libvirt service (sudo service libvirt-bin restart)
- update the nodeid (result of `cat /etc/machine-id` ) in KVM_plugin.json->configuration->nodeid, and in case the yaks server is not in the same machine, also KVM_plugin.json->configuration->nodeid with the correct ip:port of the yaks server )