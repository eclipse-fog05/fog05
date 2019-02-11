import json
import os
import uuid

from fog05.interfaces.NetworkPlugin import NetworkPlugin, BridgeNotExistingException, \
    InterfaceNotExistingException


class OVS(NetworkPlugin):
    def __init__(self, name, version, agent, plugin_uuid, configuration={}):
        super(OVS, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.interfaces_map = {}
        self.bridges_map = {}
        self.network_map = {}
        self.configuration = configuration
        self.agent.logger.info('__init__()', ' Hello from OVS Plugin')
        self.BASE_DIR = os.path.join(self.agent.base_path, 'OVS')
        self.DHCP_DIR = 'dhcp'
        self.HOME = 'network/{}'.format(self.uuid)
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.overlay_interface = None

        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.DHCP_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DHCP_DIR))
        else:
            self.agent.get_os_plugin().create_dir(self.BASE_DIR)
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DHCP_DIR))

        if self.configuration.get('data_subnet'):
            cird = self.configuration.get('data_subnet')

            data = json.loads(self.agent.astore.get(self.agent.ahome))
            for n in data.get('network'):
                intf_cird = self.__ip_mask_to_cird(
                    n.get('inft_configuration').get('ipv4_address'),
                    n.get('inft_configuration').get('ipv4_netmask')
                )
                if cird == intf_cird:
                    self.overlay_interface = n.get('intf_name')

        '''
        should listen on:

        - //dfos/<sys-id>/<node-id>/network/<myuuid>/networks/**
        - //dfos/<sys-id>/<node-id>/network/<myuuid>/bridges/**
        - //dfos/<sys-id>/<node-id>/network/<myuuid>/interfaces/**

        '''

        uri = '{}/{}/networks/**'.format(self.agent.dhome, self.HOME)
        self.agent.dstore.observe(uri, self.__react_to_cache_networks)
        self.agent.logger.info(
            'startRuntime()', ' bridge-utils Plugin - Observing {}'.format(uri))

    def create_virtual_bridge(self, name, uuid):
        command = 'sudo ovs-vsctl add-br {}'.format(name)
        self.execute(command)
        self.bridges_map.update({uuid: name})
        return uuid, name

    def delete_virtual_bridge(self, br_uuid):
        bridge_name = self.get_bridge_name(br_uuid)
        command = 'sudo ovs-vsctl del-br {}'.format(bridge_name)
        self.execute(command)

    def assign_interface_to_virtual_bridge(self, bridge_uuid, interface_uuid):
        pass

    def create_virtual_interface(self, name, uuid):
        command = 'sudo ip link add dev {} type veth peer name {}-peer'.format(name)
        self.execute(command)
        self.interfaces_map.update({uuid:name})

    def delete_virtual_interface(self, intf_uuid):
        interface_name = self.interfaces_map.get(intf_uuid, None)
        if not interface_name:
            raise InterfaceNotExistingException('{} interface not exists'.format(intf_uuid))
        command = 'sudo ip link delete {}'.format(interface_name)
        self.execute(command)

    def set_controller(self, bridge_uuid, ip, port=6653, protocol='tcp'):
        bridge_name = self.get_bridge_name(bridge_uuid)
        command = 'sudo ovs-vsctl set-controller {} {}:{}:{}'.format(bridge_name, protocol, ip, str(port))
        self.execute(command)

    def del_controller(self, bridge_uuid):
        bridge_name = self.get_bridge_name(bridge_uuid)
        command = 'sudo ovs-vsctl del-controller {}'.format(bridge_name)
        self.execute(command)

    def set_fail_mode_secure(self, bridge_uuid):
        bridge_name = self.get_bridge_name(bridge_uuid)
        command = 'sudo ovs-vsctl set-fail-mode {} secure'.format(bridge_name)
        self.execute(command)

    def delete_fail_mode_secure(self, bridge_uuid):
        bridge_name = self.get_bridge_name(bridge_uuid)
        command = 'sudo ovs-vsctl del-fail-mode {}'.format(bridge_name)
        self.execute(command)

    def get_interface_name(self, interface_uuid):
        interface_name = self.interfaces_map.get(interface_uuid, None)
        if not interface_name:
            raise InterfaceNotExistingException('{} interface not exists'.format(interface_uuid))
        return interface_name

    def get_bridge_name(self, bridge_uuid):
        bridge_name = self.bridges_map.get(bridge_uuid, None)
        if not bridge_name:
            raise BridgeNotExistingException('{} bridge not exists'.format(bridge_uuid))
        return bridge_name

    def get_virtual_bridges_in_node(self):
        cmd = 'sudo ovs-vsctl show' #TODO: could be a better command?
        output = self.agent.get_os_plugin().execute_command(cmd)
        return self.get_bridge_names_from_command_output(output)

    def create_bridges_if_not_exist(self, expected_bridges):
        current_bridges = self.get_virtual_bridges_in_node()
        for bridge in expected_bridges:
            if bridge not in current_bridges:
                self.create_virtual_bridge(bridge, '{}'.format(uuid.uuid4()))

    def get_bridge_names_from_command_output(self, output):
        pattern = 'Bridge'
        output = output.split('\n')
        return [self.get_bridge_name_from_row(item) for item in output if self.row_has_bridge_name(item)]

    def get_bridge_name_from_row(self, row):
        return row.split('"')[1]

    def row_has_bridge_name(self, row):
        return True if row.find('Bridge')>-1 else False

    def execute(self, command):
        return self.agent.get_os_plugin().execute_command(command)

    def __react_to_cache_networks(self, key, value, v):
        self.agent.logger.info('__react_to_cache_networks()',
                               ' BRCTL Plugin - React to to URI: {} Value: {} Version: {}'.format(key, value, v))
        uuid = key.split('/')[-1]
        value = json.loads(value)
        action = value.get('status')
        react_func = self.__react(action)
        if action == 'undefine':
            self.delete_virtual_network(uuid)
        if react_func is not None and action != 'undefine':
            react_func(**value)