
#!/bin/bash


set -e

case "$ARCH" in
    amd64)
        sg docker -c "docker build ./docker/amd64 -f ./docker/amd64/Dockerfile -t fog05/ubuntu-build:amd64 --no-cache" --oom-kill-disable
        ;;
    arm64)
        sg docker -c "docker build ./docker/arm64 -f ./docker/arm64/Dockerfile -t fog05/ubuntu-build:arm64 --no-cache" --oom-kill-disable
        ;;
    armhf)
        sg docker -c "docker build ./docker/armhf -f ./docker/armhf/Dockerfile -t fog05/ubuntu-build:armhf --no-cache" --oom-kill-disable
        ;;
    *)
    printf "Unrecognized architecture $ARCH\n"
    exit 1
    ;;
esac

exit 0