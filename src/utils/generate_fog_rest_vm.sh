#!/usr/bin/env bash


# INSTALL - DOCKER
# CREATE REST/YAKS container (DOCKER)


# docker swarm init --advertise-addr 192.168.100.134

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -b|--build)
    BUILD=false
    shift;;
    *)
    POSITIONAL+=("$1")
    shift
    ;;
esac
done

docker image pull fog05/yaks:5gcity

if [ $BUILD ]; then
    sg docker -c "docker build . -f ./docker/Dockerfile-fog05-rest -t fog05/rest:5gcity --no-cache"

else
    docker image pull fog05/rest:5gcity

fi
docker network rm fog05-restnet
docker network create -d overlay --attachable fog05-restnet



sleep 5

docker stack deploy -c ./docker/vm/docker-compose.yaml fog05rest




