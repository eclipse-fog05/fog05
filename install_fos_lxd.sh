#!/usr/bin/env bash

git clone https://github.com/gabrik/fog05
cd fog05

MACHINE_TYPE=`uname -m`


export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
# sudo dpkg-reconfigure locales

sudo apt update
sudo apt remove --purge lxd lxd-client lxc -y
sudo apt install libev4 libev-dev libssl1.0.0 python3-pip python3-dev curl jq snapd -y
sudo snap install lxd

newgrp lxd << EONG
lxd init --auto
lxd waitready
lxc network create lxdbr0 ipv4.address=auto ipv4.nat=true ipv6.address=none ipv6.nat=false
EONG



sudo pip3 install jsonschema

mkdir -p src/agent/_build/default/fos-agent

if [ ${MACHINE_TYPE} == 'x86_64' ]; then
    curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/y7hvr7j79ibc4pk/fos.tar.gz
elif [ ${MACHINE_TYPE} == 'armv7l' ]; then
    curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/uziduncc4v35zj9/fos.tar.gz
elif [ ${MACHINE_TYPE} == 'aarch64' ]; then
    curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/kcz3pvirb2xmh40/fos.tar.gz
fi



tar -xzvf /tmp/fos.tar.gz -C src/agent/_build/default/fos-agent
rm -rf /tmp/fos.tar.gz

sudo make install

sudo sh -c "cat /etc/machine-id | xargs -i  jq  '.configuration.nodeid = \"{}\"' /etc/fos/plugins/linux/linux_plugin.json > /tmp/linux_plugin.tmp && mv /tmp/linux_plugin.tmp /etc/fos/plugins/linux/linux_plugin.json"

sudo make -C fos-plugins/linuxbridge install

sudo sh -c "cat /etc/machine-id | xargs -i  jq  '.configuration.nodeid = \"{}\"' /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json > /tmp/linuxbridge.tmp && mv /tmp/linuxbridge.tmp /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json"

DP_FACE=$(awk '$2 == 00000000 { print $1 }' /proc/net/route | head -n 1)

sudo sh -c "jq '.configuration.dataplane_interface = \"$DP_FACE\"' /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json > /tmp/linuxbridge.tmp && mv /tmp/linuxbridge.tmp /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json"

sudo make -C fos-plugins/LXD install

sudo sh -c "cat /etc/machine-id | xargs -i  jq  '.configuration.nodeid = \"{}\"' /etc/fos/plugins/LXD/LXD_plugin.json > /tmp/lxd.tmp && mv /tmp/lxd.tmp /etc/fos/plugins/LXD/LXD_plugin.json"

sudo make -C src/utils/python/rest_proxy install



git clone https://github.com/atolab/yaks-python
cd yaks-python
git checkout 0.2
sudo pip3 uninstall yaks -y
sudo make install

sudo systemctl daemon-reload

sudo systemctl start yaks
sudo systemctl start fos_agent
sudo systemctl start fos_linux
sudo systemctl start fos_linuxbridge
sudo systemctl start fos_lxd
sudo systemctl start fosrest
