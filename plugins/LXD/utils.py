def get_bridge_names_from_instance_networks(instance_networks):
    return [network['br_name'] for network in instance_networks]
