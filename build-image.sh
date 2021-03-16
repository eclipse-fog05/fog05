
#!/bin/bash

docker image rm fog05/ubuntu-build:focal

set -e

sg docker -c "docker build ./docker -f ./docker/Dockerfile -t fog05/ubuntu-build:focal --no-cache" --oom-kill-disable