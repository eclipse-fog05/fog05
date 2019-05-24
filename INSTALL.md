# Eclipse fog05 - f0rce installation.

!!! THESE INSTRUCTIONS ARE STILL IN ALPHA !!!

In the first branch there are two python packages: ykon and f0rce.
These packages require python3.4 or above.

The first step is to install the ykon package.

$ cd ykon
$ python3 setup.py install

The second step is to install the f0rce package, which requires the ykon
package.

$ cd ../f0rce/base
$ python3 setup.py install
