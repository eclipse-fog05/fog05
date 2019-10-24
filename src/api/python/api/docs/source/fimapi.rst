============
FIM Client API
============


Eclipse fog05 FIM Client API


FIMAPI
--------------
.. autoclass:: fog05.fimapi.FIMAPI
    :members: descriptor, node, plugin, network, fdu, image, flavor

Descriptor
----------
.. autoclass:: fog05.fimapi.FIMAPI.Descriptor
    :members:

Node
----
.. autoclass:: fog05.fimapi.FIMAPI.Node
    :members:

Plugin
------
.. autoclass:: fog05.fimapi.FIMAPI.Plugin
    :members:

Network
-------
.. autoclass:: fog05.fimapi.FIMAPI.Plugin
    :members:

FDUAPI
------
.. autoclass:: fog05.fimapi.FIMAPI.FDUAPI
    :members:

Image
-----
.. autoclass:: fog05.fimapi.FIMAPI.Image
    :members:


Flavor
------
.. autoclass:: fog05.fimapi.FIMAPI.Flavor
    :members:


Plugin API
----------
.. autoclass:: fog05.interfaces.Plugin.Plugin
    :members: get_nm_plugin, get_os_plugin, get_agent, get_local_mgmt_address, get_version


OS
------
.. autoclass:: fog05.interfaces.Plugin.OS
    :members:

NM
------
.. autoclass:: fog05.interfaces.Plugin.OS
    :members:

Agent
------
.. autoclass:: fog05.interfaces.Plugin.Agent
    :members: