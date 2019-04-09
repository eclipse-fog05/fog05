#!/usr/bin/env bash

screen -S yaks -dm bash -c 'yaksd -vv'
sleep 1
screen -S agent -dm bash -c 'sudo -u fos fagent -c /etc/fos/agent.json -v'
sleep 1
screen -S linuxp -dm bash -c 'sudo -u fos fos_linux /etc/fos/plugins/linux/linux_plugin.json'
sleep 1
screen -S netp -dm bash -c 'sudo -u fos /etc/fos/plugins/linuxbridge/linuxbridge_plugin /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json'
sleep 1
screen -S lxdp -dm bash -c 'sudo -u fos /etc/fos/plugins/LXD/LXD_plugin  /etc/fos/plugins/LXD/LXD_plugin.json'

read -n 1 -s -r -p "Press any key to destroy..."

screen -S lxdp -X quit
sleep 5
screen -S netp -X quit
sleep 3
screen -S linuxp -X quit
sleep 1
screen -S agent -X quit
sleep 1
screen -S yaks -X quit
