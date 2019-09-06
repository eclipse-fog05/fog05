# fog05 Deployment Guide for 5GCity

The Eclipse fog05 ExtendedEdge-VIM has to be deployed following this instructions.

It is divided in two main components

- REST API Server + Image Server + YAKS  (Use for interaction with OSM) Expose port 8080 7887
- Compute Portion (Agent, LinuxPlugin, LinuxBridge Plugin, LXD Plugin)


The first components as to be deployed in a VM with the following specifications:

- 1 vCPU
- 1 GB RAM
- 40 GB Disk (or less this really depends in the space needed for the images)
- Ubuntu 16.04
- docker


### VM Configuration

Install docker-ce [Following these instructions](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
Add user to docker group and initiate docker swarm

```
$ sudo usermod -aG docker <username>
$ exit
$ ssh to vm
$ docker swarm init

```


Use the following script [generate_fog_rest_vm.sh](./src/utils/generate_fog_rest_vm.sh) to deploy the components in the VM



### Compute Nodes configuations

The compute nodes have to be connected to the VM as they need to have access to the images and YAKS
You can follow the installation from [install_fos_lxd.sh](./install_fos_lxd.sh)

And then modify the file `/etc/fos/agent/` by replacing the address for the YAKS server

```
...
"yaks": "tcp/<address of vm>:7887",
...
```

