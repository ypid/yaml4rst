Changelog
=========

.. include:: includes/all.rst

This project adheres to `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`__
and `human-readable changelog <http://keepachangelog.com/en/0.3.0/>`__.


`yaml4rst master`_ - unreleased
-------------------------------

.. _yaml4rst master: https://github.com/ypid/yaml4rst/compare/v0.1.5...master


`yaml4rst v0.1.5`_ - 2017-03-16
-------------------------------

.. _yaml4rst v0.1.5: https://github.com/ypid/yaml4rst/compare/v0.1.4...v0.1.5

Fixed
~~~~~

- Fix RST section level detection for folded sections. [ypid_]

- End fold started by an unfolded RST section when a new RST section with the
  same section level begins instead of including the following RST section in
  the fold. [ypid_]


`yaml4rst v0.1.4`_ - 2017-02-21
-------------------------------

.. _yaml4rst v0.1.4: https://github.com/ypid/yaml4rst/compare/v0.1.3...v0.1.4

Security
~~~~~~~~

- The default ``yaml.load`` method from PyYAML which is used to validate the input YAML file is unsafe.
  As a result ``yaml4rst`` would have executed arbitrary code given in the YAML input file.

  Refer to the issue `Make load safe_load <https://github.com/yaml/pyyaml/issues/5>`_.
  This has been fixed by switching to ``yaml.safe_load``. [ypid_]


`yaml4rst v0.1.3`_ - 2017-02-14
-------------------------------

.. _yaml4rst v0.1.3: https://github.com/ypid/yaml4rst/compare/v0.1.2...v0.1.3

Changed
~~~~~~~

- Make the FIXME note which yaml4rst adds for missing variable comments more
  precise. [ypid_]

Fixed
~~~~~

- Fix YAML block detection which lead to wrong indention of closing folds. [ypid_]


`yaml4rst v0.1.2`_ - 2016-11-18
-------------------------------

.. _yaml4rst v0.1.2: https://github.com/ypid/yaml4rst/compare/v0.1.1...v0.1.2

Fixed
~~~~~

- Python packaging which previously included and installed the unit tests as
  separate "tests" Python package.
  Now the built distribution release (Wheel) only contains the actual Python package
  "yaml4rst" without the unit tests. Checkout the source distribution or the
  git repository for hacking on the project.
  Thanks very much to ganto_ for reporting and providing a patch! [ypid_]


`yaml4rst v0.1.1`_ - 2016-11-05
-------------------------------

.. _yaml4rst v0.1.1: https://github.com/ypid/yaml4rst/compare/v0.1.0...v0.1.1

Fixed
~~~~~

- Fix legacy reST section detection when heading is directly follows by a comment. [ypid_]

- Fix YAML block detection which lead to wrong indention of closing folds. [ypid_]


yaml4rst v0.1.0 - 2016-10-28
----------------------------

Added
~~~~~

- Initial coding and design. [ypid_]
