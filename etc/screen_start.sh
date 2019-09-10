#!/usr/bin/env bash

screen -S yaks -dm bash -c 'sudo -u fos yaksd -vv'
sleep 1
screen -S rest -dm bash -c 'sudo -u fos YAKS_HOST=127.0.0.1 python3 /etc/fos/rest/service.py /etc/fos/rest/service.json '
sleep 1
screen -S agent -dm bash -c 'sudo -u fos /etc/fos/agent -c /etc/fos/agent.json -v'
sleep 1
screen -S linuxp -dm bash -c 'sudo -u fos /etc/fos/plugins/linux/linux_plugin /etc/fos/plugins/linux/linux_plugin.json'
sleep 1
screen -S netp -dm bash -c 'sudo -u fos /etc/fos/plugins/linuxbridge/linuxbridge_plugin /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json'
sleep 1
screen -S lxdp -dm bash -c 'sudo -u fos /etc/fos/plugins/LXD/LXD_plugin  /etc/fos/plugins/LXD/LXD_plugin.json'

echo "Running on screen..."
