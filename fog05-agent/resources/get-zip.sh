#!/usr/bin/env bash

ip addr show dev $(awk '$2 == 00000000 { print $1 }' /proc/net/route | head -n1) | awk '$1 ~ /^inet/ { sub("/.*", "", $2); print $2 }' | head -n1