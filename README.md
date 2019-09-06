# fog05 Deployment Guide for 5GCity

The Eclipse fog05 ExtendedEdge-VIM has to be deployed following this instructions.

It is divided in two main components

- REST API Server + Image Server + YAKS
- Compute Portion (Agent, LinuxPlugin, LinuxBridge Plugin, LXD Plugin)


The first components as to be deployed in a VM with the following specifications:

- 1 vCPU
- 1 GB RAM
- 40 GB Disk (or less this really depends in the space needed for the images)
- Ubuntu 16.04
- docker


### VM Configuration

Install docker-ce [Following these instructions](https://www.google.com)


