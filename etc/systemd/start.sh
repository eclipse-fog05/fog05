#!/usr/bin/env bash

sudo systemctl start yaks
sudo systemctl start fos_agent
sudo systemctl start fos_linux
sudo systemctl start fos_linuxbridge
sudo systemctl start fos_lxd