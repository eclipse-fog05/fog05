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

Native applications plugin

This plugin allow fog05 to manage native applications

supported operation:
- deploy
- destroy
- {{ pid_file }} parameter in starting native applications

todo:

- configure application with parameters

---
package dependencies:

- every native application you need to start
---

python dependencies:

- psutil
- jinja2


---

config dependencies:

- update the nodeid (result of `cat /etc/machine-id` ) in native_plugin.json->configuration->nodeid, and in case the yaks server is not in the same machine, also native_plugin.json->configuration->nodeid with the correct ip:port of the yaks server )