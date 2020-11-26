# Copyright (c) 2014,2018 ADLINK Technology Inc.
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Windows Plugin

$name = get-wmiobject Win32_NetworkAdapterConfiguration |? {$_.defaultipgateway} | % {$_.GetRelated("win32_NetworkAdapter")} | select NetConnectionID |%{$_.NetConnectionID};
write-output $name