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
# Contributors: Gabriele Baldoni, ADLINK Technology Inc. - Tests

import unittest
from fog05mm5 import Mm5


class APITest(unittest.TestCase):

    def test_dns_rules(self):
        self.maxDiff = None
        appid = '123'
        rule = {
            'dnsRuleId': 'dnsRule1',
            'domainName': 'www.example.com',
            'ipAddressType': 'IP_V4',
            'ipAddress': '192.0.2.0',
            'ttl': 100,
            'state': 'ACTIVE'
        }
        mm5 = Mm5()
        mm5.dns_rules.add(appid, rule)
        response_rule = {'DnsRule': rule}
        self.assertEqual(mm5.dns_rules.get(appid, rule['dnsRuleId']), response_rule)
        self.assertEqual(mm5.dns_rules.list(appid)['DnsRule'], [rule])

        updated_rule = {
            'dnsRuleId': 'dnsRule1',
            'domainName': 'www.google.com',
            'ipAddressType': 'IP_V4',
            'ipAddress': '192.0.2.0',
            'ttl': 100,
            'state': 'ACTIVE'
        }
        response_rule = {'DnsRule': updated_rule}
        mm5.dns_rules.update(appid, updated_rule['dnsRuleId'], updated_rule)
        self.assertEqual(mm5.dns_rules.get(appid, rule['dnsRuleId']), response_rule)
        self.assertEqual(mm5.dns_rules.list(appid)['DnsRule'], [updated_rule])

        mm5.dns_rules.remove(appid, updated_rule['dnsRuleId'])
        self.assertEqual(mm5.dns_rules.list(appid)['DnsRule'], [])
        self.assertRaises(ValueError, mm5.dns_rules.get, appid, updated_rule['dnsRuleId'])

    def test_traffic_rule(self):
        self.maxDiff = None
        appid = '123'
        rule = {
                'trafficRuleId': 'TrafficRule1',
                'filterType': 'FLOW',
                'priority': 1,
                'trafficFilter': [
                    {
                    'srcAddress': [
                        '192.168.1.1'
                    ],
                    'dstAddress': [
                        '192.168.1.1'
                    ],
                    'srcPort': [
                        '8080'
                    ],
                    'dstPort': [
                        '8080'
                    ],
                    "protocol": [],
                    "token": [],
                    "srcTunnelAddress": [],
                    "dstTunnelAddress": [],
                    "srcTunnelPort": [],
                    "dstTunnelPort": [],
                    'qCI': 1,
                    'dSCP': 0,
                    'tC': 1
                    }
                ],
                'action': 'DROP',
                'dstInterface': {
                    'interfaceType': 'TUNNEL',
                    'tunnelInfo': {
                    'tunnelType': 'GTP_U',
                    },
                    'srcMacAddress': '02-00-00-00-00-00',
                    'dstMacAddress': '02-00-00-00-00-00',
                    'dstIpAddress': '192.0.2.0'
                },
                'state': 'ACTIVE'
            }
        mm5 = Mm5()
        mm5.traffic_rules.add(appid, rule)
        response_rule = {'TrafficRule': rule}
        self.assertEqual(mm5.traffic_rules.get(appid, rule['trafficRuleId']), response_rule)
        self.assertEqual(mm5.traffic_rules.list(appid)['TrafficRule'], [rule])

        updated_rule = {
                'trafficRuleId': 'TrafficRule1',
                'filterType': 'FLOW',
                'priority': 1,
                'trafficFilter': [
                    {
                    'srcAddress': [
                        '192.168.1.1'
                    ],
                    'dstAddress': [
                        '192.168.1.1'
                    ],
                    'srcPort': [
                        '8080'
                    ],
                    'dstPort': [
                        '8080'
                    ],
                     "protocol": [],
                    "token": [],
                    "srcTunnelAddress": [],
                    "dstTunnelAddress": [],
                    "srcTunnelPort": [],
                    "dstTunnelPort": [],
                    'qCI': 1,
                    'dSCP': 0,
                    'tC': 1
                    }
                ],
                'action': 'DROP',
                'dstInterface': {
                    'interfaceType': 'TUNNEL',
                    'tunnelInfo': {
                    'tunnelType': 'GTP_U',
                    },
                    'srcMacAddress': '02-00-00-00-00-00',
                    'dstMacAddress': '02-00-00-00-00-00',
                    'dstIpAddress': '192.0.2.0'
                },
                'state': 'INACTIVE'
            }
        response_rule = {'TrafficRule': updated_rule}
        mm5.traffic_rules.update(appid, updated_rule['trafficRuleId'], updated_rule)
        self.assertEqual(mm5.traffic_rules.get(appid, updated_rule['trafficRuleId']), response_rule)
        self.assertEqual(mm5.traffic_rules.list(appid)['TrafficRule'], [updated_rule])

        mm5.traffic_rules.remove(appid, updated_rule['trafficRuleId'])
        self.assertEqual(mm5.traffic_rules.list(appid)['TrafficRule'], [])
        self.assertRaises(ValueError, mm5.traffic_rules.get, appid, updated_rule['trafficRuleId'])

    def test_services(self):
        self.maxDiff = None
        service_info = {
                "serInstanceId": "ServiceInstance123",
                "serName": "ExampleService",
                "serCategory": {
                    "href": "catItem1",
                    "id": "id12345",
                    "name": "RNI",
                    "version": "version1"
                },
                "version": "ServiceVersion1",
                "state": "ACTIVE",
                "transportId": "Rest1",
                "transportInfo": {
                    "id": "TransId12345",
                    "name": "REST",
                    "description": "REST API",
                    "type": "REST_HTTP",
                    "protocol": "HTTP",
                    "version": "2.0",
                    "endpoint": {
                    "uris": [
                        "/meMp1/service/EntryPoint"
                    ],
                    "addresses": [
                        {
                        "host": "192.0.2.0",
                        "port": 8080
                        }
                    ],
                    "alternative": {}
                    },
                    "security": {
                    "oAuth2Info": {
                        "grantTypes": "OAUTH2_CLIENT_CREDENTIALS",
                        "tokenEndpoint": "/meMp1/security/TokenEndPoint"
                    }
                    },
                    "implSpecificInfo": {}
                },
                "serializer": "JSON"
                }
        mm5 = Mm5()
        mm5.services.add(service_info)
        response_svc = {'ServiceInfo': service_info}
        self.assertEqual(mm5.services.get(service_info['serInstanceId']), response_svc)
        self.assertEqual(mm5.services.list()['ServiceInfo'], [service_info])

        updated_svc = {
                "serInstanceId": "ServiceInstance123",
                "serName": "ExampleService",
                "serCategory": {
                    "href": "catItem1",
                    "id": "id12345",
                    "name": "RNI",
                    "version": "version1"
                },
                "version": "ServiceVersion1",
                "state": "INACTIVE",
                "transportId": "Rest1",
                "transportInfo": {
                    "id": "TransId12345",
                    "name": "REST",
                    "description": "REST API",
                    "type": "REST_HTTP",
                    "protocol": "HTTP",
                    "version": "2.0",
                    "endpoint": {
                    "uris": [
                        "/meMp1/service/EntryPoint"
                    ],
                    "addresses": [
                        {
                        "host": "192.0.2.0",
                        "port": 8080
                        }
                    ],
                    "alternative": {}
                    },
                    "security": {
                    "oAuth2Info": {
                        "grantTypes": "OAUTH2_CLIENT_CREDENTIALS",
                        "tokenEndpoint": "/meMp1/security/TokenEndPoint"
                    }
                    },
                    "implSpecificInfo": {}
                },
                "serializer": "JSON"
                }
        response_svc = {'ServiceInfo': updated_svc}
        mm5.services.update(service_info['serInstanceId'], updated_svc)
        self.assertEqual(mm5.services.get(updated_svc['serInstanceId']), response_svc)
        self.assertEqual(mm5.services.list()['ServiceInfo'], [service_info])

        mm5.services.remove(updated_svc['serInstanceId'])
        self.assertEqual(mm5.services.list()['ServiceInfo'], [])
        self.assertRaises(ValueError, mm5.services.get, updated_svc['serInstanceId'])

    def test_transport(self):
        self.maxDiff = None
        transport_info = {
            "id": "TransId12345",
            "name": "REST",
            "description": "REST API",
            "type": "REST_HTTP",
            "protocol": "HTTP",
            "version": "2.0",
            "endpoint": {
                "uris": [
                "/meMp1/service/EntryPoint"
                ],
                "addresses": [
                {
                    "host": "192.0.2.0",
                    "port": 8080
                }
                ],
                "alternative": {}
            },
            "security": {
                "oAuth2Info": {
                "grantTypes": "OAUTH2_CLIENT_CREDENTIALS",
                "tokenEndpoint": "/meMp1/security/TokenEndPoint"
                }
            },
            "implSpecificInfo": {}
        }

        mm5 = Mm5()
        mm5.transports.add(transport_info)
        response_tx = {'TransportInfo': transport_info}
        self.assertEqual(mm5.transports.get(transport_info['id']), response_tx)
        self.assertEqual(mm5.transports.list()['TransportInfo'], [transport_info])

        updated_tx = {
            "id": "TransId12345",
            "name": "REST",
            "description": "REST API",
            "type": "REST_HTTP",
            "protocol": "HTTP",
            "version": "2.0",
            "endpoint": {
                "uris": [
                "/meMp1/service/newEntryPoint"
                ],
                "addresses": [
                {
                    "host": "192.0.2.0",
                    "port": 8080
                }
                ],
                "alternative": {}
            },
            "security": {
                "oAuth2Info": {
                "grantTypes": "OAUTH2_CLIENT_CREDENTIALS",
                "tokenEndpoint": "/meMp1/security/TokenEndPoint"
                }
            },
            "implSpecificInfo": {}
        }

        response_tx = {'TransportInfo': updated_tx}
        mm5.transports.update(updated_tx['id'], updated_tx)
        self.assertEqual(mm5.transports.get(updated_tx['id']), response_tx)
        self.assertEqual(mm5.transports.list()['TransportInfo'], [transport_info])

        mm5.transports.remove(updated_tx['id'])
        self.assertEqual(mm5.transports.list()['TransportInfo'], [])
        self.assertRaises(ValueError, mm5.transports.get, updated_tx['id'])

    def test_application(self):
        self.maxDiff = None
        appd = {
            'appTrafficRule': [],
            'appServiceProduced': [],
            'appDNSRule': [],
            'appName': 'TestApp',
            'appDId': 'App123',
            'appProvider': 'ETSI',
            'state': 'ACTIVE',
            'appInstanceId': 'd8f659a9-5864-426d-b3a6-76cf866201c6',
            'softVersion': '0.1'
            }

        mm5 = Mm5()
        mm5.applications.add(appd)
        self.assertEqual(mm5.applications.get(appd['appInstanceId'])['ApplicationInfo'], appd)
        self.assertEqual(mm5.applications.list()['ApplicationInfo'], [appd])

        updated_appd = {
            'appTrafficRule': [],
            'appServiceProduced': [],
            'appDNSRule': [],
            'appName': 'TestApp',
            'appDId': 'App123',
            'appProvider': 'ETSI',
            'state': 'ACTIVE',
            'appInstanceId': 'd8f659a9-5864-426d-b3a6-76cf866201c6',
            'softVersion': '1.1'
            }

        mm5.applications.update(updated_appd['appInstanceId'], updated_appd)
        self.assertEqual(mm5.applications.get(updated_appd['appInstanceId'])['ApplicationInfo'], updated_appd)
        self.assertEqual(mm5.applications.list()['ApplicationInfo'], [updated_appd])

        mm5.applications.remove(updated_appd['appInstanceId'])
        self.assertEqual(mm5.applications.list()['ApplicationInfo'], [])
        self.assertRaises(ValueError, mm5.applications.get, updated_appd['appInstanceId'])
