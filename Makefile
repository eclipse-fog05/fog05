# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

all:


	cd src/ocaml; make

install:

	cd src/python; sudo python3 setup.py install
	sudo useradd -r -s /bin/false fos
	sudo usermod -aG sudo fos
	sudo mkdir -p /etc/fos/plugins
	curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/ix28wgn4kqqonaa/yaksd.tar.gz
	tar -xzvf /tmp/yaks.tar.gz -C /etc/fos
	rm -rf /tmp/yaks.tar.gz
	sudo mkdir -p /var/fos
	sudo chown fos:fos /var/fos
	echo "fos      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
	sudo cp src/ocaml/_build/default/src/fos/fos-agent/fos_agent.exe /etc/fos/agent
	sudo cp -r fos-plugins/* /etc/fos/plugins
	sudo cp etc/agent.json /etc/fos/agent.json
	sudo cp etc/fos_agent.service /lib/systemd/system/
	sudo cp etc/fos_agent.target /lib/systemd/system/
	sudo cp etc/yaks.service /lib/systemd/system/
	sudo cp etc/yaks.target /lib/systemd/system/
	sudo cp /etc/fos/plugins/linux/fos_linux.service /lib/systemd/system/

uninstall:
	sudo systemctl stop fos_agent
	sudo systemctl disable fos_agent
	sudo systemctl disable fos_linux
	sudo rm -rf /etc/fos
	sudo rm -rf /var/fos
	sudo rm /lib/systemd/system/fos_agent.service
	sudo rm /lib/systemd/system/fos_agent.target
	sudo rm /lib/systemd/system/fos_linux.service
	sudo userdel fos
	sudo pip3 uninstall fog05 -y

clean:
	cd src/ocaml; make clean
	sudo rm -rf src/pyhton/fog05.egg-info
	sudo rm -rf src/pyhton/build
	sudo rm -rf src/pyhton/dist
