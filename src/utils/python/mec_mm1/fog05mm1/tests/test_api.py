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
from fog05mm1 import Mm1


class APITest(unittest.TestCase):

    def test_platforms(self):
        self.maxDiff = None
        plid = 'testp'
        uris = ['/exampleAPI/mm5/v1']

        mm1 = Mm1()

        res = mm1.platforms.list()
        self.assertEqual(1, len(res['PlatformInfo']))

        cp = mm1.platforms.get(plid)
        self.assertEqual(plid, cp['PlatformInfo']['platformId'])
        self.assertEqual(uris, cp['PlatformInfo']['endpoint']['uris'])

        res = mm1.platforms.remove(plid)
        self.assertEqual({'platformId': plid}, res)
        self.assertEqual(mm1.platforms.list(), {'PlatformInfo': []})

        res = mm1.platforms.add(cp['PlatformInfo'])
        self.assertEqual(res, cp)

    def test_dns_rules(self):
        self.maxDiff = None
        plid = 'testp'
        appid = '123'
        rule = {
            'dnsRuleId': 'dnsRule1',
            'domainName': 'www.example.com',
            'ipAddressType': 'IP_V4',
            'ipAddress': '192.0.2.0',
            'ttl': 100,
            'state': 'ACTIVE'
        }
        mm1 = Mm1()
        mm1.dns_rules.add(plid, appid, rule)
        response_rule = {'DnsRule': rule}
        self.assertEqual(mm1.dns_rules.get(plid, appid, rule['dnsRuleId']), response_rule)
        self.assertEqual(mm1.dns_rules.list(plid, appid)['DnsRule'], [rule])

        updated_rule = {
            'dnsRuleId': 'dnsRule1',
            'domainName': 'www.google.com',
            'ipAddressType': 'IP_V4',
            'ipAddress': '192.0.2.0',
            'ttl': 100,
            'state': 'ACTIVE'
        }
        response_rule = {'DnsRule': updated_rule}
        mm1.dns_rules.update(plid, appid, updated_rule['dnsRuleId'], updated_rule)
        self.assertEqual(mm1.dns_rules.get(plid, appid, updated_rule['dnsRuleId']), response_rule)
        self.assertEqual(mm1.dns_rules.list(plid, appid)['DnsRule'], [updated_rule])

        mm1.dns_rules.remove(plid, appid, updated_rule['dnsRuleId'])
        self.assertEqual(mm1.dns_rules.list(plid, appid)['DnsRule'], [])
        self.assertRaises(ValueError, mm1.dns_rules.get, plid, appid, updated_rule['dnsRuleId'])

    def test_traffic_rule(self):
        self.maxDiff = None
        plid = 'testp'
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
        mm1 = Mm1()
        mm1.traffic_rules.add(plid, appid, rule)
        response_rule = {'TrafficRule': rule}
        self.assertEqual(mm1.traffic_rules.get(plid, appid, rule['trafficRuleId']), response_rule)
        self.assertEqual(mm1.traffic_rules.list(plid, appid)['TrafficRule'], [rule])

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
        mm1.traffic_rules.update(plid, appid, updated_rule['trafficRuleId'], updated_rule)
        self.assertEqual(mm1.traffic_rules.get(plid, appid, updated_rule['trafficRuleId']), response_rule)
        self.assertEqual(mm1.traffic_rules.list(plid, appid)['TrafficRule'], [updated_rule])

        mm1.traffic_rules.remove(appid, updated_rule['trafficRuleId'])
        self.assertEqual(mm1.traffic_rules.list(plid, appid)['TrafficRule'], [])
        self.assertRaises(ValueError, mm1.traffic_rules.get, plid, appid, updated_rule['trafficRuleId'])

    def test_services(self):
        self.maxDiff = None
        plid = 'testp'
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
        mm1 = Mm1()
        mm1.services.add(plid, service_info)
        response_svc = {'ServiceInfo': service_info}
        self.assertEqual(mm1.services.get(plid, service_info['serInstanceId']), response_svc)
        self.assertEqual(mm1.services.list(plid)['ServiceInfo'], [service_info])

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
        mm1.services.update(plid, service_info['serInstanceId'], updated_svc)
        self.assertEqual(mm1.services.get(plid, updated_svc['serInstanceId']), response_svc)
        self.assertEqual(mm1.services.list(plid)['ServiceInfo'], [updated_svc])

        mm1.services.remove(plid, updated_svc['serInstanceId'])
        self.assertEqual(mm1.services.list(plid)['ServiceInfo'], [])
        self.assertRaises(ValueError, mm1.services.get, plid, updated_svc['serInstanceId'])

    def test_transport(self):
        self.maxDiff = None
        plid = 'testp'
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

        mm1 = Mm1()
        mm1.transports.add(plid, transport_info)
        response_tx = {'TransportInfo': transport_info}
        self.assertEqual(mm1.transports.get(plid, transport_info['id']), response_tx)
        self.assertEqual(mm1.transports.list(plid)['TransportInfo'], [transport_info])

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
        mm1.transports.update(plid, updated_tx['id'], updated_tx)
        self.assertEqual(mm1.transports.get(plid, updated_tx['id']), response_tx)
        self.assertEqual(mm1.transports.list(plid)['TransportInfo'], [updated_tx])

        mm1.transports.remove(plid, updated_tx['id'])
        self.assertEqual(mm1.transports.list(plid)['TransportInfo'], [])
        self.assertRaises(ValueError, mm1.transports.get, plid, updated_tx['id'])

    def test_application(self):
        self.maxDiff = None
        plid = 'testp'
        appd = {
            "appDId": "App123",
            "appName": "TestApp",
            "appProvider": "ETSI",
            "appSoftVersion": "0.1",
            "appDVersion": "1",
            "mecVersion": ["1", "2"],
            "appDescription": "Test App",
            "appServiceRequired": [],
            "appServiceOptional": [],
            "appServiceProduced": [],
            "appFeatureRequired": [],
            "appFeatureOptional": [],
            "transportDependencies": [],
            "appTrafficRule": [],
            "appDNSRule": [],
            "appLatency": {
                "timeUnit": 10,
                "latency": "ms"
            }
        }

        # add
        # {
        #  'appTrafficRule': [],
        #  'appSoftVersion': '0.1',
        #  'appDVersion': '1',
        #  'appFeatureRequired': [],
        #  'appServiceProduced': [],
        #  'appProvider': 'ETSI',
        #  'appLatency': {'latency': 'ms', 'timeUnit': 10},a
        #  'appDNSRule': [],
        #  'mecVersion': ['1', '2'],
        #  'appName': 'TestApp',
        #  'appDId': 'App123',
        #  'transportDependencies': [],
        #  'appDescription': 'Test App',
        #  'appServiceRequired': [],
        #  'appServiceOptional': [],
        #  'appFeatureOptional': []
        # }

        # get
        # [
        #   {'appTrafficRule': [],
        #    'appServiceProduced': [],
        #     'appDNSRule': [],
        #     'appName': 'TestApp',
        #     'appDId': 'App123',
        #     'appProvider': 'ETSI',
        #     'state': 'ACTIVE',
        #     'appInstanceId': 'd8f659a9-5864-426d-b3a6-76cf866201c6',
        #     'softVersion': '0.1'}
        # ]

        mm1 = Mm1()
        res = mm1.applications.add(plid, appd)

        self.assertEqual(res['ApplicationInfo']['appDId'], appd['appDId'])
        self.assertEqual(mm1.applications.get(plid, res['ApplicationInfo']['appInstanceId']), res)
        self.assertEqual(mm1.applications.list(plid)['ApplicationInfo'], [res['ApplicationInfo']])

        # appd = {
        #     "appDId": "App123",
        #     "appName": "TestApp",
        #     "appProvider": "ETSI",
        #     "appSoftVersion": "1.1",
        #     "appDVersion":"1",
        #     "mecVersion": ["1", "2"],
        #     "appDescription": "Test App",
        #     "appServiceRequired": [],
        #     "appServiceOptional": [],
        #     "appServiceProduced": [],
        #     "appFeatureRequired": [],
        #     "appFeatureOptional": [],
        #     "transportDependencies": [],
        #     "appTrafficRule": [],
        #     "appDNSRule": [],
        #     "latency": {
        #         "time_unit": 10,
        #         "latency": "ms"
        #     }
        # }

        # mm1.applications.update(updated_appd['id'], updated_appd)
        # self.assertEqual(mm1.applications.get(updated_appd['id']), updated_appd)
        # self.assertEqual(mm1.applications.list(), [updated_appd])

        mm1.applications.remove(plid, res['ApplicationInfo']['appInstanceId'])
        self.assertEqual(mm1.applications.list(plid), {'ApplicationInfo': []})
        self.assertRaises(ValueError, mm1.applications.get, plid, res['ApplicationInfo']['appInstanceId'])
