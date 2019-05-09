#!/usr/bin/env bash


lxc launch images:ubuntu/bionic meao
sleep 3;

lxc exec meao -- sudo apt update -qq
lxc exec meao -- sudo apt install curl -y
lxc exec meao -- sudo useradd -m mec
lxc exec meao -- usermod -aG sudo mec
lxc exec meao -- echo "mec      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
lxc exec meao -- mkdir -p /etc/fos/utils/mec
lxc exec meao -- mkdir -p /etc/fos/utils/
lxc exec meao -- curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/g4tnzvjwlx3zcr2/yaksd.tar.gz
lxc exec meao -- tar -xzvf /tmp/yaks.tar.gz -C /etc/fos
lxc exec meao -- rm -rf /tmp/yaks.tar.gz
lxc file push ./ocaml/mec_meao_mepmv/_build/default/meao/meao.exe meao/etc/fos/utils/meao
lxc exec meao -- sudo chown mec:mec -R /etc/fos

lxc file push ../../etc/yaks.service meao/lib/systemd/system/
lxc file push ../../etc/yaks.target meao/lib/systemd/system/
lxc file push ./ocaml/mec_meao_mepmv/etc/mec_meao.service meao/lib/systemd/system/
lxc exec meao -- sudo apt install libev-dev libssl-dev nginx -y

lxc file push ./ocaml/mec_meao_mepmv/etc/nginx meao/etc/nginx/sites-available/default
lxc file push ./ocaml/mec_meao_mepmv/etc/ip_replace.sh meao/tmp/

lxc exec meao --  /tmp/ip_replace.sh

lxc exec meao -- systemctl stop nginx

lxc exec meao -- systemctl daemon-reload
lxc exec meao -- systemctl enable nginx
lxc exec meao -- systemctl enable yaks
lxc exec meao -- systemctl enable mec_meao

lxc exec meao -- systemctl start nginx
lxc exec meao -- systemctl start yaks
lxc exec meao -- systemctl start mec_meao
