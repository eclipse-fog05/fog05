# Eclipse fog05 FIM installation.

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


## Start Eclipse fog05 FIM

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