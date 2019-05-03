#!flask/bin/python
import json
import sys
import os
import psutil
import signal
from flask import Flask, request, abort, send_from_directory, url_for

# HOST_FILE = 'dynhosts'
HOST_FILE = '/tmp/dynhosts'
# conf = None
# fos_api = None
app = Flask(__name__)



## HELPERS

def signal_dnsmasq():
    pids = psutil.pids()
    for pid in pids:
        if psutil.Process(pid).name() == "dnsmasq":
            os.kill(pid,signal.SIGHUP)
            break

def update_host(hostname, ip):
    line_to_update = "%s\t%s\n" %(ip, hostname)
    with open(HOST_FILE, 'r') as f:
        data = f.readlines()

    updated = False
    # need to enumerate list iter to update data
    for idx, line in enumerate(data):
        # split tab delimiter
        hn = line.split('\t')[1]
        # remove end of line char
        hn = hn.split('\n')[0]
        if line == line_to_update:
            return
        elif hn == hostname:
            data[idx] = line_to_update
            updated = True
    if not updated:
        data.append(line_to_update)
    with open(HOST_FILE, 'w') as f:
        f.writelines(data)
    signal_dnsmasq()


def delete_host(hostname, ip):
    line_to_update = "%s\t%s\n" %(ip, hostname)
    with open(HOST_FILE, 'r') as f:
        data = f.readlines()

    with open(HOST_FILE, 'w') as f:
        for line in data:
            if line != line_to_update:
                f.write(line)
    signal_dnsmasq()


@app.route('/')
def index():
    return json.dumps({'name':'Eclipse fog05 DynDNS', 'version':'0.0.1'})



# GET Record
@app.route('/record',methods=['GET'])
def get_records():
    with open(HOST_FILE, 'r') as f:
        cont = f.readlines()
    print(cont)
    l = []
    for line in cont:
        ls = line.split('\t')
        print(ls)
        r = {
            'ip': ls[0],
            'name': ls[1]
        }
        l.append(r)
    return json.dumps({'result':l})


# Add Record
@app.route('/record',methods=['PUT'])
def add_record():
    data = json.loads(request.data)
    ip = data['ip']
    name = data['name']
    update_host(name,ip)
    return json.dumps({'result':'added'})


# Remove Record
@app.route('/record',methods=['DELETE'])
def del_record():
    data = json.loads(request.data)
    ip = data['ip']
    name = data['name']
    delete_host(name,ip)
    return json.dumps({'result':'deletted'})
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
    app.run(host=conf.get('host'),port=conf.get('port'),debug=conf.get('debug'))