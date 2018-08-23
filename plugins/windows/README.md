Windows os plugin

This plugin allow fog05 to run on top of windows

supported operation:
- execute command
- check that file exists
- save on file
- read from file
- get hw information (cp,ram,network,disks)
- get uuid from motherboard
- get hostname
- send signal
- check if a pid exists


todo:

- get detailed i/o informations
- get hw accelerators informations
- get pid from process name
- get monitoring information about network
- get gps information about node
- install packages
- remove packages

---


python dependencies:

- psutil
- netifaces

-- 

config dependencies:

- user should be able to use sudo without password asking (`echo "username  ALL=(ALL) NOPASSWD: ALL"  >> /etc/sudoers`)

