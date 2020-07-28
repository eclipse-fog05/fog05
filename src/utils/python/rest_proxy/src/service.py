#!/usr/bin/env python3
import json
import sys
import os
from flask import Flask, request, abort, send_from_directory, url_for
from fog05 import FIMAPI
from fog05_sdk.interfaces import Constants
from fog05_sdk.interfaces.FDU import FDU
from fog05_sdk.interfaces.InfraFDU import InfraFDU


# conf = None
# fos_api = None
app = Flask(__name__)



@app.route('/')
def index():
    return json.dumps({'name':'Eclipse fog05 REST Proxy', 'version':'0.2.0', 'system':conf.get('sysid'), 'tenant':conf.get('tenantid')})


# NODE

@app.route('/nodes/list', methods=['GET'])
def node_list():
    return json.dumps(fos_api.node.list())


@app.route('/nodes/<uuid>/info', methods=['GET'])
def node_info(uuid):
    return json.dumps(fos_api.node.info(uuid))


@app.route('/node/<uuid>/status', methods=['GET'])
def node_status(uuid):
    return json.dumps(fos_api.node.status(uuid))


@app.route('/nodes/<uuid>/plugins/list', methods=['GET'])
def node_plugins(uuid):
    return json.dumps(fos_api.node.plugins(uuid))

# PLUGIN


@app.route('/nodes/<node_uuid>/plugins/<pl_uuid>/info', methods=['GET'])
def plugin_info(pl_uuid, node_uuid):
    return json.dumps(fos_api.plugin.info(node_uuid, pl_uuid))

# NETWORK

@app.route('/networks/<net_uuid>/info', methods=['GET','PUT','DELETE'])
def network(net_uuid):

    method = request.method
    if method == 'GET':
        nets = fos_api.network.list()
        n = [n for n in nets if n.get('uuid') == net_uuid]
        if len(n) == 0:
            return json.dumps({})
        return json.dumps(n[0])
    elif method == 'PUT':
        descriptor = json.loads(request.data)
        return json.dumps(fos_api.network.add_network(descriptor))
    elif method == 'DELETE':
        return json.dumps(fos_api.network.remove_network(net_uuid))



@app.route('/nodes/<node>/network/<netid>/info', methods=['PUT', 'DELETE'])
def network_node(node, net_id):
    method = request.method
    if method == 'PUT':
        descriptor = json.loads(request.data)
        try:
            res = json.dumps(fos_api.network.add_network_to_node(descriptor, node))
        except ValueError as ve:
            return json.dumps({'error':'{}'.format(ve)})
        return res
    elif method == 'DELETE':
        try:
            res = json.dumps(fos_api.network.remove_network_from_node(net_id, node))
        except ValueError as ve:
            return json.dumps({'error':'{}'.format(ve)})
        return res


@app.route('/network/list', methods=['GET'])
def network_list():
    return json.dumps(fos_api.network.list())


# @app.route('/connection_point/add', methods=['POST'])
# def cp_add():
#     data = request.data
#     if isinstance(data,bytes):
#         data = data.decode()
#     descriptor = json.loads(data)
#     return json.dumps({'result':fos_api.network.add_connection_point(descriptor)})


# @app.route('/connection_point/remove/<cp_id>', methods=['DELETE'])
# def cp_remove(cp_id):
#     return json.dumps({'result':fos_api.network.delete_connection_point(cp_id)})


# FDU

@app.route('/fdu/<fduid>/info', methods=['GET','DELETE','PUT'])
def fdu(fduid):

        #  try:
        #     res = json.dumps(fos_api.network.remove_network_from_node(net_id, node))
        # except ValueError as ve:
        #     return json.dumps({'error':'{}'.format(ve)})
        # return res
    method = request.method
    if method == 'GET':
        try:
            res = fos_api.fdu.info(fduid)
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return json.dumps(res.to_json())
    elif method == 'PUT':
        data = request.data
        if isinstance(data,bytes):
            data = data.decode()
        descriptor = json.loads(data)
        try:
            res = json.dumps(fos_api.fdu.onboard(descriptor))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res
    elif method == 'DELETE':
        try:
            res = json.dumps(fos_api.fdu.offload(fduid))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res

@app.route('/fdu/{}/schedule', methods=['PUT'])
def fdu_define(fduid):
    try:
        res = fos_api.fdu.define(fduid)
    except Exception as ve:
        return json.dumps({'error':'{}'.format(ve)})
    return json.dumps(res.to_json())


