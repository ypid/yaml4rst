Installation
============

Latest release
--------------

You can install ``yaml4rst`` by invoking the following commands:

.. code-block:: bash

   gpg --recv-keys 'C505 B5C9 3B0D B3D3 38A1  B600 5FE9 2C12 EE88 E1F0'
   mkdir --parent /tmp/yaml4rst && cd /tmp/yaml4rst
   wget -r -nd -l 1 https://pypi.python.org/pypi/yaml4rst --accept-regex '^https://(test)?pypi\.python\.org/packages/.*\.whl.*'
   current_release="$(find . -type f -name '*.whl' | sort | tail -n 1)"
   gpg -v "${current_release}.asc" && pip3 install "${current_release}"

Refer to `Verifying PyPI and Conda Packages`_ for more details. Note that this might pull down dependencies in an unauthenticated way! You might want to install the dependencies yourself beforehand.

Or if you feel lazy and agree that `pip/issues/1035 <https://github.com/pypa/pip/issues/1035>`_
should be fixed you can also install ``yaml4rst`` like this:

.. code-block:: bash

   pip3 install yaml4rst

.. _Verifying PyPI and Conda Packages: http://stuartmumford.uk/blog/verifying-pypi-and-conda-packages.html

Development version
-------------------

If you want to be more on the bleeding edge of ``yaml4rst`` development
consider cloning the ``git`` repository and installing from it:

.. code-block:: bash

   gpg --recv-keys 'EF96 BC32 AC57 CFC7 2DF0  1D8C 489A 4D5E C353 C98A'
   git clone https://github.com/ypid/yaml4rst.git
   cd yaml4rst && git verify-commit HEAD
   echo 'Check if the HEAD commit has a good signature and only proceed in that case!' && read -r fnord
   echo 'Then chose one of the commands below to install yaml4rst and its dependencies:'
   pip3 install .
   ./setup.py develop --user
   ./setup.py install --user
   ./setup.py install
