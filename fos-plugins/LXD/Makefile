# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

ETC_FOS_DIR = /etc/fos/
VAR_FOS_DIR = /var/fos/
FOS_CONF_FILE = /etc/fos/agent.json
LXD_PLUGIN_DIR = /etc/fos/plugins/LXD
LLXD_PLUGIN_CONFFILE = /etc/fos/plugins/LXD/LXD_plugin.json
all:
	cd src/ocaml; make

install:
	sudo pip3 install pylxd jinja2 packaging
ifeq "$(wildcard $(LXD_PLUGIN_DIR))" ""
	sudo cp -r fos-plugins/LXD /etc/fos/plugins/
else
	sudo cp -r fos-plugins/LXD/templates /etc/fos/plugins/LXD/
	sudo cp fos-plugins/LXD/__init__.py /etc/fos/plugins/LXD/
	sudo cp fos-plugins/LXD/LXD_plugin /etc/fos/plugins/LXD/
	sudo cp fos-plugins/LXD/LXDFDU.py /etc/fos/plugins/LXD/
	sudo cp fos-plugins/LXD/README.md /etc/fos/plugins/LXD/
	sudo cp /etc/fos/plugins/LXD/fos_lxd.service /lib/systemd/system/
endif


uninstall:
	sudo systemctl disable fos_lxd
	sudo rm -rf /etc/fos
	sudo rm -rf /var/fos/lxd
	sudo rm /lib/systemd/system/fos_lxd.service
