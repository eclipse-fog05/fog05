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

{{ command }} & echo $! > {{outfile}}.pid



# Try this way!
#
# screen -dmSL [session name] [commands]
#
# -d starts a screen session and immediately detaches from it
# -m forces creating a new screen session
# -S lets you give the session a name
# -L turns on logging to ~/screenlog.0
#
# screen -dmS testx -L script.log ping google.com && screen -S testx -Q echo '$PID'
#