all: echo "Nothing to do..."


clean:
	rm -rf build dist fog05.egg-info
	make -C docs clean

install:
	python3 setup.py install
	rm -rf build dist fog05.egg-info

uninstall:
	pip3 uninstall fog05 -y

doc:
	make -C docs html