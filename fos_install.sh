#!/usr/bin/env bash

git clone https://github.com/eclipse/fog05
cd fog05
git checkout 0.2-devel

sudo apt update -qq
sudo apt install libev4 libdev-dev libssl1.0.0 pyhton3-pip python3-dev -y
sudo pip3 install jsonschema

mkdir -p src/ocaml/_build/default/src/fos/fos-agent/
curl -L -o /tmp/fos.tar.gz https://www.dropbox.com/s/yxmcomji7pezq8h/fos.tar.gz
tar -xzvf /tmp/fos.tar.gz -C src/agent/_build/default/fos-agent
rm -rf /tmp/fos.tar.gz

sudo make install

echo 'Update the fog05 configuration file under /etc/fos/agent.json and /etc/fos/plugins/linux/linux_plugins.json'



