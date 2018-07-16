# -*-Makefile-*-

WD := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))));

all:

	cd ./tmp; git clone https://github.com/atolab/python-cdds; cd python-cdds; ./configure; sudo python3 setup.py install --record cdds_files.txt;

	cd ./tmp; git clone https://github.com/atolab/python-dstore; cd python-dstore; sudo python3 setup.py install --record dstore_files.txt;

	pip3 install python-daemon psutil netifaces jinja2 flask websockets

	#cd ./client; atdgen -t types/*.atd; atdgen -j types/*.atd; atdgen -v types/*.atd; jbuilder build;  cp ./_build/default/bin/fos.exe ./fos;


#cli-ng:
#	cd ./client; atdgen -t types/*.atd; atdgen -j types/*.atd; atdgen -v types/*.atd; jbuilder build;  cp ./_build/default/bin/fos.exe ./fos;

install:
#	sudo cp ./client/fos /usr/local/bin/fos-ng
#	sudo cp ./client/bin/check_pid.sh /usr/local/bin/fos-check-pid
	sudo python3 setup.py install --record fog05_files.txt


clean:
	cd ./tmp/python-cdds; sudo rm -rf ./dist ./build python-cdds.egg-info;
	cd ./tmp/python-dstore; sudo rm -rf ./dist ./build python-dstore.egg-info;
#	cd ./client; jbuilder clean; 	rm -rf fos; rm -rf types/types*.ml types/types*.mli;
	sudo rm -rf ./build ./disk ./fog05.egg-info;