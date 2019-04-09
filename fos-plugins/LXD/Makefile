# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

ETC_FOS_DIR = /etc/fos/
VAR_FOS_DIR = /var/fos/
FOS_CONF_FILE = /etc/fos/agent.json
LXD_PLUGIN_DIR = /etc/fos/plugins/LXD
LLXD_PLUGIN_CONFFILE = /etc/fos/plugins/LXD/LXD_plugin.json
all:
	echo "Nothing to do..."

install:
	sudo pip3 install pylxd jinja2 packaging
	sudo usermod -aG lxd fos
ifeq "$(wildcard $(LXD_PLUGIN_DIR))" ""
	sudo cp -r ../LXD /etc/fos/plugins/
else
	sudo cp -r ../LXD/templates /etc/fos/plugins/LXD/
	sudo cp ../LXD/__init__.py /etc/fos/plugins/LXD/
	sudo cp ../LXD/LXD_plugin /etc/fos/plugins/LXD/
	sudo cp ../LXD/LXD_plugin.json /etc/fos/plugins/LXD/
	sudo cp ../LXD/LXDFDU.py /etc/fos/plugins/LXD/
	sudo cp ../LXD/README.md /etc/fos/plugins/LXD/
	sudo ln -sf /etc/fos/plugins/LXD/LXD_plugin /usr/bin/fos_lxd
endif
	sudo cp /etc/fos/plugins/LXD/fos_lxd.service /lib/systemd/system/


uninstall:
	sudo systemctl disable fos_lxd
	gpasswd -d fos lxd
	sudo rm -rf /etc/fos/plugins/LXD
	sudo rm -rf /var/fos/lxd
	sudo rm /lib/systemd/system/fos_lxd.service
	sudo rm -rf /usr/bin/fos_lxd
