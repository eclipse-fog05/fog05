# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

LB_PLUGIN_DIR = /etc/fos/plugins/linuxbridge
LB_PLUGIN_CONFFILE = /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json
all:
	cd src/ocaml; make

install:
	sudo pip3 install jinja2
ifeq "$(wildcard $(LB_PLUGIN_DIR))" ""
	sudo cp -r ../linuxbridge /etc/fos/plugins/
else
	sudo cp -r ../linuxbridge/templates /etc/fos/plugins/linuxbridge/
	sudo cp ../linuxbridge/__init__.py /etc/fos/plugins/linuxbridge/
	sudo cp ../linuxbridge/linuxbridge_plugin /etc/fos/plugins/linuxbridge/
	sudo cp ../linuxbridge/README.md /etc/fos/plugins/linuxbridge/
	sudo cp /etc/fos/plugins/linuxbridge/fos_linuxbridge.service /lib/systemd/system/
	sudo ln -sf /etc/fos/plugins/linuxbridge/linuxbridge_plugin /usr/bin/fos_linuxbridge
endif


uninstall:
	sudo systemctl disable fos_linuxbridge
	sudo rm -rf /etc/fos/plugins/linuxbridge
	sudo rm -rf /var/fos/linuxbridge
	sudo rm /lib/systemd/system/fos_linuxbridge.service
	sudo rm -rf /usr/bin/fos_linuxbridge
