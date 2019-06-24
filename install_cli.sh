#!/usr/bin/env bash

# git clone https://github.com/eclipse/fog05
# cd fog05
# git checkout 0.2-devel




MACHINE_TYPE=`uname -m`




sudo apt update -qq
sudo apt install libev4 libev-dev libssl1.0.0 curl -y

if [ ${MACHINE_TYPE} == 'x86_64' ]; then
    curl -L -o /tmp/cli.tar.gz https://www.dropbox.com/s/8g1500udh8zsod7/cli.tar.gz
elif [ ${MACHINE_TYPE} == 'armv7l' ]; then
    curl -L -o /tmp/cli.tar.gz https://www.dropbox.com/s/6vg7lcwhco46tdz/cli.tar.gz
elif [ ${MACHINE_TYPE} == 'aarch64' ]; then
    curl -L -o /tmp/cli.tar.gz https://www.dropbox.com/s/gf0l1ry8hwelrn3/cli.tar.gz
fi



tar -xzvf /tmp/cli.tar.gz -C /tmp
sudo mv /tmp/fos_cli_ng.exe /usr/local/bin/fos
rm -rf  /tmp/cli.tar.gz /tmp/fos_cli_ng.exe

echo 'Add FOS_YAKS_ENDPOINT to your enviroment before using the CLI'



