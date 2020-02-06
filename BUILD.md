# Eclipse fog05 build instructions

This document describes the steps needed in order to build Eclipse fog05 in your machine. This was tested on Debian Buster (kernel version 4.19.67-2+deb10u1)

Eclipse fog05 is composed by different components:

- SDK
- agent
- APIs
- Plugin

In order to build everything you need to start by the SDK

### Build Eclipse fog05 Prerequisites

The Eclipse fog05 SDK is written in OCaml, it support version 4.07.1, we recomend to not use the OCaml version provided by your distribution package system but instead to install
it using `opam`, please follow this link for installation instructions [opam installation](https://opam.ocaml.org/doc/Install.html).


Once `opam` is installed you need to install the following some packages verify the OCaml version, it should be 4.09.0


```
sudo apt install jq libev-dev libssl-dev python3 python3-dev python3-pip m4 pkg-config rsync unzip bubblewrap cmake -y
sudo pip3 install pyangbind
$ opam switch
#  switch    compiler                       description
→  defaut    ocaml-base-compiler.4.09.0     defaut
....

```

Then you need to install some required libraries from opam and others that need to be built locally:

- apero-core (https://github.com/atolab/apero-core)
- apero-net (https://github.com/atolab/apero-net)
- apero-time (https://github.com/atolab/apero-time)
- zenoh (https://github.com/atolab/zenoh)
- yaks-common (https://github.com/atolab/zenoh)
- yaks-ocaml (https://github.com/atolab/yaks-ocaml)

To install all of these you have to execute the [build.sh](build.sh) script:

```
$ ./build.sh
```

### Eclipse fog05 Agent

Then you can use the Eclipse fog05 makefile to build the agent

```
$ cd fog05
$ git submodule update --init --recursive
$ make
....
dune build
make[1]: Leaving directory '/home/debian/fog05/src/agent'
$
```

