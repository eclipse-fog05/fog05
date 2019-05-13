#!/usr/bin/env bash

ip -4 -o addr show dev eth0 | awk '{split($4,a,"/");print a[1]}' | xargs -i sed -i -e "s/ip/{}/g" /etc/nginx/sites-available/default