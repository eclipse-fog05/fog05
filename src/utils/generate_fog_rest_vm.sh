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

if [ $BUILD ]; then
    sg docker -c "docker build . -f ./docker/Dockerfile-yaks -t fog05/yaks --no-cache"
    sg docker -c "docker build . -f ./docker/Dockerfile-fog05-rest -t fog05/rest --no-cache"

else
    docker image pull fog05/rest
    docker image pull fog05/yaks
fi
docker network rm fog05-restnet
docker network create -d overlay --attachable fog05-restnet



sleep 5

docker stack deploy -c ./docker/vm/docker-compose.yaml fog05rest




