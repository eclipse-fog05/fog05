# -*-Makefile-*-


NATIVE_PLUGIN_DIR = /etc/fos/plugins/constraint
all:
	echo "Nothing to do..."

install:
	sudo pip3 install jinja2 psutil
ifeq "$(wildcard $(NATIVE_PLUGIN_DIR))" ""
	sudo cp -r ../constraint /etc/fos/plugins/
else
	sudo cp -r ../constraint/templates $(NATIVE_PLUGIN_DIR)
	sudo cp ../constraint/__init__.py $(NATIVE_PLUGIN_DIR)
	sudo cp ../constraint/constraint_plugin $(NATIVE_PLUGIN_DIR)
	sudo cp ../constraint/NativeFDU.py $(NATIVE_PLUGIN_DIR)
	sudo cp ../constraint/README.md $(NATIVE_PLUGIN_DIR)
	sudo cp /etc/fos/plugins/constraint/fos_constraint.service /lib/systemd/system/
	sudo ln -sf /etc/fos/plugins/constraint/constraint_plugin /usr/bin/fos_constraint
endif


uninstall:
	sudo systemctl disable fos_constraint
	sudo rm -rf $(NATIVE_PLUGIN_DIR)
	sudo rm -rf /var/fos/constraint
	sudo rm /lib/systemd/system/fos_constraint.service
	sudo rm -rf /usr/bin/fos_constraint
