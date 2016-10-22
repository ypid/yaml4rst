# -*- coding: utf-8 -*-

"""
Default configuration of yaml4rst
"""

from __future__ import absolute_import, division, print_function

import os

__all__ = ['DEFAULTS']


DEFAULTS = {
    'preset': 'debops/ansible',
    'template_path': os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'templates',
    ),
    'config': {
        'wanted_empty_lines_between_items': 2,
        'closing_fold_format_spec': '{:>72}',
        'add_string_for_missing_comment': 'FIXME',
    },
}
