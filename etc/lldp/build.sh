#!/usr/bin/env bash

sudo apt update -qq
sudo apt install -y git build-essential pkg-config automake libtool

if [ -d lldpd ]; then
	if [ -d lldpd/.git  ]; then
		cd lldpd
		git pull
		cd ..
	else
		sudo rm -rf lldpd
	fi
fi
if [ ! -d lldpd ]; then
	git clone https://github.com/vincentbernat/lldpd.git
fi

if [ ! -d /usr/local/var/run ]; then
	sudo mkdir -p /usr/local/var/run
fi

cd lldpd
git checkout 1.0.3
./autogen.sh
./configure --with-privsep-user=nobody --with-privsep-group=nogroup
make
sudo make install
sudo ldconfig
cd ..
