#!/usr/bin/env bash

# git clone https://github.com/eclipse/fog05
# cd fog05
# git checkout 0.2-devel




MACHINE_TYPE=`uname -m`




sudo apt update -qq
sudo apt install libev4 libev-dev libssl1.0.0 python3-pip python3-dev curl jq -y
sudo pip3 install jsonschema

mkdir -p src/agent/_build/default/fos-agent

if [ ${MACHINE_TYPE} == 'x86_64' ]; then
    curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/y7hvr7j79ibc4pk/fos.tar.gz
elif [ ${MACHINE_TYPE} == 'armv7l' ]; then
    curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/uziduncc4v35zj9/fos.tar.gz
elif [ ${MACHINE_TYPE} == 'aarch64' ]; then
    curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/kcz3pvirb2xmh40/fos.tar.gz
fi



tar -xzvf /tmp/fos.tar.gz -C src/agent/_build/default/fos-agent
rm -rf /tmp/fos.tar.gz

sudo make install

sudo sh -c "cat /etc/machine-id | xargs -i  jq  '.configuration.nodeid = \"{}\"' /etc/fos/plugins/linux/linux_plugin.json > /tmp/linux_plugin.tmp && mv /tmp/linux_plugin.tmp /etc/fos/plugins/linux/linux_plugin.json"

