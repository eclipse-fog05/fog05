============
Installation
============

In order to run install Eclipse fog05 FIMAPI you need to install ``zenoh-c``, ``zenoh-python`` and ``yaks-python``
you can get those from GitHub::

    git clone github.com/atolab/zenoh-c
    cd zenoh-c
    git checkout 58bad2cf1616f405fe401b22a713b95a6fef786c
    make
    sudo make install
    cd ..
    git clone github.com/atolab/zenoh-python
    cd zenoh-python
    git checkout 1ced877917816acea13e58c151e02cf950ad8009
    sudo python3 setup.py install
    cd ..
    git clone github.com/atolab/yaks-python
    cd yaks-python
    git checkout 50c9fc7d022636433709340f220e7b58cd74cefc
    sudo make install


Once you have those dependecies installed you can install the API::

    pip3 install pyangbind pyang
    git clone github.com/eclipse/fog05
    make -C src/im/python
    make -C src/im/python install
    make -C src/api/python/api install

