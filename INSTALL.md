# Eclipse fog05 FIM installation.


## Manual Installation



Follow [BUILD.md](BUILD.md) for build instructions.
Then install using
```
$ sudo make install
```


Copy all the plugins needed plugins in the /etc/fos/plugins directory
You need to copy all the files except for the configuration ones for each plugins


If your YAKS server is running on a separate machine, update `ylocator` in the configuration file of agent `/etc/fos/agent.json` and for the plugins `/etc/fos/plugins/<name>/<name>_plugin.json`.


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

