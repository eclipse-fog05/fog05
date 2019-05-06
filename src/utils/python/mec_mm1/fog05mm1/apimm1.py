# Copyright (c) 2014,2018 Contributors to the Eclipse Foundation
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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - API v2

import requests
import json
import os
import tempfile
import uuid


def save_file(content, filename):
    full_path = os.path.join(tempfile.gettempdir(), filename)
    f = open(full_path, 'w')
    f.write(content)
    f.flush()
    f.close()
    return full_path


class Mm1(object):
    '''
        This class allow the interaction with fog05 FIM
    '''

    def __init__(self, endpoint='127.0.0.1:8091/exampleAPI/mm5/v1',):
        self.base_url = 'http://{}'.format(endpoint)
        self.applications = self.Applications(self.base_url)
        self.dns_rules = self.DnsRules(self.base_url)
        self.traffic_rules = self.TrafficRules(self.base_url)
        self.services = self.Services(self.base_url)
        self.transports = self.Transports(self.base_url)
        self.platforms = self.platforms(self.base_url)

    def check(self):
        url = '{}'.format(self.base_url)
        return json.loads(requests.get(url).text)

    def close(self):
        pass

    class Platforms(object):
        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            url = '{}/platforms'.format(self.base_url)
            return json.loads(requests.get(url).text)

        def add(self, platd):
            url = '{}/platforms'.format(self.base_url)
            return json.loads(requests.post(url, data=json.dumps(platd)).text)

        def get(self, platformid):
            url = '{}/platforms/{}'.format(self.base_url, platformid)
            ret = json.loads(requests.get(url).text)
            if 'ProblemDetails' in ret.keys():
                raise ValueError(ret['ProblemDetails']['title'])
            return ret

        def update(self, platformid, platd):
            url = '{}/platforms/{}'.format(self.base_url, platformid)
            return json.loads(requests.put(url, data=json.dumps(platd)).text)

        def remove(self, platformid):
            url = '{}/platforms/{}'.format(self.base_url, platformid)
            ret = requests.delete(url)
            return {'id': platformid}

    class Applications(object):
        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            url = '{}/applications'.format(self.base_url)
            return json.loads(requests.get(url).text)

        def add(self, appd):
            url = '{}/applications'.format(self.base_url)
            return json.loads(requests.post(url, data=json.dumps(appd)).text)

        def get(self, applicationid):
            url = '{}/applications/{}'.format(self.base_url, applicationid)
            ret = json.loads(requests.get(url).text)
            if 'ProblemDetails' in ret.keys():
                raise ValueError(ret['ProblemDetails']['title'])
            return ret

        def update(self, applicationid, appd):
            url = '{}/applications/{}'.format(self.base_url, applicationid)
            return json.loads(requests.put(url, data=json.dumps(appd)).text)

        def remove(self, applicationid):
            url = '{}/applications/{}'.format(self.base_url, applicationid)
            ret = requests.delete(url)
            return {'id': applicationid}

    class DnsRules(object):
        def __init__(self, base_url):
            self.base_url = base_url

        def list(self, applicationid):
            url = '{}/applications/{}/dns_rules'.format(self.base_url, applicationid)
            return json.loads(requests.get(url).text)

        def add(self, applicationid, dns_rule):
            url = '{}/applications/{}/dns_rules'.format(self.base_url, applicationid)
            return json.loads(requests.post(url, data=json.dumps(dns_rule)).text)

        def update(self, applicationid, dns_rule_id, dns_rule):
            url = '{}/applications/{}/dns_rules/{}'.format(self.base_url, applicationid, dns_rule_id)
            return json.loads(requests.put(url, data=json.dumps(dns_rule)).text)

        def get(self, applicationid, dns_rule_id):
            url = '{}/applications/{}/dns_rules/{}'.format(self.base_url, applicationid, dns_rule_id)
            ret = json.loads(requests.get(url).text)
            if 'ProblemDetails' in ret.keys():
                raise ValueError(ret['ProblemDetails']['title'])
            return ret

        def remove(self, applicationid, dns_rule_id):
            url = '{}/applications/{}/dns_rules/{}'.format(self.base_url, applicationid, dns_rule_id)
            ret = requests.delete(url)
            return {'DnsRule': {'dnsRuleId': dns_rule_id}}

    class TrafficRules(object):
        def __init__(self, base_url):
            self.base_url = base_url

        def list(self, applicationid):
            url = '{}/applications/{}/traffic_rules'.format(self.base_url, applicationid)
            return json.loads(requests.get(url).text)

        def add(self, applicationid, traffic_rule):
            url = '{}/applications/{}/traffic_rules'.format(self.base_url, applicationid)
            return json.loads(requests.post(url, data=json.dumps(traffic_rule)).text)

        def update(self, applicationid, traffic_rule_id, traffic_rule):
            url = '{}/applications/{}/traffic_rules/{}'.format(self.base_url, applicationid, traffic_rule_id)
            return json.loads(requests.put(url, data=json.dumps(traffic_rule)).text)

        def get(self, applicationid, traffic_rule_id):
            url = '{}/applications/{}/traffic_rules/{}'.format(self.base_url, applicationid, traffic_rule_id)
            ret = json.loads(requests.get(url).text)
            if 'ProblemDetails' in ret.keys():
                raise ValueError(ret['ProblemDetails']['title'])
            return ret

        def remove(self, applicationid, traffic_rule_id):
            url = '{}/applications/{}/traffic_rules/{}'.format(self.base_url, applicationid, traffic_rule_id)
            ret = requests.delete(url)
            return {'TrafficRule': {'trafficRuleId': traffic_rule_id}}

    class Services(object):
        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            url = '{}/services'.format(self.base_url)
            return json.loads(requests.get(url).text)

        def add(self, service_info):
            url = '{}/services'.format(self.base_url)
            return json.loads(requests.post(url, data=json.dumps(service_info)).text)

        def update(self, service_id, service_info):
            url = '{}/services/{}'.format(self.base_url, service_id)
            return json.loads(requests.put(url, data=json.dumps(service_info)).text)

        def get(self, service_id):
            url = '{}/services/{}'.format(self.base_url, service_id)
            ret = json.loads(requests.get(url).text)
            if 'ProblemDetails' in ret.keys():
                raise ValueError(ret['ProblemDetails']['title'])
            return ret

        def remove(self, service_id):
            url = '{}/services/{}'.format(self.base_url, service_id)
            ret = requests.delete(url)
            return {'ServiceInfo': {'serInstanceId': service_id}}

    class Transports(object):
        def __init__(self, base_url):
            self.base_url = base_url

        def list(self):
            url = '{}/transports'.format(self.base_url)
            return json.loads(requests.get(url).text)

        def add(self, transport_info):
            url = '{}/transports'.format(self.base_url)
            return json.loads(requests.post(url, data=json.dumps(transport_info)).text)

        def update(self, transport_id, transport_info):
            url = '{}/transports/{}'.format(self.base_url, transport_id)
            return json.loads(requests.put(url, data=json.dumps(transport_info)).text)

        def get(self, transport_id):
            url = '{}/transports/{}'.format(self.base_url, transport_id)
            ret = json.loads(requests.get(url).text)
            if 'ProblemDetails' in ret.keys():
                raise ValueError(ret['ProblemDetails']['title'])
            return ret

        def remove(self, transport_id):
            url = '{}/transports/{}'.format(self.base_url, transport_id)
            ret = requests.delete(url)
            return {'TransportInfo': {'id': transport_id}}