@app.route('/nodes/<node>/<fduid>/define', methods=['PUT'])
def fdu_define_node(node, fduid):
    try:
        res = fos_api.fdu.define(fduid, node)
    except Exception as ve:
        return json.dumps({'error':'{}'.format(ve)})
    return json.dumps(res.to_json())



@app.route('/fdu/instances/<instance>/info', methods=['GET','DELETE'])
def fdu_instance(instance):
    method = request.method
    if method == 'GET':
        try:
            res = fos_api.fdu.instance_info(instance)
        except Exception as ve:
            return json.dumps({'error':'{}'.format(ve)})
        return json.dumps(res.to_json())
    elif method == 'DELETE':
        try:
            res = json.dumps(fos_api.fdu.undefine(instance))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res





@app.route('/fdu/instances/<instance>/configure', methods=['POST'])
def fdu_instance_configure(instance):
    try:
        res = json.dumps(fos_api.fdu.configure(instance))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res


@app.route('/fdu/instances/<instance>/clean', methods=['POST'])
def fdu_instance_clean(instance):
    try:
        res = json.dumps(fos_api.fdu.clean(instance))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res

@app.route('/fdu/instances/<instance>/start', methods=['POST'])
def fdu_instance_start(instance):
    try:
        env = request.data
        if isinstance(env,bytes):
            env = env.decode()
        res = json.dumps(fos_api.fdu.start(instance, env))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res


@app.route('/fdu/instances/<instance>/stop', methods=['POST'])
def fdu_instance_stop(instance):
    try:
        res = json.dumps(fos_api.fdu.stop(instance))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res

@app.route('/fdu/instances/<instance>/pause', methods=['POST'])
def fdu_instance_pause(instance):
    try:
        res = json.dumps(fos_api.fdu.pause(instance))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res

@app.route('/fdu/instances/<instance>/resume', methods=['POST'])
def fdu_instance_resume(instance):
    try:
        res = json.dumps(fos_api.fdu.resume(instance))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res

@app.route('/fdu/instances/<instance>/migrate/<destination>', methods=['POST'])
def fdu_instance_resume(instance, destination):
    try:
        res = json.dumps(fos_api.fdu.migrate(instance, destination))
    except Exception as e:
        return json.dumps({'error':'{}'.format(e)})
    return res



@app.route('/fdu/<fdu>/nodes/list', methods=['GET'])
def fdu_get_nodes(fdu):
    return json.dumps(fos_api.fdu.get_nodes(fdu))


@app.route('/nodes/<node>/fdu/list', methods=['GET'])
def fdu_node_list(node):
    return json.dumps(fos_api.fdu.list_node(node))



@app.route('/fdu/<fdu>/instances/list', methods=['GET'])
def fdu_instance_list(fdu):
    return json.dumps(fos_api.fdu.instance_list(fdu))


@app.route('/fdu/list', methods=['GET'])
def fdu_list():
    return json.dumps(fos_api.fdu.list())

# IMAGE

@app.route('/images/<imgid>/info', methods=['GET','PUT','DELETE'])
def image(imgid):

    method = request.method
    if method == 'GET':
        try:
            return json.dumps(fos_api.image.get(imgid))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
    elif method == 'PUT':
        data = request.data
        if isinstance(data,bytes):
            data = data.decode()
        descriptor = json.loads(data)
        try:
            res = json.dumps(fos_api.image.add(descriptor))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res
    elif method == 'DELETE':
        try:
            res = json.dumps(fos_api.fdu.remove(imgid))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res


@app.route('/images/list', methods=['GET'])
def image_list():
    return json.dumps(fos_api.image.list())


#FLAVOR

@app.route('/flavors/<flv_id>/info', methods=['GET','PUT','DELETE'])
def flavor(flv_id):

    method = request.method
    if method == 'GET':
        try:
            return json.dumps(fos_api.flavor.get(flv_id))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
    elif method == 'PUT':
        data = request.data
        if isinstance(data,bytes):
            data = data.decode()
        descriptor = json.loads(data)
        try:
            res = json.dumps(fos_api.flavor.add(descriptor))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res
    elif method == 'DELETE':
        try:
            res = json.dumps(fos_api.fdu.remove(flv_id))
        except Exception as e:
            return json.dumps({'error':'{}'.format(e)})
        return res


@app.route('/flavors/list', methods=['GET'])
def flavor_list():
    return json.dumps(fos_api.flavor.list())


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
    global img_dict
    img_dict = {}
    app.run(host=conf.get('host'),port=conf.get('port'),debug=conf.get('debug'))