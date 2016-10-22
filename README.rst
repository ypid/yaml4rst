yaml4rst introduction
=====================

| |Build Status| |Read The Docs| |CII Best Practices| |Code Coverage Status|
| |Version| |License| |Python versions| |dev status| |pypi monthly downloads|

yaml4rst is a linting/checking/reformatting tool for YAML files documented with
inline RST which goes hand in hand with yaml2rst_.

It has been written to help with keeping the ``defaults/main.yml`` file in
Ansible roles, maintained in DebOps_, up-to-date and to assist with writing or
including new roles. DebOps uses Sphinx to generate Ansible role documentation
which also includes the default role variables. Refer to `debops/docs`_ for
details.

Usage
-----

The typical use case for this program is to improve the defaults YAML file of
Ansible roles.

The recommended way to do this is to commit all your changes in the repository
of the role, then run:

.. code-block:: bash

   yaml4rst -e 'ansible_full_role_name=ROLE_OWNER.ROLE_NAME' defaults/main.yml -i

from the root of the role repository. Be sure to replace
``ROLE_OWNER.ROLE_NAME`` with the particular Ansible role name.

This will check and reformat the ``defaults/main.yml`` file in place.

Now you can check the reformatted file with a diffing/editing tool of your choosing
and fix any warning which ``yaml4rst`` might have emitted.

Refer to ``input_files`` and ``output_files`` in the `tests directory`_ for
automatically tested examples of input and output files.

Note that for continues usage yaml4rst is invoked from debops-optimize_ when
yaml4rst is installed so you might want to try debops-optimize_.

Features
--------

.. Redundant. Places: /README.rst and /yaml4rst/reformatter.py

Checks for:

* Reasonable variable namespace
* Undocumented variables

Automatically fixes:

* RST sections which are not folds
* Undocumented variables (adds a FIXME for the user)
* Documented variables which are not folds
* YAML documents without a defined header
* Spacing between variables and sections

Known limitations
-----------------

* Does not handle folds with implicit level and missing closing fold marker.

  Status: Should be doable but currently not needed nor implemented. A
  ``NotImplementedError`` exception is thrown which causes the CLI program to
  terminate immediately with an error and reference to this section.

  As workaround just strip out the opening folds with your favorite editor as
  ``yaml4rst`` will add missing folds for sections and variables anyway.
  Refer to the Makefile_ (``prepare-real-data`` target) where such a workaround
  is used for integration testing. Note that this is not perfect as can be seen
  on the debops.apt_install test case.

Authors
-------

* `Robin Schneider <https://me.ypid.de/>`_

License
-------

`GNU Affero General Public License v3 (AGPL-3.0)`_

.. _GNU Affero General Public License v3 (AGPL-3.0): https://tldrlegal.com/license/gnu-affero-general-public-license-v3-%28agpl-3.0%29
.. _DebOps: https://debops.org/
.. _debops/docs: https://github.com/debops/docs/
.. _yaml2rst: https://github.com/htgoebel/yaml2rst
.. _Makefile: https://github.com/ypid/yaml4rst/blob/master/Makefile
.. _tests directory: https://github.com/ypid/yaml4rst/tree/master/tests
.. _debops-optimize: https://github.com/ypid/ypid-ansible-common/blob/master/bin/debops-optimize

.. |Build Status| image:: https://travis-ci.org/ypid/yaml4rst.svg
   :target: https://travis-ci.org/ypid/yaml4rst

.. |Read the Docs| image:: https://readthedocs.org/projects/yaml4rst/badge/?version=latest
   :target: https://yaml4rst.readthedocs.io/en/latest/

.. |CII Best Practices| image:: https://bestpractices.coreinfrastructure.org/projects/457/badge
   :target: https://bestpractices.coreinfrastructure.org/projects/457

.. No need to register at https://coveralls.io or something. 100% is just enforced in the CI build.
.. |Code Coverage Status| image:: https://img.shields.io/badge/coverage-100%-brightgreen.svg
   :target: https://travis-ci.org/ypid/yaml4rst

.. |Version| image:: https://img.shields.io/pypi/v/yaml4rst.svg
   :target: https://pypi.python.org/pypi/yaml4rst

.. |License| image:: https://img.shields.io/pypi/l/yaml4rst.svg
   :target: https://pypi.python.org/pypi/yaml4rst

.. |Python versions| image:: https://img.shields.io/pypi/pyversions/yaml4rst.svg
   :target: https://pypi.python.org/pypi/yaml4rst

.. |dev status| image:: https://img.shields.io/pypi/status/yaml4rst.svg
   :target: https://pypi.python.org/pypi/yaml4rst

.. |pypi monthly downloads| image:: https://img.shields.io/pypi/dm/yaml4rst.svg
   :target: https://pypi.python.org/pypi/yaml4rst
