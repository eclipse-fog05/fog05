#!flask/bin/python
import json
import sys
import os
from flask import Flask, request, abort, send_from_directory, url_for
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
def node_status(uuid):
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
    try:
        return json.dumps({'result':fos_api.fdu.define(fdu_id, node_id)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/undefine/<finstanceid>', methods=['DELETE'])
def fdu_undefine(instanceid):
    return json.dumps({'result':fos_api.fdu.undefine(instanceid)})


@app.route('/fdu/configure/<instanceid>', methods=['POST'])
def fdu_configure(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.configure(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/clean/<instanceid>', methods=['POST'])
def fdu_clean(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.clean(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/start/<instanceid>', methods=['POST'])
def fdu_run(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.start(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/stop/<instanceid>', methods=['POST'])
def fdu_stop(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.stop(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/pause/<instanceid>', methods=['POST'])
def fdu_pause(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.pause(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/resume/<instanceid>', methods=['POST'])
def fdu_resume(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.resume(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/migrate/<instanceid>/<destinationid>', methods=['POST'])
def fdu_migrate(instanceid ,destinationid):
    try:
        return json.dumps({'result':fos_api.fdu.migrate(instanceid, destinationid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/instantiate/<fdu_id>/<node_id>', methods=['POST'])
def fdu_instantiate(fdu_id, node_id):
    try:
        return json.dumps({'result':fos_api.fdu.instantiate(fdu_id, node_id)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/terminate/<instanceid>', methods=['POST'])
def fdu_terminate(instanceid):
    try:
        return json.dumps({'result':fos_api.fdu.terminate(instanceid)})
    except ValueError as ve:
        return json.dumps({'error':'{}'.format(ve)})


@app.route('/fdu/get_nodes/<fdu_id>', methods=['GET'])
def fdu_get_nodes(fdu_id):
    return json.dumps(fos_api.fdu.get_nodes(fdu_id))


@app.route('/fdu/list_node/<node_id>', methods=['GET'])
def fdu_node_list(node_id):
    return json.dumps(fos_api.fdu.list_node(node_id))


@app.route('/fdu/info/<fdu_id>', methods=['GET'])
def fdu_info(fdu_id):
    return json.dumps(fos_api.fdu.info(fdu_id))


@app.route('/fdu/instance_info/<instanceid>', methods=['GET'])
def fdu_instance_info(instanceid):
    return json.dumps(fos_api.fdu.instance_info(instanceid))


@app.route('/fdu/instance_list/<fdu_id>', methods=['GET'])
def fdu_instance_list(fdu_id):
    return json.dumps(fos_api.fdu.instance_list(fdu_id))


@app.route('/fdu/list', methods=['GET'])
def fdu_list():
    return json.dumps(fos_api.fdu.list())

# IMAGE

@app.route('/image/add', methods=['POST'])
def image_add():
    if 'descriptor' not in request.files:
        abort(403)
    if 'image' not in request.files:
        abort(403)

    desc_file = request.files['descriptor']
    desc_filename = desc_file.filename
    desc_path = os.path.join(conf.get('image_path'), desc_filename)
    desc_file.save(desc_path)
    descriptor = json.loads(read_file(desc_path))

    img_file = request.files['image']
    img_filename = img_file.filename
    img_path = os.path.join(conf.get('image_path'), img_filename)
    img_file.save(img_path)
    img_dict.update({descriptor.get('uuid'):img_filename})
    uri = 'http://{}:{}{}'.format( conf['host'], conf['port'],url_for('get_image_file',fname=img_filename))
    descriptor.update({'uri':uri})
    return json.dumps({'result':fos_api.image.add(descriptor)})


@app.route('/image/<img_id>', methods=['GET'])
def image_get(img_id):
    return json.dumps(fos_api.image.get(img_id))


@app.route('/image/list', methods=['GET'])
def image_list():
    return json.dumps(fos_api.image.list())


@app.route('/image/remove/<img_id>', methods=['DELETE'])
def image_remove(img_id):
    if img_id not in img_dict:
        abort(404)
    else:
        f_name = img_dict.pop(img_id)
        if os.path.isfile(os.path.join(conf.get('image_path'), f_name)):
            os.remove(os.path.join(conf.get('image_path'), f_name))
        if os.path.isfile(os.path.join(conf.get('image_path'), '{}.json'.format(img_id))):
            os.remove(os.path.join(conf.get('image_path'), '{}.json'.format(img_id)))
        return json.dumps({'result':fos_api.image.remove(img_id)})


@app.route('/image/file/<fname>', methods=['GET'])
def get_image_file(fname):
    return send_from_directory(conf.get('image_path'), fname)

#FLAVOR


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

    yendpoint= conf.get('yaks', os.environ['YAKS_HOST'])
    fos_api = FIMAPI(locator=yendpoint, sysid=conf.get('sysid'), tenantid=conf.get('tenantid'))
    global img_dict
    img_dict = {}
    app.run(host=conf.get('host'),port=conf.get('port'),debug=conf.get('debug'))