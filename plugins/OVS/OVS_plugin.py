import os

from src.python.fog05.interfaces.NetworkPlugin import NetworkPlugin, BridgeNotExistingException, \
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
        #TODO

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

    def create_bridges_if_not_exist(self, expected_bridges):
        current_bridges = self.get_virtual_bridges_in_node()
        cmd = 'sudo sh -c \'ovs-vsctl show | grep Bridge\''
        output = self.agent.get_os_plugin().execute_command(cmd)
        return self.get_bridge_names_from_command_output(output)

    def get_bridge_names_from_command_output(self, output):
        raise NotImplementedError

    def execute(self, command):
        return self.agent.get_os_plugin().execute_command(command)
