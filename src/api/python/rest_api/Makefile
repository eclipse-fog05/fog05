all: echo "Nothing to do..."


clean:
	rm -rf build dist fog05rest.egg-info

install:
	python setup.py install
	rm -rf build dist fog05rest.egg-info

uninstall:
	pip uninstall fog05rest -y

package:
	python setup.py sdist bdist_wheel