all: echo "Nothing to do..."


clean:
	rm -rf build dist fog05mm1.egg-info
	rm -rf .tox

install:
	python setup.py install
	rm -rf build dist fog05mm1.egg-info

uninstall:
	pip uninstall fog05mm1 -y

package:
	python setup.py sdist bdist_wheel

test:
	rm -rf .tox
	tox