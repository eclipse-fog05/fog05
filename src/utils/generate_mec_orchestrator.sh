#!/usr/bin/env bash


lxc launch images:ubuntu/bionic meao
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
lxc file push ./ocaml/mec_meao_mepmv/_build/default/meao/meao.exe plat/etc/fos/utils/meao
lxc exec plat -- sudo chown mec:mec -R /etc/fos

lxc file push ../../etc/yaks.service plat/lib/systemd/system/
lxc file push ../../etc/yaks.target plat/lib/systemd/system/
lxc file push ./ocaml/mec_meao_mepmv/etc/mec_meao.service plat/lib/systemd/system/
lxc exec plat -- sudo apt install libev-dev libssl-dev nginx -y

lxc file push ./ocaml/mec_meao_mepmv/etc/nginx plat/etc/nginx/sites-available/default
lxc file push ./ocaml/mec_meao_mepmv/etc/ip_replace.sh plat/tmp/

lxc exec plat --  /tmp/ip_replace.sh

lxc exec plat -- systemctl stop nginx

lxc exec plat -- systemctl daemon-reload
lxc exec plat -- systemctl enable nginx
lxc exec plat -- systemctl enable yaks
lxc exec plat -- systemctl enable mec_meao

lxc exec plat -- systemctl start nginx
lxc exec plat -- systemctl start yaks
lxc exec plat -- systemctl start mec_platform
