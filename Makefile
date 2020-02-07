# -*-Makefile-*-


WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

ETC_FOS_DIR = /etc/fos/
VAR_FOS_DIR = /var/fos/
FOS_CONF_FILE = /etc/fos/agent.json
LINUX_PLUGIN_DIR = /etc/fos/plugins/plugin-os-linux
LINUX_PLUGIN_CONFFILE = /etc/fos/plugins/plugin-os-linux/linux_plugin.json
UUID = $(shell ./etc/to_uuid.sh)



all: ocaml-sdk ocaml-api agent

submodules:
	git submodule update --init --recursive
	# git submodule foreach git pull origin master


ocaml-sdk:
	make -C sdk/sdk-ocaml install

ocaml-api:
	make -C api/api-ocaml install

sdk-go:
	ln -s sdk/sdk-go/fog05sdk ${GOPATH}/src
	go install fog05sdk


api-go:
	ln -s api/api-go/fog05 ${GOPATH}/src
	go install fog05

sdk-python:
	pip3 install pyangbind pyang
	make -C sdk/sdk-python
	make -C sdk/sdk-python install

api-python:
	make -C api/api-python install


agent:
	make -C src/agent

install: sdk-python api-python


ifeq "$(wildcard $(ETC_FOS_DIR))" ""
	sudo mkdir -p /etc/fos/plugins
endif

	make -C src/agent install

	sudo id -u fos  >/dev/null 2>&1 ||  sudo useradd -r -s /bin/false fos
	sudo usermod -aG sudo fos
	cp ./fos_build/zenohd/_build/default/zenoh-router-daemon/zenohd.exe /etc/fos/zenohd
	cp ./fos_build/yaks/_build/default/src/yaks/yaks-plugin.cmxs /etc/fos/zenohd/yaks-plugin.cmxs

ifeq "$(wildcard $(VAR_FOS_DIR))" ""
	sudo mkdir -p /var/fos
	sudo chown fos:fos /var/fos
endif

	echo "fos      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
	make -C plugins/plugin-os-linux install

	sudo cp etc/yaks.service /lib/systemd/system/
	sudo cp etc/yaks.target /lib/systemd/system/

lldp:
	sudo mkdir -p /etc/fos/lldpd
	sudo ./etc/lldp/build.sh
	sudo ./etc/lldp/config.sh
	sudo cp ./etc/lldp/run.sh /etc/fos/lldpd/run.sh
	sudo systemctl disable lldpd
	sudo systemctl stop lldpd

cli:
	make -C src/utils/ocaml/cli install

uninstall:
	sudo systemctl stop fos_agent
	sudo systemctl disable fos_agent
	sudo systemctl disable fos_linux
	sudo rm -rf /etc/fos
	sudo rm -rf /var/fos
	sudo rm /lib/systemd/system/fos_agent.service
	sudo rm /lib/systemd/system/fos_agent.target
	sudo rm /lib/systemd/system/yaks.target
	sudo rm /lib/systemd/system/yaks.service
	sudo rm /lib/systemd/system/fos_linux.service
	sudo rm -rf /etc/fos/yaksd
	sudo rm -rf /etc/fos/agent
	sudo rm -rf /usr/bin/fos_linux
	sudo userdel fos
	sudo pip3 uninstall fog05-sdk fog05 -y
	opam uninstall fos-sdk

clean:
	make -C src/agent clean
