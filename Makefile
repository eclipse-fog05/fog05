# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

ETC_FOS_DIR = /etc/fos/
VAR_FOS_DIR = /var/fos/
FOS_CONF_FILE = /etc/fos/agent.json
LINUX_PLUGIN_DIR = /etc/fos/plugins/linux
LINUX_PLUGIN_CONFFILE = /etc/fos/plugins/linux/linux_plugin.json
all:


	make -C src/im/ocaml; make -C src/im/ocaml install
	make -C src/core/ocaml; make -C src/core/ocaml install
	make -C src/agent/;

install:

	make -C src/api/python/api install
	make -C src/api/ocaml/api; make -C src/api/ocaml install
ifeq "$(wildcard $(ETC_FOS_DIR))" ""
	sudo mkdir -p /etc/fos/plugins
endif
	sudo id -u fos  >/dev/null 2>&1 ||  sudo useradd -r -s /bin/false fos
	sudo usermod -aG sudo fos
ifeq ($(shell uname -m), x86_64)
	curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/qrqrp0uqwm2kvjl/yaksd.tar.gz
else ifeq ($(shell uname -m), armv7l)
	curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/ku6i5s0t09gayqf/yaks_armv7l.tar.gz
else ifeq ($(shell uname -m), aarch64)
	curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/gzhucpcykegum3d/yaks_arm64.tar.gz
endif
	tar -xzvf /tmp/yaks.tar.gz -C /etc/fos
	rm -rf /tmp/yaks.tar.gz

ifeq "$(wildcard $(VAR_FOS_DIR))" ""
	sudo mkdir -p /var/fos
	sudo chown fos:fos /var/fos
endif

	echo "fos      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
	sudo cp src/agent/_build/default/fos-agent/fos_agent.exe /etc/fos/agent

ifeq "$(wildcard $(LINUX_PLUGIN_DIR))" ""
	sudo cp -r fos-plugins/linux /etc/fos/plugins/
else
	sudo cp -r fos-plugins/linux/scripts /etc/fos/plugins/linux/
	sudo cp fos-plugins/linux/__init__.py /etc/fos/plugins/linux/
	sudo cp fos-plugins/linux/linux_plugin /etc/fos/plugins/linux/
	sudo cp fos-plugins/linux/README.md /etc/fos/plugins/linux/
endif


ifeq "$(wildcard $(FOS_CONF_FILE))" ""
	sudo cp etc/agent.json /etc/fos/agent.json
endif
	sudo cp etc/fos_agent.service /lib/systemd/system/
	sudo cp etc/fos_agent.target /lib/systemd/system/
	sudo cp etc/yaks.service /lib/systemd/system/
	sudo cp etc/yaks.target /lib/systemd/system/
	sudo cp /etc/fos/plugins/linux/fos_linux.service /lib/systemd/system/
	sudo ln -sf /etc/fos/yaksd /usr/bin/yaksd
	sudo ln -sf /etc/fos/agent /usr/bin/fagent
	sudo ln -sf /etc/fos/plugins/linux/linux_plugin /usr/bin/fos_linux

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
	sudo pip3 uninstall fog05 -y

clean:
	make -C src/im/ocaml clean
	make -C src/core/ocaml clean
	make -C src/agent clean
	make -C src/api/ocaml/api clean
	sudo rm -rf src/pyhton/fog05.egg-info
	sudo rm -rf src/pyhton/build
	sudo rm -rf src/pyhton/dist
