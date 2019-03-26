#!flask/bin/python
import json
import sys
import os
from flask import Flask, request
from fog05 import FIMAPI


# conf = None
# fos_api = None
app = Flask(__name__)



@app.route('/')
def index():
    return json.dumps({'name':'Eclipse fog05 REST Proxy', 'version':'0.0.1', 'system':conf.get('sysid'), 'tenant':conf.get('tenantid')})


# NODE

@app.route('/node/list', methods=['GET'])
def node_list():
    return json.dumps(fos_api.node.list())

@app.route('/node/info/<uuid>', methods=['GET'])
def node_info(uuid):
    return json.dumps(fos_api.node.info(uuid))

@app.route('/node/status/<uuid>', methods=['GET'])
def node_info(uuid):
    return json.dumps(fos_api.node.status(uuid))


@app.route('/node/plugins/<uuid>', methods=['GET'])
def node_plugins(uuid):
    return json.dumps(fos_api.node.plugins(uuid))

# PLUGIN


@app.route('/plugin/info/<pl_uuid>/<node_uuid>', methods=['GET'])
def plugin_info(pl_uuid, node_uuid):
    return json.dumps(fos_api.plugin.info(node_uuid, pl_uuid))

# NETWORK

@app.route('/network/add', methods=['POST'])
def network_add():
    descriptor = json.loads(request.data)
    return json.dumps({'result':fos_api.network.add_network(descriptor)})


@app.route('/network/remove/<net_id>', methods=['DELETE'])
def network_remove(net_id):
    return json.dumps({'result':fos_api.network.remove_network(net_id)})

@app.route('/network/list', methods=['GET'])
def network_list():
    return json.dumps(fos_api.network.list())

@app.route('/connection_point/add', methods=['POST'])
def cp_add():
    descriptor = json.loads(request.data)
    return json.dumps({'result':fos_api.network.add_connection_point(descriptor)})


@app.route('/connection_point/remove/<cp_id>', methods=['DELETE'])
def cp_remove(cp_id):
    return json.dumps({'result':fos_api.network.delete_connection_point(cp_id)})


# FDU

@app.route('/fdu/onboard', methods=['POST'])
def fdu_onboard():
    descriptor = json.loads(request.data)
    return json.dumps({'result':fos_api.fdu.onboard(descriptor)})

@app.route('/fdu/offload/<fdu_id>', methods=['DELETE'])
def fdu_offload(fdu_id):
    return json.dumps({'result':fos_api.fdu.offload(fdu_id)})

@app.route('/fdu/define/<fdu_id>/<node_id>', methods=['POST'])
def fdu_define(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.define(fdu_id, node_id, wait=True)})

@app.route('/fdu/undefine/<fdu_id>/<node_id>', methods=['DELETE'])
def fdu_undefine(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.undefine(fdu_id, node_id, wait=True)})

@app.route('/fdu/configure/<fdu_id>/<node_id>', methods=['POST'])
def fdu_configure(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.configure(fdu_id, node_id, wait=True)})

@app.route('/fdu/clean/<fdu_id>/<node_id>', methods=['POST'])
def fdu_clean(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.clean(fdu_id, node_id, wait=True)})

@app.route('/fdu/run/<fdu_id>/<node_id>', methods=['POST'])
def fdu_run(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.run(fdu_id, node_id, wait=True)})

@app.route('/fdu/stop/<fdu_id>/<node_id>', methods=['POST'])
def fdu_stop(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.stop(fdu_id, node_id, wait=True)})

@app.route('/fdu/pause/<fdu_id>/<node_id>', methods=['POST'])
def fdu_pause(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.pause(fdu_id, node_id, wait=True)})

@app.route('/fdu/resume/<fdu_id>/<node_id>', methods=['POST'])
def fdu_resume(fdu_id, node_id):
    return json.dumps({'result':fos_api.fdu.resume(fdu_id, node_id, wait=True)})

@app.route('/fdu/info/<fdu_id>', methods=['GET'])
def fdu_info(fdu_id):
    return json.dumps(fos_api.fdu.info(fdu_id))

@app.route('/fdu/instance_info/<fdu_id>/<node_id>', methods=['GET'])
def fdu_instance_info(fdu_id, node_id):
    return json.dumps(fos_api.fdu.instance_info(fdu_id, node_id))

@app.route('/fdu/list', methods=['GET'])
def fdu_list():
    return json.dumps(fos_api.fdu.list())

# IMAGE

@app.route('/image/add', methods=['POST'])
def image_add():
    descriptor = json.loads(request.data)
    return json.dumps({'result':fos_api.image.add(descriptor)})

@app.route('/image/<img_id>', methods=['GET'])
def image_get(img_id):
    return json.dumps(fos_api.image.get(img_id))

@app.route('/image/list', methods=['GET'])
def image_list():
    return json.dumps(fos_api.image.list())

@app.route('/image/remove/<img_id>', methods=['DELETE'])
def image_remove(img_id):
    return json.dumps({'result':fos_api.image.remove(img_id)})

# FLAVOR


@app.route('/flavor/add', methods=['POST'])
def flavor_add():
    descriptor = json.loads(request.data)
    return json.dumps({'result':fos_api.flavor.add(descriptor)})

@app.route('/flavor/<flv_id>', methods=['GET'])
def flavor_get(flv_id):
    return json.dumps(fos_api.flavor.get(flv_id))

@app.route('/flavor/list', methods=['GET'])
def flavor_list():
    return json.dumps(fos_api.flavor.list())

@app.route('/flavor/<flv_id>', methods=['DELETE'])
def flavor_remove(flv_id):
    fos_api.flavor.remove(flv_id)
    return json.dumps({'result':True})


# MAIN and UTILS

def read_file(file_path):
    data = ''
    with open(file_path, 'r') as f:
        data = f.read()
    return data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        exit(-1)
    print('ARGS {}'.format(sys.argv))
    file_dir = os.path.dirname(__file__)
    cfg = json.loads(read_file(sys.argv[1]))
    global conf
    conf = cfg
    global fos_api
    fos_api = FIMAPI(locator=conf.get('yaks'), sysid=conf.get('sysid'), tenantid=conf.get('tenantid'))
    app.run(host=conf.get('host'),port=conf.get('port'),debug=conf.get('debug'))