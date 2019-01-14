def get_bridge_names_from_output_string(output):  # todo: last item is empty-> delete
    rows = output.split('\n')
    table = [row.split('\t') for row in rows]
    bridges_names = [item[0] for item in table]
    return bridges_names[1:]  # pop name of the table


def get_bridge_names_from_instance_networks(instance_networks):
    return [network['br_name'] for network in instance_networks]
