#!/usr/bin/env bash

sudo ip link del mecbuildbr
sudo ip link add mecbuildbr type bridge
sudo ip link set mecbuildbr up



lxc profile copy default mecp
lxc profile device add mecp eth1 nic nictype=bridged parent=mecbuildbr
lxc launch images:ubuntu/bionic plat -p mecp
sleep 3;
lxc file push ./ocaml/mec_platform/etc/10-lxc.yaml plat/etc/netplan/10-lxc.yaml
lxc exec plat -- netplan apply
sleep 3;
lxc exec plat -- sudo apt update -qq
lxc exec plat -- sudo apt install curl -y
lxc exec plat -- sudo useradd -m mec
lxc exec plat -- usermod -aG sudo mec
lxc exec plat -- echo "mec      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
lxc exec plat -- mkdir -p /etc/fos/utils/mec
lxc exec plat -- mkdir -p /etc/fos/utils/
lxc exec plat -- curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/g4tnzvjwlx3zcr2/yaksd.tar.gz
lxc exec plat -- tar -xzvf /tmp/yaks.tar.gz -C /etc/fos
lxc exec plat -- rm -rf /tmp/yaks.tar.gz
lxc file push ./ocaml/mec_platform/_build/default/me_platform/me_platform.exe plat/etc/fos/utils/platform
lxc file push -r ./python/dyndns plat/etc/fos/utils
lxc exec plat -- sudo chown mec:mec -R /etc/fos

lxc file push ../../etc/yaks.service plat/lib/systemd/system/
lxc file push ../../etc/yaks.target plat/lib/systemd/system/
lxc file push ./ocaml/mec_platform/etc/mec_platform.service plat/lib/systemd/system/
lxc file push ./python/dyndns/etc/dyndns.service plat/lib/systemd/system/
lxc exec plat -- sudo apt install libev-dev libssl-dev nginx dnsmasq python3 python3-pip -y
lxc exec plat -- sudo pip3 install flask psutil

lxc file push ./ocaml/mec_platform/etc/nginx plat/etc/nginx/sites-available/default
lxc file push ./ocaml/mec_platform/etc/dnsmasq plat/etc/default/dnsmasq
lxc file push ./python/dyndns/etc/mec.conf plat/etc/dnsmasq.d/mec.conf

lxc exec plat -- touch /tmp/dynhosts
# lxc exec plat --  ip -4 -o addr show dev eth0 | awk '{split($4,a,"/");print a[1]}' | xargs -i sed -i -e "s/10.212.26.21/{}/g" /etc/nginx/sites-available/default

lxc exec plat -- systemctl stop nginx
lxc exec plat -- systemctl stop dnsmasq

lxc exec plat -- systemctl daemon-reload
lxc exec plat -- systemctl enable dnsmasq
lxc exec plat -- systemctl enable nginx
lxc exec plat -- systemctl enable yaks
lxc exec plat -- systemctl enable mec_platform
lxc exec plat -- systemctl enable dyndns

lxc exec plat -- systemctl start dnsmasq
lxc exec plat -- systemctl start nginx
lxc exec plat -- systemctl start yaks
lxc exec plat -- systemctl start mec_platform
lxc exec plat -- systemctl start dyndns
