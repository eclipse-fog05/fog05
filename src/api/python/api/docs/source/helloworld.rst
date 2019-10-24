================
Getting Started
================

To kick off our tour of Eclipse fog05, we will start with the obligatory "hello world"
example.
This example will deploy a native compoent written in python that create a file and write "hello, world!" to the file.

Let's get started.

First, we write the python code.

.. code-block:: python

    import time

    with open('/tmp/fos_helloworld', 'a') as out:
        while True:
            out.write('Hello, world! It is {}\n'.format(time.time_ns()))
            time.sleep(2)

Let's save it as ``/tmp/fos_helloworld.py``

Next, we need to write the descriptor for this native component.
Let's call it ``fdu_helloworld.json``:


.. code-block:: json

    {
        "id": "helloword_fdu",
        "name": "helloworld",
        "computation_requirements": {
            "cpu_arch": "x86_64",
            "cpu_min_freq": 0,
            "cpu_min_count": 1,
            "ram_size_mb": 64.0,
            "storage_size_gb": 1.0
        },
        "command": {
            "binary": "python3",
            "args": ["/tmp/fos_helloworld.py"]
        },
        "hypervisor": "BARE",
        "migration_kind": "COLD",
        "storage": [],
        "depends_on": [],
        "interfaces": [],
        "io_ports": [],
        "connection_points": []
    }


Now if we suppose to have an Eclipse fog05 node in our localhost, we can
use the Eclipse fog05 Python FIM API to register and deploy this component.

Let's imagine that our descriptor was saved in our ``$HOME`` directory,
we can use this simple python script to deploy the "hello world" example

.. code-block:: python

    from fog05 import FIMAPI

    def read_file(filepath):
        with open(filepath, 'r') as f:
            data = f.read()
        return data

    n = '<our node id>'
    api = FIMAPI()
    desc = read_file('$HOME/fdu_helloworld.json')

    fduD = api.fdu.onboard(desc)
    print ('fdu_id : {}'.format(fduD.get_uuid()))
    time.sleep(2)
    inst_info = api.fdu.instantiate(fdu_id, n)
    print ('Instance ID : {}'.format(inst_info.get_uuid()))

    input('Press enter to terminate')

    api.fdu.terminate(inst_info.get_uuid())

    api.close()
    exit(0)


We can save this file as ``fos_deploy.py`` and run it using ``python3``

::

    $ python3 fos_deploy.py
    fdu_id: 6f52866c-0e69-4075-9ee1-b24c3b8a0969
    Instance ID: 4ac683a6-7fee-4481-af2b-c7ca6c5bdf9c
    Press enter to terminate
    ...
    $

Before the termination you can run `c`at /tmp/fos_helloworld`` and you shold get something similar to

::

    $ cat /tmp/fos_helloworld
    Hello, world! It is 1571134486584032000
    Hello, world! It is 1571134488586158000
    Hello, world! It is 1571134490586510000
    Hello, world! It is 1571134492586757000
    Hello, world! It is 1571134494589501000
    Hello, world! It is 1571134496589933000

