# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

ETC_FOS_DIR = /etc/fos/
VAR_FOS_DIR = /var/fos/
FOS_CONF_FILE = /etc/fos/agent.json
KVM_PLUGIN_DIR = /etc/fos/plugins/KVM
LKVM_PLUGIN_CONFFILE = /etc/fos/plugins/KVM/KVM_plugin.json
all:
	cd src/ocaml; make

install:
	sudo pip3 install libvirt-python jinja2
	sudo usermod -aG kvm fos
	sudo usermod -aG libvirtd fos
ifeq "$(wildcard $(KVM_PLUGIN_DIR))" ""
	sudo cp -r ../KVM /etc/fos/plugins/
else
	sudo cp -r ../KVM/templates /etc/fos/plugins/KVM/
	sudo cp ../KVM/__init__.py /etc/fos/plugins/KVM/
	sudo cp ../KVM/KVM_plugin /etc/fos/plugins/KVM/
	sudo cp ../KVM/KVMFDU.py /etc/fos/plugins/KVM/
	sudo cp ../KVM/README.md /etc/fos/plugins/KVM/
	sudo cp /etc/fos/plugins/KVM/fos_kvm.service /lib/systemd/system/
	sudo ln -sf /etc/fos/plugins/KVM/KVM_plugin /usr/bin/fos_kvm
endif


uninstall:
	sudo systemctl disable fos_kvm
	gpasswd -d fos kvm
	gpasswd -d fos libvirtd
	sudo rm -rf /etc/fos/plugins/KVM
	sudo rm -rf /var/fos/kvm
	sudo rm /lib/systemd/system/fos_kvm.service
	sudo rm -rf /usr/bin/fos_kvm
