all: echo "Nothing to do..."


clean:
	rm -rf build dist fog05mm5.egg-info
	rm -rf .tox

install:
	python setup.py install
	rm -rf build dist fog05mm5.egg-info

uninstall:
	pip uninstall fog05mm5 -y

test:
	rm -rf .tox
	tox