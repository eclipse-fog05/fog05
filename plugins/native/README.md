<!-- # Copyright (c) 2014,2018 ADLINK Technology Inc.
# 
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
# 
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0
# 
# SPDX-License-Identifier: EPL-2.0
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

