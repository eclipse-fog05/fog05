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



Follow [BUILD.md](BUILD.md) for build instructions.
Then install using
```
$ sudo make install
```


Copy all the plugins needed plugins in the /etc/fos/plugins directory
You need to copy all the files except for the configuration ones for each plugins

Update the configuration files of agent `/etc/fos/agent.json` and the one of the plugins `/etc/fos/plugins/<name>/<name>_plugin.json` by replacing the `uuid` with the UUID of the current node from `/etc/machine-id` converted to UUID4 and the IP address of the eventual yaks server in `ylocator`


Update your descriptor following: https://github.com/eclipse-fog05/examples/blob/master/fim_api/descriptors/fdu_lxd_net.json

## Verify the binaries

The installation script or the manual installation gets binaries from a cloud storage, it may happen that those binaries are not up to date,
you can verify if they are up to date by a checksum verification using `md5sum`

Checksums:
- /etc/fos/agent (x86_64) `3f627bb68cbea21c75e512e783231b29`
- /etc/fos/agent (armv7l) `4d83e0b115d0f8bad8bed79d70cab2a8`
- /etc/fos/agent (aarch64) `0d1e144d5acbad1518390781e6e1cc68`




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

    sudo -u fos /etc/fos/agent -c /etc/fos/agent.json -v

Linux Plugin:

    sudo -u fos fos_linux /etc/fos/plugins/plugin-os-linux/linux_plugin.json

Linux Bridge Plugin:

    sudo -u fos /etc/fos/plugins/plugin-net-linuxbridge/linuxbridge_plugin /etc/fos/plugins/plugin-net-linuxbridge/linuxbridge_plugin.json

LXD Plugin:

    sudo -u fos /etc/fos/plugins/plugin-fdu-lxd/LXD_plugin /etc/fos/plugins/plugin-fdu-lxd/LXD_plugin.json


## Verify that the node is running

Open another shell (or use another machine that has the fog05 api installed)
and execute:

    python3
    >>> from fog05 import FIMAPI
    >>> api = FIMAPI(locator='127.0.0.1') # or locator='IP of the YAKS server'
    >>> api.node.list()
    >>> ['your node uuid',...]
    >>> api.close()

Examples are available in the [examples repository](https://github.com/eclipse-fog05/examples)


REST API for FIM are under development...


## Basic CLI Interface

It is also possible to install a CLI interface, just execute

    ./install_cli.sh


On a node with the fos CLI interface installed declare the env variable `FOS_YAKS_ENDPOINT`
and verify the list of the nodes available

    export FOS_YAKS_ENDPOINT="tcp/<address of yaks server>:7447"
    fos fim node list

