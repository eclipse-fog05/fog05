# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

REST_API_DIR = /etc/fos/rest
REST_API_CONFIG = /etc/fos/rest/service.json
all:
	echo "Nothing to do"

install:
	sudo pip3 install flask
ifeq "$(wildcard $(REST_API_DIR))" ""
	sudo cp -r ./src/service.py $(REST_API_DIR)/service.py
	sudo cp -r ./src/service.json $(REST_API_CONFIG)
else
	sudo mkdir -p $(REST_API_DIR)
	sudo mkdir -p $(REST_API_DIR)/imgs
	sudo cp -r ./src/service.py $(REST_API_DIR)/service.py
	sudo cp -r ./src/service.json $(REST_API_CONFIG)
	sudo ln -sf $(REST_API_DIR)/service.py /usr/bin/fos_rest
endif
	sudo cp ./fosrest.service /lib/systemd/system/

	sudo chown fos:fos -R $(REST_API_DIR)

uninstall:
	sudo systemctl disable fosrest
	sudo rm -rf $(REST_API_DIR)
	sudo rm /lib/systemd/system/fosrest.service
	sudo rm -rf /usr/bin/fos_rest
