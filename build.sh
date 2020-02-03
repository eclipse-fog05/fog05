#!/bin/bash

VER_APERO="0.4.6"
VER_ZENOH="0.3.0"
VER_YAKS="0.3.0"

echo "[BUILD] Installing dependencies"
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
git clone http://github.com/atolab/zenoh-c
cd zenoh-c
git checkout $VER_ZENOH
make
make install
cd ..
git clone http://github.com/atolab/zenoh-python
cd zenoh-python
git checkout $VER_ZENOH
python3 setup.py install
cd ..
git clone http://github.com/atolab/yaks-python
cd yaks-python
git checkout $VER_YAKS
make install

echo "[BUILD] Building Fog05"
# build fog05
cd ../..
git submodule update --init --recursive
make