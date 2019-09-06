#!/usr/bin/env bash


# INSTALL SNAPD - LXD - DOCKER
# CREATE MEAO/YAKS container (DOCKER)
# CREATE TEST MEC Container (LXD)

# docker swarm init --advertise-addr 192.168.100.134

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -t|--test)
    TEST=true
    shift;;
    -b|--build)
    BUILD=false
    shift;;
    *)
    POSITIONAL+=("$1")
    shift
    ;;
esac
done

docker image rm fog05/yaks --force
docker image rm fog05/meao --force


if [ $BUILD ]; then
    make -C ocaml/mec_meao_mepmv clean
    make -C ocaml/mec_meao_mepmv
else
    mkdir -p ocaml/mec_meao_mepmv/_build/default/meao
    curl -L -o /tmp/meao.tar.gz https://www.dropbox.com/s/91fw8iromfz3su6/meao.tar.gz
    tar -xzvf /tmp/meao.tar.gz -C ocaml/mec_meao_mepmv/_build/default/meao
    rm -rf /tmp/meao.tar.gz
fi



docker network rm fog05-meaonet
docker network create -d overlay --attachable fog05-meaonet


sg docker -c "docker build . -f ./docker/Dockerfile-yaks -t fog05/yaks --no-cache"
sg docker -c "docker build . -f ./docker/Dockerfile-meao -t fog05/meao --no-cache"

docker stack deploy -c ./docker/meao/docker-compose.yaml meao


if [ $TEST ]; then
    if [ $BUILD ]; then
        make -C ocaml/mec_platform clean
        make -C ocaml/mec_platform
    else
        mkdir -p ocaml/mec_platform/_build/default/me_platform
        curl -L -o /tmp/mecp.tar.gz https://www.dropbox.com/s/gx32gnr1y4gcm2w/mecp.tar.gz
        tar -xzvf /tmp/mecp.tar.gz -C ocaml/mec_platform/_build/default/me_platform
        rm -rf /tmp/mecp.tar.gz
    fi
    ./generate_mec_platform.sh
    MEC_IP=$(lxc list -c4 --format json plat |  jq -r '.[0].state.network.eth0.addresses[0].address')
    PL="{\"platformId\":\"testp\", \"endpoint\":{\"uris\":[\"/exampleAPI/mm5/v1\"], \"alternative\":{},\"addresses\":[{\"host\":\"$MEC_IP\",\"port\":8091}]}}"
    curl -X POST http://127.0.1:8071/exampleAPI/mm1/v1/platforms -d "$PL"
fi


sleep 5

docker stack deploy -c docker/meao/docker-compose.yaml meao



# lxc launch images:ubuntu/bionic meao
# sleep 3;

# lxc exec meao -- sudo apt update -qq
# lxc exec meao -- sudo apt install curl -y
# lxc exec meao -- sudo useradd -m mec
# lxc exec meao -- usermod -aG sudo mec
# lxc exec meao -- echo "mec      ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers > /dev/null
# lxc exec meao -- mkdir -p /etc/fos/utils/mec
# lxc exec meao -- mkdir -p /etc/fos/utils/
# lxc exec meao -- curl -L -o /tmp/yaks.tar.gz https://www.dropbox.com/s/g4tnzvjwlx3zcr2/yaksd.tar.gz
# lxc exec meao -- tar -xzvf /tmp/yaks.tar.gz -C /etc/fos
# lxc exec meao -- rm -rf /tmp/yaks.tar.gz
# lxc file push ./ocaml/mec_meao_mepmv/_build/default/meao/meao.exe meao/etc/fos/utils/meao
# lxc exec meao -- sudo chown mec:mec -R /etc/fos

# lxc file push ../../etc/yaks.service meao/lib/systemd/system/
# lxc file push ../../etc/yaks.target meao/lib/systemd/system/
# lxc file push ./ocaml/mec_meao_mepmv/etc/mec_meao.service meao/lib/systemd/system/
# lxc exec meao -- sudo apt install libev-dev libssl-dev nginx -y

# lxc file push ./ocaml/mec_meao_mepmv/etc/nginx meao/etc/nginx/sites-available/default
# lxc file push ./ocaml/mec_meao_mepmv/etc/ip_replace.sh meao/tmp/

# lxc exec meao --  /tmp/ip_replace.sh

# lxc exec meao -- systemctl stop nginx

# lxc exec meao -- systemctl daemon-reload
# lxc exec meao -- systemctl enable nginx
# lxc exec meao -- systemctl enable yaks
# lxc exec meao -- systemctl enable mec_meao

# lxc exec meao -- systemctl start nginx
# lxc exec meao -- systemctl start yaks
# lxc exec meao -- systemctl start mec_meao

# # lxc list -c4 --format json plat

# MEAOIP=$(lxc list -c4 --format csv meao | cut -d' ' -f1)

# sudo iptables -t nat -A PREROUTING -i lo -p tcp --dport 8071 -j DNAT --to $MEAOIP:8071

# echo "export MEAO=127.0.0.1:8071/exampleAPI/mm1/v1" >> ~/.profile

# export MEAO="127.0.0.1:8071/exampleAPI/mm1/v1"