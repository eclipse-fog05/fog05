#!/usr/bin/env bash


sudo ip link add mecbuildbr
sudo ip link set mecbuildbr up


lxc profile copy default mecp
lxc profile device add mecp eth1 nic nictype=bridged parent=mecbuildbr
lxc launch images:ubuntu/bionic plat -p mecp
sleep 3;
lxc file push ./ocaml/mec_platform/etc/10-lxc.yaml plat/etc/netplan/10-lxc.yaml
lxc exec plat -- netplan apply
sleep 3;
lxc exec plat -- id -u mec  >/dev/null 2>&1 ||  useradd -m mec
lxc exec plat -- usermod -aG sudo fos
lxc exec plat -- echo "mec      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
lxc exec plat -- mkdir -p /etc/fos/utils/mec
lxc exec plat -- mkdir -p /etc/fos/utils/
lxc exec plat -- curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/g4tnzvjwlx3zcr2/yaksd.tar.gz
lxc exec plat -- tar -xzvf /tmp/yaks.tar.gz -C /etc/fos
lxc exec plat -- rm -rf /tmp/yaks.tar.gz
lxc file push ./ocaml/mec_platform/_build/default/me_platform/me_platform.exe plat/var/fos/utils/platform
lxc file push -r ./python/dyndns plat/var/fos/utils
lxc exec plat -- sudo chown mec:mec -R /var/fos

lxc file push ../../etc/yaks.service plat/lib/systemd/system/
lxc file push ../../etc/yaks.target plat/lib/systemd/system/
lxc file push ./ocaml/mec_platform/etc/mec_platform.service plat/lib/systemd/system/
lxc file push .python/dyndns/etc/dyndns.service plat/lib/systemd/system/
lxc exec -- apt install libev-dev libssl-dev nginx dnsmasq python3 python3-pip
lxc exec -- pip3 install flask psutil

lxc file push ./ocaml/mec_platform/etc/nginx plat/etc/nginx/sites-available/default
lxc file push ./ocaml/mec_platform/etc/dnsmasq plat/etc/default/dnsmasq

lxc exec -- systemctl daemon-reload
lxc exec -- systemctl enable dnsmasq
lxc exec -- systemctl enable nginx
lxc exec -- systemctl enable yaks
lxc exec -- systemctl enable mec_platfrom
lxc exec -- systemctl enable dyndns

lxc exec -- systemctl start dnsmasq
lxc exec -- systemctl start nginx
lxc exec -- systemctl start yaks
lxc exec -- systemctl start mec_platform
lxc exec -- systemctl start dyndns
