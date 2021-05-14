
#!/bin/bash

set -e

case "$ARCH" in
    amd64)
        # crearting output directory
        mkdir -p ./debs/amd64;

        IMAGE="fog05/ubuntu-build:amd64"
        docker pull ${IMAGE}
        docker run -it -d --name build-fos-amd64 ${IMAGE} bash

        # install rust
        docker exec -u root build-fos-amd64 bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain nightly -y'

        # installing cargo deb
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cargo install cargo-deb'

        # cloning repos inside container
        docker exec -u root build-fos-amd64 bash -c "cd /root && git clone https://github.com/eclipse-zenoh/zenoh"
        docker exec -u root build-fos-amd64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05"
        docker exec -u root build-fos-amd64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-networking-linux"
        docker exec -u root build-fos-amd64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-native"
        docker exec -u root build-fos-amd64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-ros2"

        # build zenohd and zenoh-plugin-storages
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'

        # generate debian packages for zenohd and zenoh-plugin-storages
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo deb --target=x86_64-unknown-linux-gnu -p zenoh --no-build'
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo deb --target=x86_64-unknown-linux-gnu  -p zenoh-plugin-storages --no-build'

        # copy-out generated debian files
        docker cp  'build-fos-amd64:/root/zenoh/target/x86_64-unknown-linux-gnu/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/amd64

        # build agent and fosctl
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo update && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'

        # generate debian packages for fosctl and agent
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=x86_64-unknown-linux-gnu -p fog05-agent --no-build'
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=x86_64-unknown-linux-gnu  -p fog05-fosctl --no-build'

        # copy-out generated debian files
        docker cp  'build-fos-amd64:/root/fog05/target/x86_64-unknown-linux-gnu/debian' /tmp
        mv /tmp/debian/*.deb ./debs/amd64

        # build linux networking plugin
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'

        # generate debian packages for fog05-newtworking-linux
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && cargo deb --target=x86_64-unknown-linux-gnu --no-build'

        # copy-out generated debian files
        docker cp  'build-fos-amd64:/root/fog05-networking-linux/target/x86_64-unknown-linux-gnu/debian' /tmp
        mv /tmp/debian/*.deb ./debs/amd64


        # build native plugin
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'

        # generate debian packages for fog05-hypervisor-native
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo deb --target=x86_64-unknown-linux-gnu --no-build'

        # copy-out generated debian files
        docker cp  'build-fos-amd64:/root/fog05-hypervisor-native/target/x86_64-unknown-linux-gnu/debian' /tmp
        mv /tmp/debian/*.deb ./debs/amd64

        # build ros2 plugin
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo build --target=x86_64-unknown-linux-gnu --release --all-targets'

        # generate debian packages for fog05-hypervisor-ros2
        docker exec -u root build-fos-amd64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo deb --target=x86_64-unknown-linux-gnu --no-build'

        # copy-out generated debian files
        docker cp  'build-fos-amd64:/root/fog05-hypervisor-ros2/target/x86_64-unknown-linux-gnu/debian' /tmp
        mv /tmp/debian/*.deb ./debs/amd64

        ;;
    arm64)

        mkdir -p ./debs/arm64;

        IMAGE="fog05/ubuntu-build:arm64"
        docker pull ${IMAGE}
        docker run -it -d --name build-fos-arm64 ${IMAGE} bash

        docker exec -u root build-fos-arm64 bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain nightly -y'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && rustup target add aarch64-unknown-linux-gnu'

        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cargo install cargo-deb'

        # configuring cargo
        docker exec -u root build-fos-arm64 bash -c 'echo [target.aarch64-unknown-linux-gnu] >> ${HOME}/.cargo/config'
        docker exec -u root build-fos-arm64 bash -c 'echo linker = \"aarch64-linux-gnu-gcc\" >> ${HOME}/.cargo/config'
        docker exec -u root build-fos-arm64 bash -c 'echo strip = { path = \"aarch64-linux-gnu-strip\" } >> ${HOME}/.cargo/config'
        docker exec -u root build-fos-arm64 bash -c 'echo objcopy = { path = \"aarch64-linux-gnu-objcopy\" } >> ${HOME}/.cargo/config'

        docker exec -u root build-fos-arm64 bash -c "cd /root && git clone https://github.com/eclipse-zenoh/zenoh"
        docker exec -u root build-fos-arm64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05"
        docker exec -u root build-fos-arm64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-networking-linux"
        docker exec -u root build-fos-arm64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-native"
        docker exec -u root build-fos-arm64 bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-ros2"

        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && rustup target add aarch64-unknown-linux-gnu'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo deb --target=aarch64-unknown-linux-gnu -p zenoh --no-build'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo deb --target=aarch64-unknown-linux-gnu  -p zenoh-plugin-storages --no-build'
        docker cp  'build-fos-arm64:/root/zenoh/target/aarch64-unknown-linux-gnu/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/arm64


        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo update && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=aarch64-unknown-linux-gnu -p fog05-agent --no-build'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=aarch64-unknown-linux-gnu  -p fog05-fosctl --no-build'
        docker cp  'build-fos-arm64:/root/fog05/target/aarch64-unknown-linux-gnu/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/arm64

        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && cargo update && PKG_CONFIG_PATH=/usr/lib/aarch64-linux-gnu/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/aarch64-linux-gnu/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo deb --target=aarch64-unknown-linux-gnu --no-build'
        docker cp  'build-fos-arm64:/root/fog05-networking-linux/target/aarch64-unknown-linux-gnu/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/arm64

        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo update && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo deb --target=aarch64-unknown-linux-gnu --no-build'
        docker cp  'build-fos-arm64:/root/fog05-hypervisor-native/target/aarch64-unknown-linux-gnu/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/arm64

        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo update && cargo build --target=aarch64-unknown-linux-gnu --release --all-targets'
        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo deb --target=aarch64-unknown-linux-gnu --no-build'
        docker cp  'build-fos-arm64:/root/fog05-hypervisor-ros2/target/aarch64-unknown-linux-gnu/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/arm64
        ;;
    armhf)

        mkdir -p ./debs/armhf

        IMAGE="fog05/ubuntu-build:armhf"
        docker pull ${IMAGE}
        docker run -it -d --name build-fos-armhf ${IMAGE} bash

        docker exec -u root build-fos-armhf bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain nightly -y'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && rustup target add armv7-unknown-linux-gnueabihf'

        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cargo install cargo-deb'

        docker exec -u root build-fos-armhf bash -c 'echo [target.armv7-unknown-linux-gnueabihf] >> ${HOME}/.cargo/config'
        docker exec -u root build-fos-armhf bash -c 'linker = \"arm-linux-gnueabihf-gcc\" >> ${HOME}/.cargo/config'
        docker exec -u root build-fos-armhf bash -c 'strip = { path = \"arm-linux-gnueabihf-strip\" } >> ${HOME}/.cargo/config'
        docker exec -u root build-fos-armhf bash -c 'objcopy = { path = \"arm-linux-gnueabihf-objcopy\" } >> ${HOME}/.cargo/config'

        docker exec -u root build-fos-armhf bash -c "cd /root && git clone https://github.com/eclipse-zenoh/zenoh"
        docker exec -u root build-fos-armhf bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05"
        docker exec -u root build-fos-armhf bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-networking-linux"
        docker exec -u root build-fos-armhf bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-native"
        docker exec -u root build-fos-armhf bash -c "cd /root && git clone https://github.com/eclipse-fog05/fog05-hypervisor-ros2"

        docker exec -u root build-fos-arm64 bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && rustup target add armv7-unknown-linux-gnueabihf'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo deb --target=armv7-unknown-linux-gnueabihf -p zenoh --no-build'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/zenoh/ && cargo deb --target=armv7-unknown-linux-gnueabihf  -p zenoh-plugin-storages --no-build'
        docker cp  'build-fos-armhf:/root/zenoh/target/armv7-unknown-linux-gnueabihf/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/armhf

        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=armv7-unknown-linux-gnueabihf -p fog05-agent --no-build'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05/ && cargo deb --target=armv7-unknown-linux-gnueabihf  -p fog05-fosctl --no-build'
        docker cp  'build-fos-armhf:/root/fog05/target/armv7-unknown-linux-gnueabihf/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/armhf

        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-networking-linux/ && PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig PKG_CONFIG_ALLOW_CROSS=1 cargo deb --target=armv7-unknown-linux-gnueabihf --no-build'
        docker cp  'build-fos-armhf:/root/fog05-networking-linux/target/armv7-unknown-linux-gnueabihf/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/armhf

        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-native/ && cargo deb --target=armv7-unknown-linux-gnueabihf --no-build'
        docker cp  'build-fos-armhf:/root/fog05-hypervisor-native/target/armv7-unknown-linux-gnueabihf/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/armhf

        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets'
        docker exec -u root build-fos-armhf bash -c 'source ${HOME}/.cargo/env && cd /root/fog05-hypervisor-ros2/ && cargo deb --target=armv7-unknown-linux-gnueabihf --no-build'
        docker cp  'build-fos-armhf:/root/fog05-hypervisor-ros2/target/armv7-unknown-linux-gnueabihf/debian' /tmp/
        mv /tmp/debian/*.deb ./debs/armhf
        ;;
    *)
    printf "Unrecognized architecture $ARCH\n"
    exit 1
    ;;
esac

echo 'Done!'
