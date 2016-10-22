Configuration
=============

``ansible_full_role_name``

  Ansible role name. Example: ``debops.apt``.

  No default.

``closing_fold_format_spec``

  Format string in `str.format
  <https://docs.python.org/3/library/string.html#string-formatting>`_ syntax
  used defining how closing folds should look like.

  Defaults to:

  .. program-output:: python -c 'from yaml4rst.defaults import DEFAULTS; print(DEFAULTS["config"]["closing_fold_format_spec"])'

``wanted_empty_lines_between_items``

  Number of empty lines wanted between sections and/or variables.
  Note that the closing folds are by default space indented and also count as
  "empty lines" for that matter.

  Defaults to:

  .. program-output:: python -c 'from yaml4rst.defaults import DEFAULTS; print(DEFAULTS["config"]["wanted_empty_lines_between_items"])'

``add_string_for_missing_comment``

  The string to add when a undocumented variable/section was found.

  Defaults to:

  .. program-output:: python -c 'from yaml4rst.defaults import DEFAULTS; print(DEFAULTS["config"]["add_string_for_missing_comment"])'
