# Eclipse fog05

Eclipse fog05 allows the end-to-end management of compute, storage,
networking and I/O fabric in the Edge and Fog Environment.
Instead of relying on a centralized architecture (like cloud-management-systems)
it is based on a decentralized architecture.

Eclipse fog05 allows users to manage and deploy different types of applications,
packaged as containers, VMs, binaries and so on. This possibility is achieved
thanks to Eclipse fog05 plugin architecture.


More specifically, Eclipse fog05 is a Fog Infrastructure-as-a-Service solution
composed by two major components:

* The Fog Orchestration Engine (FOrcE)
* The Fog Infrastructure Manager (FIM)

These components provides the abstractions to deploy your applications in the
Fog and Edge environment.

## Unified abstractions

Common API and information model for management.
Eclipse fog05 provides an unified API for the management of the virtualization infrastructure.

### Operating System Plugins
Eclipse fog05 can run on different operating systems, it just need the
right OS Plugin.


### Networking Plugins
Eclipse fog05 can manage networking fabrics for which a Networking plugin is
present.

## Heterogenous applications

Support of heterogenous runtimes, hypervisors and networking.
Deploy heterogenous applications composed by VMs, containers, ROS2, native applications.


### Runtime Plugins
Eclipse fog05 can manage and open-ended set of hypervisors and container
technologies for which a Runtime Plugin was implemented.

### Single Descriptor
Eclipse fog05 allows you to define your application in a single descriptor.
No matters if it is composed by heterogeneous components.


## Lightweight

Eclipse fog05 is designed to be deployed from big servers to micro-controllers.

### Decentralized state

Because Eclipse fog05 uses [YAKS](http://www.yaks.is/) for location-transparency state access and management.
It can be deployed on resource constrained devices and leverage other nodes for state management.

### Modular

Eclipse fog05 is built with a plugin architecture and his components can be deployed separately.

## Example

A basic example of an LXD container descriptor that can be deployed by Eclipse fog05

```json
{
    "id": "lxd_example_fdu",
    "name": "test_1",
    "computation_requirements": {
        "cpu_arch": "x86_64",
        "cpu_min_freq": 0,
        "cpu_min_count": 1,
        "ram_size_mb": 128.0,
        "storage_size_gb": 5.0
    },
    "image": {
        "uri": "lxd://alpine/edge",
        "checksum": "",
        "format": ""
    },
    "storage": [],
    "hypervisor": "LXD",
    "migration_kind": "COLD",
    "interfaces": [
        {
            "name": "eth0",
            "is_mgmt": false,
            "if_type": "INTERNAL",
            "mac_address": "be:ef:be:ef:00:01",
            "virtual_interface": {
                "intf_type": "BRIDGED",
                "vpci": "lxdbr0",
                "bandwidth": 10
            }
        }
    ],
    "io_ports": [],
    "connection_points": [],
    "depends_on": []
}
}
```

More examples can be found [here](https://github.com/eclipse-fog05/examples).