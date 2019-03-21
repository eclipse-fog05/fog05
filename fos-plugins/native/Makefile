# -*-Makefile-*-


NATIVE_PLUGIN_DIR = /etc/fos/plugins/native
all:
	echo "Nothing to do..."

install:
	sudo pip3 install jinja2 psutil
ifeq "$(wildcard $(NATIVE_PLUGIN_DIR))" ""
	sudo cp -r ../native /etc/fos/plugins/
else
	sudo cp -r ../native/templates /etc/fos/plugins/native/
	sudo cp ../native/__init__.py /etc/fos/plugins/native/
	sudo cp ../native/native_plugin /etc/fos/plugins/native/
	sudo cp ../native/NativeFDU.py /etc/fos/plugins/native/
	sudo cp ../native/README.md /etc/fos/plugins/native/
	sudo cp /etc/fos/plugins/native/fos_native.service /lib/systemd/system/
	sudo ln -sf /etc/fos/plugins/native/native_plugin /usr/bin/fos_native
endif


uninstall:
	sudo systemctl disable fos_native
	sudo rm -rf /etc/fos/plugins/native
	sudo rm -rf /var/fos/native
	sudo rm /lib/systemd/system/fos_native.service
	sudo rm -rf /usr/bin/fos_native
