# Eclipse fog05 FIM installation.


## Script Installation
---

In order to run install Eclipse fog05 as FIM (Fog Infrastrucutre Manager)
you have to execute the following commands


    ./fos_install.sh

Then you have to edit the agent and linux plugin configuration file


Agent configuration file: `/etc/fos/agent.json`

update the mgmt_interface parameter with the name of the interface used for managment
update the autoload parameter to false



Linux Plugin configuration file: `/etc/fos/plugins/linux/linux_plugin.json`

update the nodeid parameter with the content of `/etc/machine-id`
this is used to identify the node and to make the plugin connect the right agent.


If you want to run contanerized applications on the node, you have to install and configure LXD

sudo apt remove --purge lxd
sudo snap install lxd
sudo lxd init

add current user to lxd and verify that it is operational (eg. launch a container `lxc launch images:alpine/edge test` and remove it `lxc delete --force test`)
then execute the following commands:


    cd fog05/fos-plugins/linuxbridge/
    sudo make install


and then edit the Linux Bridge plugin configuration file:  `/etc/fos/plugins/linuxbridge/linuxbridge_plugin.json`

update the nodeid parameter with the content of `/etc/machine-id`
this is used to identify the node and to make the plugin connect the right agent.
update the dataplane_interface parameter with the name of the interface used for dataplane (VxLANs will be created over that interface)


then you have to install the LXD plugin

    cd fog05/fos-plugins/LXD
    sudo make install


and then edit the LXD plugin configuration file:  `/etc/fos/plugins/LXD/LXD_plugin.json`

update the nodeid parameter with the content of `/etc/machine-id`
this is used to identify the node and to make the plugin connect the right agent.


## Manual Installation 

Remove everything:

```
pip3 uninstall -y fog05 yaks papero 

```


Install zenoh API

```
wget https://github.com/atolab/atobin/blob/master/zenoh-c/unstable/ubuntu/16.04/libzenohc.so
sudo cp libzenohc.so /usr/local/lib
git clone https://github.com/atolab/zenoh-python
cd zenoh-python
sudo python3 setup.py install
cd ..

```

Install YAKS API


```
git clone https://github.com/atolab/yaks-python
cd yaks-python
sudo make install

```



Clone fog05

```
git clone https://github.com/eclipse/fog05 
cd fog05
```

Make and install the python types and API


```
sudo pip3 install pyang pyangbind
make -C src/im/python
make -C src/im/python install
make -C src/api/python/api install

```

Copy all the plugins needed plugins in the /etc/fos/plugins directory
You need to copy all the files except for the configuration ones for each plugins

Update the configuration files of agent `/etc/fos/agent.json` and the one of the plugins `/etc/fos/plugins/<name>/<name>_plugin.json` by replacing the `uuid` with the UUID of the current node from `/etc/machine-id` converted to UUID4 and the IP address of the eventual yaks server in `ylocator`


Download and install the agent (this link is for the x86_64 one)

```
curl -L -o /tmp/agent.tar.gz https://www.dropbox.com/s/y7hvr7j79ibc4pk/fos.tar.gz
tar -xzvf /tmp/agent.tar.gz
sudo cp /tmp/agent /etc/fos/agent

```


Download and install yaks


```

curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/v55js274504z5f5/yaks.tar.gz
tar -xzvf /tmp/agent.tar.gz
sudo cp /tmp/zenohd /etc/fos/zenohd
sudo cp /tmp/yaks-plugin.cmxs /etc/fos/yaks-plugin.cmxs
sudo cp /tmp/yaksd /etc/fos/yaksd
```


Update your descriptor following: https://github.com/atolab/fog05_demo/blob/master/fim_api/fdu_lxd_net.json

Example of start.py script https://github.com/atolab/fog05_demo/blob/master/fim_api/yaks/start.py


## Verify the binaries

The installation script or the manual installation gets binaries from a cloud storage, it may happen that those binaries are not up to date,
you can verify if they are up to date by a checksum verification using `md5sum`

Checksums:
- agent (x86_64) `3f627bb68cbea21c75e512e783231b29`
- agent (armv7l)
- agent (aarch64) 




# Start Eclipse fog05

There are two ways to start fog05, the first one using systemd and the second one by hand,
the second one is the one to be used during development.

## Start Eclipse fog05 FIM using systemd

In order to start Eclipse fog05 FIM using systemd you have to first enable it
by using the script present under `etc/systemd/enable.sh` this will enable autostart of the fog05 Node

    $ cd fog05
    $ ./etc/systemd/enable
    $ ./etc/systemd/start

This will start all the component for an all-in-one fog05 installation.

## Start Eclipse fog05 FIM by hand

As this version is still under development you have to start all the components by hand
(even if a systemd service is provided and installed, but start manually is more safe at the moment)

You need at least 5 shells/screens, as you have to start

1. Yaks server
2. Eclipse fog05 Agent
3. Linux Plugin
4. Linux Bridge Plugin
5. LXD Plugin


to start the components:

YAKS:
    yaksd -vv

 Agent:

    sudo -u fos fagent -c /etc/fos/agent.json -v

Linux Plugin:

    sudo -u fos fos_linux /etc/fos/plugins/linux/linux_plugin.json

Linux Bridge Plugin:

    sudo -u fos /etc/fos/plugins/linuxbridge/linuxbridge_plugin /etc/fos/plugins/linuxbridge/linuxbridge_plugin.json

LXD Plugin:

    sudo -u fos /etc/fos/plugins/LXD/LXD_plugin /etc/fos/plugins/LXD/LXD_plugin.json


## Verify that the node is running

Open another shell (or use another machine that has the fog05 api installed)
and execute:

    python3
    >>> from fog05 import FIMAPI
    >>> api = FIMAPI(locator='127.0.0.1') # or locator='IP of the YAKS server'
    >>> api.node.list()
    >>> ['your node uuid',...]
    >>> api.close()

Examples are available in https://github.com/atolab/fog05_demo/tree/master/fim_api


REST API for FIM is under development...


## Basic CLI Interface

It is also possible to install a CLI interface, just execute

    ./install_cli.sh


On a node with the fos CLI interface installed declare the env variable `FOS_YAKS_ENDPOINT`
and verify the list of the nodes available

    export FOS_YAKS_ENDPOINT="tcp/<address of yaks server>:7447"
    fos fim node list

