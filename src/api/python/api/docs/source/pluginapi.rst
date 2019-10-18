============
Plugin API
============


Eclipse fog05 Plugin API

Plugin
------
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


RuntimePluginFDU
----------------
.. autoclass:: fog05.interfaces.RuntimePluginFDU.RuntimePluginFDU
    :members: wait_destination_ready, wait_dependencies, write_fdu_error, update_fdu_status, get_local_instances, start_runtime, stop_runtime, get_fdus, define_fdu, undefine_fdu, run_fdu, stop_fdu, migrate_fdu, before_migrate_fdu_actions, after_migrate_fdu_actions, scale_fdu, pause_fdu, resume_fdu, configure_fdu, clean_fdu, is_uuid

