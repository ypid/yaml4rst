# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import textwrap

from nose.tools import assert_equal, assert_not_equal

from yaml4rst.helpers import get_first_match, list_index, get_last_index, get_last_match, strip_list


def test_list_index():
    data = ['first', 'second', 'third']
    assert_equal(0, list_index(data, 'first'))
    assert_equal(2, list_index(data, 'third'))
    assert_equal(None, list_index(data, 'none'))
    assert_equal(23, list_index(data, 'none', fallback=23))


def test_get_last_index():
    data = ['first', 'second', 'third', 'first']
    assert_equal(3, get_last_index(data, ['first', 'third']))
    assert_equal(3, get_last_index(data, ['third', 'first']))
    assert_equal(3, get_last_index(data, ['first']))
    assert_equal(1, get_last_index(data, ['second']))
    assert_equal(2, get_last_index(data, ['third', 'second']))
    assert_equal(2, get_last_index(data, ['third']))
    assert_equal(None, get_last_index(data, ['none']))
    assert_equal(23, get_last_index(data, ['none'], fallback=23))

    data = textwrap.dedent("""
        # .. envvar:: don’t match

        # .. envvar:: don’t match

        # .. envvar:: match
        #
        # List of base packages to install.
    """).strip().split('\n')
    assert_equal(3, get_last_index(data, ['']))


def test_get_first_match():
    data = ['first', 'second', 'third']
    assert_equal(None, get_first_match(r'none', data))
    assert_equal('first', get_first_match(r'first', data).group())
    assert_equal('first', get_first_match(r'f.*', data).group())
    assert_equal(0, get_first_match(r'first', data, ind_offset=0))
    assert_equal(1, get_first_match(r'first', data, ind_offset=1))
    assert_equal(-1, get_first_match(r'first', data, ind_offset=-1))
    assert_equal(0, get_first_match(r'second', data, ind_offset=-1))
    assert_equal(1, get_first_match(r'second', data, ind_offset=0))
    assert_equal(None, get_first_match(r'third', data, ind_offset=0, break_pattern=r'second'))
    assert_equal(0, get_first_match(r'first', data, ind_offset=0, break_pattern=r'second'))


def test_get_first_match_limit_pattern():
    input_lines = textwrap.dedent("""
        # test [[[

        # ]]]

        # 3
    """).strip().split('\n')

    closing_fold = get_first_match(
        r'^\s*#.*\]\]\]$',
        input_lines,
        ind_offset=0,
        limit_pattern=r'^(?:(?:# ).*|)?$',
    )
    assert_equal(2, closing_fold)


def test_get_last_match():
    data = ['first', 'second', 'third']
    assert_equal('first', get_last_match(r'first', data).group())
    assert_equal('first', get_last_match(r'f.*', data).group())
    assert_equal(-3, get_last_match(r'first', data, ind_offset=0))
    assert_equal(1, get_last_match(r'first', data, ind_offset=4))
    assert_equal(None, get_last_match(r'none', data, ind_offset=4))


def test_get_last_match_comments():
    data = textwrap.dedent("""
        # .. envvar:: don’t match

        # .. envvar:: match
        #
        # List of base packages to install.
    """).strip().split('\n')
    assert_not_equal(None, get_last_match(r'# \.\. envvar:: don’t match', data))
    assert_equal(None, get_last_match(r'# \.\. envvar:: don’t match', data, limit_pattern=r'^#'))


def test_strip_list():
    input_lines = textwrap.dedent("""

        # 1
        # 2

        # 3

    """).split('\n')

    assert_equal(
        ['# 1', '# 2', '', '# 3'],
        strip_list(input_lines),
    )

    input_lines = textwrap.dedent("""
        # 1
        # 2

        # 3
    """).strip().split('\n')

    assert_equal(input_lines, strip_list(input_lines))
    assert_equal(input_lines, strip_list([''] + input_lines))
    assert_equal(input_lines, strip_list(input_lines + ['']))

    input_lines = textwrap.dedent("""
        # 1
        # 2
        # 3
    """).strip().split('\n')

    assert_equal(input_lines, strip_list(input_lines))
    assert_equal(input_lines, strip_list([''] + input_lines))
    assert_equal(input_lines, strip_list(input_lines + ['']))
