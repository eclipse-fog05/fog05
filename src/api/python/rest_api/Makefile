all: echo "Nothing to do..."


clean:
	rm -rf build dist fog05rest.egg-info
	rm -rf build dist fog05rest.egg-info

install3:
	python3 setup.py install
	rm -rf build dist fog05rest.egg-info

install:
	python setup.py install
	rm -rf build dist fog05rest.egg-info

uninstall:
	pip uninstall fog05rest -y

uninstall3:
	pip3 uninstall fog05rest -y

package:
	python setup.py sdist bdist_wheel

package3:
	python3 setup.py sdist bdist_wheel