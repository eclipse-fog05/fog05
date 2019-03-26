#!/bin/bash

CONF="/etc/fos/lldpd/lldpd.conf"

if [ -n "$1" ]; then
	CONF=$1
fi

sudo lldpd -d -k -O $CONF
