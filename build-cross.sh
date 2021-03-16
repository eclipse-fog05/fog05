
#!/bin/bash

docker image rm fog05/ubuntu-build:focal

set -e



IMAGE="fog05/ubuntu-build:focal"
DEBIAN="debian:10-slim"

docker pull ${IMAGE}
docker run -it -d --name build-fos ${IMAGE} bash

# install rust
docker exec build-fos bash -c "curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain nightly -y"

# installing rust targets
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && rustup target add aarch64-unknown-linux-gnu && rustup target add armv7-unknown-linux-gnueabihf'

# installing cargo deb
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cargo install cargo-deb'

# configuring cargo
docker exec build-fos sh 'echo [target.aarch64-unknown-linux-gnu] >> ${HOME}/.cargo/config'
docker exec build-fos sh 'echo linker = "aarch64-linux-gnu-gcc" >> ${HOME}/.cargo/config'
docker exec build-fos sh 'echo strip = { path = "aarch64-linux-gnu-strip" } >> ${HOME}/.cargo/config'
docker exec build-fos sh 'echo objcopy = { path = "aarch64-linux-gnu-objcopy" } >> ${HOME}/.cargo/config'

docker exec build-fos sh 'echo [target.armv7-unknown-linux-gnueabihf] >> ${HOME}/.cargo/config'
docker exec build-fos sh 'linker = "arm-linux-gnueabihf-gcc" >> ${HOME}/.cargo/config'
docker exec build-fos sh 'strip = { path = "arm-linux-gnueabihf-strip" } >> ${HOME}/.cargo/config'
docker exec build-fos sh 'objcopy = { path = "arm-linux-gnueabihf-objcopy" } >> ${HOME}/.cargo/config'

# cloning repos inside container

docker exec build-fos bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05"
docker exec build-fos bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-networking-linux"
docker exec build-fos bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-native"
docker exec build-fos bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-ros2"


# creating output directories
mkdir -p ./debs/arm64; mkdir -p ./debs/amd64; mkdir -p ./debs/armhf

# build agent and fosctl
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'

# generate debian packages for fosctl and agent

docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=x86_64-unknown-linux-gnu -p fog05-agent --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=x86_64-unknown-linux-gnu  -p fog05-fosctl --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=aarch64-unknown-linux-gnu -p fog05-agent --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=aarch64-unknown-linux-gnu  -p fog05-fosctl --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=armv7-unknown-linux-gnueabihf -p fog05-agent --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=armv7-unknown-linux-gnueabihf  -p fog05-fosctl --no-build'

# copy-out generated debian files
docker cp 'build-fos:/root/fog05/target/x86_64-unknown-linux-gnu/debian/*.deb' ./debs/amd64
docker cp 'build-fos:/root/fog05/target/aarch64-unknown-linux-gnu/debian/*.deb' ./debs/arm64
docker cp 'build-fos:/root/fog05/target/armv7-unknown-linux-gnueabihf/debian/*.deb' ./debs/armhf

# build linux networking plugin
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/aarch64-linux-gnu/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'

# generate debian packages for fog05-newtworking-linux
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && cargo deb --target=x86_64-unknown-linux-gnu --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/aarch64-linux-gnu/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo deb --target=aarch64-unknown-linux-gnu --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo deb --target=armv7-unknown-linux-gnueabihf --no-build'


# copy-out generated debian files
docker cp 'build-fos:/root/fog05-networking-linux/target/x86_64-unknown-linux-gnu/debian/*.deb' ./debs/amd64
docker cp 'build-fos:/root/fog05-networking-linux/target/aarch64-unknown-linux-gnu/debian/*.deb' ./debs/arm64
docker cp 'build-fos:/root/fog05-networking-linux/target/armv7-unknown-linux-gnueabihf/debian/*.deb' ./debs/armhf

# build native plugin
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'

# generate debian packages for fog05-hypervisor-native
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo deb --target=x86_64-unknown-linux-gnu --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo deb --target=aarch64-unknown-linux-gnu --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo deb --target=armv7-unknown-linux-gnueabihf --no-build'


# copy-out generated debian files
docker cp 'build-fos:/root/fog05-hypervisor-native/target/x86_64-unknown-linux-gnu/debian/*.deb' ./debs/amd64
docker cp 'build-fos:/root/fog05-hypervisor-native/target/aarch64-unknown-linux-gnu/debian/*.deb' ./debs/arm64
docker cp 'build-fos:/root/fog05-hypervisor-native/target/armv7-unknown-linux-gnueabihf/debian/*.deb' ./debs/armhf


# build ros2 plugin
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'

# generate debian packages for fog05-hypervisor-ros2
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo deb --target=x86_64-unknown-linux-gnu --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo deb --target=aarch64-unknown-linux-gnu --no-build'
docker exec build-fos bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo deb --target=armv7-unknown-linux-gnueabihf --no-build'


# copy-out generated debian files
docker cp 'build-fos:/root/fog05-hypervisor-ros2/target/x86_64-unknown-linux-gnu/debian/*.deb' ./debs/amd64
docker cp 'build-fos:/root/fog05-hypervisor-ros2/target/aarch64-unknown-linux-gnu/debian/*.deb' ./debs/arm64
docker cp 'build-fos:/root/fog05-hypervisor-ros2/target/armv7-unknown-linux-gnueabihf/debian/*.deb' ./debs/armhf


echo 'Done!'
