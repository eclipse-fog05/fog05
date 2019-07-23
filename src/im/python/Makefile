# Copyright (c) 2018 ADLINK Technology Inc.
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - MEAO Yang models
#
#

# NOTE: pyang and pyangbind are required for build

PYANG:= pyang
PYBINDPLUGIN:=$(shell /usr/bin/env python3 -c \
	            'import pyangbind; import os; print("{}/plugin".format(os.path.dirname(pyangbind.__file__)))')

YANG_DESC_MODELS := user_fdu
YANG_RECORD_MODELS := infra_fdu

PYTHON_MODELS := $(addsuffix .py, $(YANG_DESC_MODELS))
PYTHON_RECORDS := $(addsuffix .py, $(YANG_RECORD_MODELS))

PYTHON_JSONSCHEMAS := $(addsuffix .jsonschema, $(YANG_DESC_MODELS))
YANG_DESC_TREES := $(addsuffix .tree.txt, $(YANG_DESC_MODELS))
YANG_DESC_JSTREES := $(addsuffix .html, $(YANG_DESC_MODELS))
YANG_RECORD_TREES := $(addsuffix .tree.txt, $(YANG_RECORD_MODELS))
YANG_RECORD_JSTREES := $(addsuffix .html, $(YANG_RECORD_MODELS))

OUT_DIR := fog05_im
TREES_DIR := fog05_im_trees
MODEL_DIR := yang/fos
RW_PB_EXT := build/yang/rw-pb-ext.yang
Q?=@

PYANG_OPTIONS := -Werror

all: $(PYTHON_MODELS) pyang-json-schema-plugin $(PYTHON_RECORDS) pyang-json-schema-plugin $(PYTHON_JSONSCHEMAS) clean-plugin pyang-json-schema-plugin $(PYTHON_JSONSCHEMAS) trees

trees: $(YANG_DESC_TREES) $(YANG_DESC_JSTREES) $(YANG_RECORD_TREES) $(YANG_RECORD_JSTREES)

$(OUT_DIR):
	$(Q)mkdir -p $(OUT_DIR)
	$(Q)touch $(OUT_DIR)/__init__.py

$(TREES_DIR):
	$(Q)mkdir -p $(TREES_DIR)

%.py: $(OUT_DIR) $(RW_PB_EXT)
	$(Q)echo generating $@ from $*.yang
	#$(Q)echo pyang $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) --plugindir $(PYBINDPLUGIN) -f pybind -o $(OUT_DIR)/$@ $(MODEL_DIR)/$*.yang
	$(Q)pyang $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) --plugindir $(PYBINDPLUGIN) -f pybind -o $(OUT_DIR)/$@ $(MODEL_DIR)/$*.yang

%.jsonschema: $(OUT_DIR) $(RW_PB_EXT) pyang-json-schema-plugin
	$(Q)echo generating $@ from $*.yang
	#$(Q)echo pyang  $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) --plugindir pyang-json-schema-plugin/jsonschema -f jsonschema $(MODEL_DIR)/$*.yang > $(OUT_DIR)/$@
	$(Q)pyang -Werror $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) --plugindir pyang-json-schema-plugin/jsonschema -f jsonschema $(MODEL_DIR)/$*.yang > $(OUT_DIR)/$@

%.tree.txt: $(TREES_DIR)
	$(Q)echo generating $@ from $*.yang
	$(Q)pyang $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) -f tree -o $(TREES_DIR)/$@ $(MODEL_DIR)/$*.yang

%.html: $(TREES_DIR)
	$(Q)echo generating $@ from $*.yang
	$(Q)pyang $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) -f jstree -o $(TREES_DIR)/$@ $(MODEL_DIR)/$*.yang
	# $(Q)sed -i 's|data\:image/gif\;base64,R0lGODlhS.*RCAA7|https://osm.etsi.org/images/OSM-logo.png\" width=\"175\" height=\"60|g' $(TREES_DIR)/$@
	# $(Q)sed -i 's|<a href=\"http://www.tail-f.com">|<a href="http://osm.etsi.org">|g' $(TREES_DIR)/$@

%.rec.tree.txt: $(TREES_DIR)
	$(Q)echo generating $@ from $*.yang
	$(Q)pyang $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) -f tree -o $(TREES_DIR)/$@ $(MODEL_DIR)/$*.yang
	$(Q)mv $(TREES_DIR)/$@ $(TREES_DIR)/$*.tree.txt

%.rec.html: $(TREES_DIR)
	$(Q)echo generating $@ from $*.yang
	$(Q)pyang $(PYANG_OPTIONS) --path build/yang --path $(MODEL_DIR) -f jstree -o $(TREES_DIR)/$@ $(MODEL_DIR)/rw-project.yang $(MODEL_DIR)/$*.yang
	# $(Q)sed -i 's|data\:image/gif\;base64,R0lGODlhS.*RCAA7|https://osm.etsi.org/images/OSM-logo.png\" width=\"175\" height=\"60|g' $(TREES_DIR)/$@
	# $(Q)sed -i 's|<a href=\"http://www.tail-f.com">|<a href="http://osm.etsi.org">|g' $(TREES_DIR)/$@
	$(Q)mv $(TREES_DIR)/$@ $(TREES_DIR)/$*.html

$(RW_PB_EXT):
	$(Q)mkdir -p $$(dirname $@)
	$(Q)wget -q https://raw.githubusercontent.com/RIFTIO/RIFT.ware/RIFT.ware-4.4.1/modules/core/util/yangtools/yang/rw-pb-ext.yang -O $@

package:
	tox -e build
	tox -e build3
	#./build-docs.sh


pyangbind: pyang
	git clone https://github.com/alf-tierno/pyangbind
	# cd pyangbind; git checkout issue151; \
    #    python setup.py --command-packages=stdeb.command bdist_deb; \
    #    python3 setup.py --command-packages=stdeb.command bdist_deb; \
    #    cd ..
	#mkdir -p deb_dist
	#cp pyangbind/deb_dist/*.deb deb_dist

pyang:
	git clone https://github.com/mbj4668/pyang
	# cd pyang; \
    #    python setup.py --command-packages=stdeb.command bdist_deb;  \
    #    python3 setup.py --command-packages=stdeb.command bdist_deb;  \
    #    cd ..
	#mkdir -p deb_dist
	#cp pyang/deb_dist/*.deb deb_dist

pyang-json-schema-plugin:
	git clone https://github.com/cmoberg/pyang-json-schema-plugin

clean-plugin:
	$(Q)rm -rf pyang-json-schema-plugin

clean:
	$(Q)rm -rf build dist fog05_im.egg-info deb deb_dist *.gz pyang pyangbind pyang-json-schema-plugin $(OUT_DIR) $(TREES_DIR)
	$(Q)rm -rf

install:
	python3 setup.py install

uninstall:
	pip3 remove fog05-im -y