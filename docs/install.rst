Installation
============

You can install ``yaml4rst`` by invoking the following commands:

.. code-block:: bash

   gpg --recv-keys 'C505 B5C9 3B0D B3D3 38A1  B600 5FE9 2C12 EE88 E1F0'
   mkdir --parent /tmp/yaml4rst && cd /tmp/yaml4rst
   wget -r -nd -l 1 https://pypi.python.org/pypi/yaml4rst --accept-regex '^https://(test)?pypi\.python\.org/packages/.*\.whl.*'
   current_release="$(find . -type f -name '*.whl' | sort | tail -n 1)"
   gpg -v "${current_release}.asc" && pip3 install "${current_release}"

Refer to `Verifying PyPI and Conda Packages`_ for more details.

Or if you feel lazy and agree that `pip/issues/1035 <https://github.com/pypa/pip/issues/1035>`_
should be fixed you can also install ``yaml4rst`` like this:

.. code-block:: bash

   pip3 install yaml4rst

.. _Verifying PyPI and Conda Packages: http://stuartmumford.uk/blog/verifying-pypi-and-conda-packages.html
