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
#
# Powershell script for adding/removing/showing entries to the hosts file.
#
# Known limitations:
# - does not handle entries with comments afterwards ("<ip>    <host>    # comment")
#

$file = "C:\Windows\System32\drivers\etc\hosts"

function add-host([string]$filename, [string]$ip, [string]$hostname) {
    remove-host $filename $hostname
    $ip + "`t`t" + $hostname | Out-File -encoding ASCII -append $filename
}

function remove-host([string]$filename, [string]$hostname) {
    $c = Get-Content $filename
    $newLines = @()

    foreach ($line in $c) {
        $bits = [regex]::Split($line, "\t+")
        if ($bits.count -eq 2) {
            if ($bits[1] -ne $hostname) {
                $newLines += $line
            }
        } else {
            $newLines += $line
        }
    }

    # Write file
    Clear-Content $filename
    foreach ($line in $newLines) {
        $line | Out-File -encoding ASCII -append $filename
    }
}

function print-hosts([string]$filename) {
    $c = Get-Content $filename

    foreach ($line in $c) {
        $bits = [regex]::Split($line, "\t+")
        if ($bits.count -eq 2) {
            Write-Host $bits[0] `t`t $bits[1]
        }
    }
}

try {
    if ($args[0] -eq "add") {

        if ($args.count -lt 3) {
            throw "Not enough arguments for add."
        } else {
            add-host $file $args[1] $args[2]
        }

    } elseif ($args[0] -eq "remove") {

        if ($args.count -lt 2) {
            throw "Not enough arguments for remove."
        } else {
            remove-host $file $args[1]
        }

    } elseif ($args[0] -eq "show") {
        print-hosts $file
    } else {
        throw "Invalid operation '" + $args[0] + "' - must be one of 'add', 'remove', 'show'."
    }
} catch  {
    Write-Host $error[0]
    Write-Host "`nUsage: hosts add <ip> <hostname>`n       hosts remove <hostname>`n       hosts show"
}