#!/bin/bash

VER_APERO="0.4.6"
VER_ZENOH="0.3.0"
VER_YAKS="0.3.0"

echo "[BUILD] Installing opam dependencies"
opam install dune.1.11.4 atdgen.2.0.0 conf-libev ocp-ocamlres -y

echo "[BUILD] Building and installing dependencies"
# install dependencies
mkdir fos_build
cd fos_build
git clone https://github.com/atolab/apero-core
cd apero-core
git checkout $VER_APERO
opam install . --working-dir -y
cd ..
git clone  https://github.com/atolab/apero-net
cd apero-net
git checkout $VER_APERO
opam install . --working-dir -y
cd ..
git clone https://github.com/atolab/apero-time
cd apero-time
git checkout $VER_APERO
opam install . --working-dir -y
cd ..
git clone https://github.com/atolab/zenoh
cd zenoh
git checkout $VER_ZENOH
opam install . --working-dir -y
cd ..
git clone https://github.com/atolab/yaks-common
cd yaks-common
git checkout $VER_YAKS
opam install . --working-dir -y
cd ..
git clone https://github.com/atolab/yaks-ocaml
cd yaks-ocaml
git checkout $VER_YAKS
opam install . --working-dir -y
cd ..
git clone http://github.com/atolab/yaks
cd yaks
git checkout $VER_YAKS
rm -rf src/yaks-be/yaks-be-influxdb/ src/yaks-be/yaks-be-sql/
make
cd ..
git clone http://github.com/atolab/zenoh-c
cd zenoh-c
git checkout $VER_ZENOH
make
sudo make install
cd ..
git clone http://github.com/atolab/zenoh-python
cd zenoh-python
git checkout $VER_ZENOH
sudo python3 setup.py install
cd ..
git clone http://github.com/atolab/yaks-python
cd yaks-python
git checkout $VER_YAKS
sudo  make install
cd ..
mkdir zenohd
cp zenoh/Makefile zenohd/
cp zenoh/zenoh-router-daemon.opam zenohd/
cp -r zenoh/src/zenoh-router-daemon zenohd/
echo -e "(lang dune 1.11.1)\n(name zenohd)" > zenohd/dune-project
sed -i 's/zenoh_proto/zenoh-proto/g' zenohd/zenoh-router-daemon/dune
sed -i 's/zenoh_tx_inet/zenoh-tx-inet/g' zenohd/zenoh-router-daemon/dune
sed -i 's/zenoh_router/zenoh-router/g' zenohd/zenoh-router-daemon/dune
cd zenohd
make
cd ../..

echo "[BUILD] Building Fog05"
# build fog05
git submodule update --init --recursive
make