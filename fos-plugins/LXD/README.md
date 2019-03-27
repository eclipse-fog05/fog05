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


LXD plugin

This plugin allow fog05 to manage lxd container

supported operation:


todo:

- scale of vm
- deploy
- migrate
- destroy
- stop
- pause
- resume

---
package dependencies:

- lxd
- lxd-client
---

python dependencies:

- pylxd
- packaging
- jinja2


---

config dependencies:

- update the nodeid (result of `cat /etc/machine-id` ) in LXD_plugin.json->configuration->nodeid, and in case the yaks server is not in the same machine, also LXD_plugin.json->configuration->nodeid with the correct ip:port of the yaks server )

WARNING:

if you use lxd from snap
https://github.com/lxc/pylxd/issues/257
export LXD_DIR=/var/snap/lxd/common/lxd/



## LIVE MIGRATION:
In order to perform live migration of lxd container you need CRIU installed and configured

    $ sudo apt install criu
    $ sudo snap set lxd criu.enable=true

