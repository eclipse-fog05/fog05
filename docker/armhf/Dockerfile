FROM ubuntu:bionic

LABEL authors="Gabriele Baldoni"

COPY etc/sources.list /etc/apt/sources.list
COPY etc/arm-cross-compile-sources.list /etc/apt/sources.list.d/arm-cross-compile-sources.list


RUN DEBIAN_FRONTEND=noninteractive dpkg --add-architecture armhf

RUN DEBIAN_FRONTEND=noninteractive apt update && \
	DEBIAN_FRONTEND=noninteractive apt install git build-essential devscripts debhelper pkg-config dpkg-dev crossbuild-essential-armhf pkg-config-arm-linux-gnueabihf libnftnl-dev:armhf libnfnetlink-dev:armhf libmnl-dev:armhf -y


COPY bin/uid_entrypoint /bin/uid_entrypoint
RUN mkdir -p /home/jenkins
RUN chgrp -R 0 /home/
RUN chmod -R g=u /home/
RUN chmod g=u /etc/passwd
RUN ["chmod", "+x", "/bin/uid_entrypoint"]
ENTRYPOINT [ "/bin/uid_entrypoint" ]
USER 1001

CMD /usr/bin/bash