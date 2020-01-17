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


Once `opam` is installed you need to install the following some packages verify the OCaml version, and if needed downgrade to 4.07.1


```
sudo apt install jq libev-dev libssl-dev python3 python3-dev python3-pip m4 pkg-config rsync unzip bubblewrap cmake -y
sudo pip3 install pyangbind
$ opam switch
#  switch    compiler                       description
→  defaut    ocaml-base-compiler.4.09.0     defaut
$ opam switch create fos ocaml-base-compiler.4.07.1
....

```

Then you need to install some required libraries from opam

```
opam install atdgen ocp-ocamlres conf-libev
```

And other requirements not present in opam:

- apero-core (https://github.com/atolab/apero-core)
- apero-net (https://github.com/atolab/apero-net)
- apero-time (https://github.com/atolab/apero-time)
- zenoh (https://github.com/atolab/zenoh)
- yaks-common (https://github.com/atolab/zenoh)
- yaks-ocaml (https://github.com/atolab/yaks-ocaml)

To install these you can execute the following commands:

```
$ mkdir fos_build
$ cd fos_build
$ git clone https://github.com/atolab/apero-core
$ cd apero-core
$ git checkout c36dee5
$ opam install . --working-dir -y
$ cd ..
$ git clone  https://github.com/atolab/apero-net
$ cd apero-net
$ git checkout 824c954
$ opam install . --working-dir -y
$ cd ..
$ git clone https://github.com/atolab/apero-time
$ cd apero-time
$ git checkout b0446b7
$ opam install . --working-dir -y
$ cd ..
$ git clone https://github.com/atolab/zenoh
$ cd zenoh
$ git checkout 46d4378
$ opam install . --working-dir -y
$ cd ..
$ git clone https://github.com/atolab/yaks-common
$ cd yaks-common
$ git checkout 5d2e70d
$ opam install . --working-dir -y
$ cd ..
$ git clone https://github.com/atolab/yaks-ocaml
$ cd yaks-ocaml
$ git checkout d076645
$ opam install . --working-dir -y
$ cd ..
$ git clone http://github.com/atolab/zenoh-c
$ cd zenoh-c
$ git checkout 1e20bb6
$ make
$ sudo make install
$ cd ..
$ git clone http://github.com/atolab/zenoh-python
$ cd zenoh-python
$ git checkout 1ced877
$ sudo python3 setup.py install
$ cd ..
$ git clone http://github.com/atolab/yaks-python
$ cd yaks-python
$ git checkout 50c9fc7
$ sudo make install
```

### Eclipse fog05 Agent

Then you can use the Eclipse fog05 makefile to build the agent

```
$ cd fog05
$ make submodules
$ make
....
dune build
make[1]: Leaving directory '/home/debian/fog05/src/agent'
$
```

