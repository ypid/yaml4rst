# -*- coding: utf-8 -*-

"""
Helper functions of yaml4rst
"""

from __future__ import absolute_import, division, print_function

import re
import logging

LOG = logging.getLogger(__name__)


def list_index(input_list, elem, fallback=None):
    try:
        i = input_list.index(elem)
    except ValueError:
        i = fallback

    return i


def get_last_index(input_list, search_elems, fallback=None):
    for i, string in reversed(list(enumerate(input_list))):

        if string in search_elems:
            return i

    return fallback


def get_first_match(pattern, strings, ind_offset=None, limit_pattern=None, break_pattern=None, match=True):
    #  LOG.debug('search {} in {}'.format(pattern, strings))
    for string_ind, string in enumerate(strings):
        #  LOG.debug('string: {}'.format(string))

        _re = re.search(pattern, string)
        if (_re is not None) == match:
            if ind_offset is not None:
                return string_ind + ind_offset
            else:
                return _re
        if limit_pattern is not None and not re.search(limit_pattern, string):
            #  LOG.debug("Limit pattern matched")
            return None
        if break_pattern is not None and re.search(break_pattern, string):
            return None
    return None


def get_last_match(pattern, strings, ind_offset=None, limit_pattern=None, match=True):
    if ind_offset is not None:
        ind = get_first_match(pattern, reversed(strings), ind_offset=0, limit_pattern=limit_pattern, match=match)
        if ind is None:
            return None
        else:
            return ind_offset - ind - 1
    else:
        return get_first_match(pattern, reversed(strings), limit_pattern=limit_pattern, match=match)


def insert_list(base_list, ind, add_list):
    for insert_item in reversed(add_list):
        base_list.insert(ind, insert_item)
    return ind + len(add_list) - 1


def strip_list(input_list):
    # before, in, after
    state = 'before'
    prev_state = 'before'
    stripped_list = []

    tmp_list = []
    for item in input_list:
        if item == '':
            if state == 'in':
                state = 'after'
                tmp_list = []
        else:
            state = 'in'

        if state == 'in':
            if prev_state == 'after':
                stripped_list.extend(tmp_list)
            stripped_list.append(item)

        tmp_list.append(item)
        prev_state = state

    return stripped_list
