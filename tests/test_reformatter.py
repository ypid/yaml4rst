# -*- coding: utf-8 -*-
# vim: foldmarker=[[[,]]]:foldmethod=marker

from __future__ import absolute_import, division, print_function

import os
import textwrap
import pprint
import logging
from copy import deepcopy
from io import StringIO
import unittest
# Python 2 does not yet have mock which was a separate package back then.

from nose.tools import assert_equal, assert_not_equal, assert_raises_regexp
from testfixtures import log_capture, tempdir

from yaml4rst.reformatter import YamlRstReformatter, YamlRstReformatterError, LOG
from yaml4rst.defaults import DEFAULTS


class Test(unittest.TestCase):

    def setUp(self):
        self.r = YamlRstReformatter(
            config={
                'ansible_full_role_name': 'role_owner.role_name',
                'add_string_for_missing_comment': '',
            },
        )
        logging.getLogger().addHandler(logging.NullHandler())
        LOG.setLevel(logging.DEBUG)

    def tearDown(self):
        pass

    def test_auto_complete_config(self):
        config = {
            'ansible_full_role_name': 'role_owner.role_name',
        }
        self.r = YamlRstReformatter(
            config=deepcopy(config),
        )
        self.r._auto_complete_config()

        config.update(DEFAULTS['config'])
        config.update({
            'ansible_role_owner': 'role_owner',
            'ansible_role_name': 'role_name',
        })

        pprint.pprint(self.r._config)
        assert_equal(
            self.r._config,
            config,
        )

    def test_auto_complete_config_missing(self):
        self.r = YamlRstReformatter()
        self.r._auto_complete_config()

        assert_equal(
            self.r._config,
            DEFAULTS['config'],
        )

    @log_capture(level=logging.WARNING)
    def test_process_user_invalid_ansible_full_role_name(self, log):
        config = {
            'ansible_full_role_name': 'role_owner-role_name',
        }
        self.r = YamlRstReformatter(
            config=deepcopy(config),
        )

        pprint.pprint(self.r._config)
        config.update(DEFAULTS['config'])
        assert_equal(
            self.r._config,
            config,
        )
        print(log)
        log.check(
            (
                'yaml4rst.reformatter',
                'WARNING',
                "The config option 'ansible_full_role_name' has a invalid format."
                " Expected 'ROLE_OWNER.ROLE_NAME'. Got role_owner-role_name (no '.')."
            ),
        )

    @unittest.mock.patch('sys.stdout', new_callable=StringIO)
    @tempdir()
    def test_read_write_file(self, mock_stdout, d):
        file_path = os.path.join(d.path, 'main.yml')
        input_data = textwrap.dedent(u"""
            role_name__1: []

            role_name__2: []
        """).strip()

        d.write('main.yml', input_data, 'utf-8')
        self.r.read_file(file_path)
        assert_equal(input_data, self.r.get_content())
        self.r.write_file(file_path)
        assert_equal(mock_stdout.getvalue(), '')
        self.r.write_file('-')
        assert_equal(mock_stdout.getvalue(), self.r.get_content() + '\n')
        assert_equal(input_data, self.r.get_content())
        assert_equal(d.read('main.yml', 'utf-8'), input_data + '\n')

        self.r.reformat()
        assert_not_equal(input_data, self.r.get_content(), input_data)
        self.r.write_file(file_path)
        assert_not_equal(d.read('main.yml', 'utf-8'), input_data + '\n')
        assert_not_equal(input_data, self.r.get_content(), input_data)

    def test_get_rendered_template(self):
        expected_string = textwrap.dedent("""
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst
        """).strip()
        assert_equal(
            expected_string,
            self.r._get_rendered_template('defaults_header'),
        )
        self.r._update_header()
        pprint.pprint(self.r._lines)
        assert_equal(
            expected_string.split('\n') + [
                '',
                '',
                '                                                                   # ]]]'
            ],
            self.r._lines,
        )

    def test_update_header(self):
        expected_lines = textwrap.dedent("""
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst


            role_name__1: 'test'
                                                                               # ]]]
        """).strip().split('\n')

        # ----------------------------------
        self.r._lines = textwrap.dedent("""
            ---

            role_name__1: 'test'
        """).strip().split('\n')
        self.r._update_header()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_lines, self.r._lines)

        # ----------------------------------
        self.r._lines = textwrap.dedent("""
            ---
            role_name__1: 'test'
        """).strip().split('\n')
        self.r._update_header()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_lines, self.r._lines)

        # ----------------------------------
        self.r._lines = textwrap.dedent("""
            role_name__1: 'test'
        """).strip().split('\n')
        self.r._update_header()

        # ----------------------------------
        self.r._lines = textwrap.dedent("""
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst



            role_name__1: 'test'
                                                                               # ]]]
        """).strip().split('\n')
        self.r._update_header()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_lines, self.r._lines)

        # ----------------------------------
        self.r._lines = textwrap.dedent("""
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst
            #


            role_name__1: 'test'
                                                                               # ]]]
        """).strip().split('\n')
        self.r._update_header()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_lines, self.r._lines)

        # ----------------------------------
        self.r._update_header()
        assert_equal(expected_lines, self.r._lines)

    def test_update_header_empty(self):
        expected_lines = textwrap.dedent("""
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst


                                                                               # ]]]
        """).strip().split('\n')

        # ----------------------------------
        self.r._lines = []
        self.r._update_header()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_lines, self.r._lines)

        # ----------------------------------
        self.r._lines = ['---']
        self.r._update_header()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_lines, self.r._lines)

    def test_get_rendered_template_missing_vars(self):
        self.r = YamlRstReformatter()
        assert_raises_regexp(
            YamlRstReformatterError,
            r"^'ansible_full_role_name' is undefined\. Consider providing the variable as config option\.$",
            self.r._get_rendered_template,
            'defaults_header',
        )

    def test_get_line_fold_opening(self):
        assert_equal(
            {'change': 1, 'level': '', 'name': '.. envvar:: 1'},
            self.r._get_line_fold('# .. envvar:: 1 [[['),
        )

        assert_equal(
            {'change': 1, 'level': '', 'name': '.. envvar:: 1'},
            self.r._get_line_fold('# .. envvar:: 1 ((('),
        )

        assert_equal(
            {'change': 1, 'level': '', 'name': '.. envvar:: 1'},
            self.r._get_line_fold('# .. envvar:: 1 {{{'),
        )

        assert_equal(
            {'change': 1, 'level': '', 'name': 'section title'},
            self.r._get_line_fold('# section title [[['),
        )

    def test_get_line_fold_closing(self):
        assert_equal(
            {'change': -1, 'level': None, 'name': None},
            self.r._get_line_fold('# ]]]'),
        )

        assert_equal(
            {'change': -1, 'level': None, 'name': None},
            self.r._get_line_fold('# )))'),
        )

        assert_equal(
            {'change': -1, 'level': None, 'name': None},
            self.r._get_line_fold('# }}}'),
        )

    def test_get_line_fold_not_implemented_error(self):

        assert_raises_regexp(
            NotImplementedError,
            r"^Found explicit fold level\. See under known limitations in the docs\.$",
            self.r._get_line_fold,
            '# .. envvar:: 1 [[[1',
        )

        assert_raises_regexp(
            NotImplementedError,
            r"^Found explicit fold level\. See under known limitations in the docs\.$",
            self.r._get_line_fold,
            '# section [[[23',
        )

    def test_check_folds(self):
        self.r._lines = textwrap.dedent("""
            # .. envvar:: 1 [[[
            #
            1: []
                                                                               # ]]]
            # .. envvar:: 2 [[[
            #
            2: []
                                                                               # ]]]
        """).strip().split('\n')
        self.r._check_folds()
        self.r._check_folds(lines=self.r._lines)

    def test_check_folds_problem(self):
        self.r._lines = textwrap.dedent("""
            # .. envvar:: 1 [[[
            #
            1: []
                                                                               # ]]]
            # .. envvar:: 2 [ [[
            #
            2: []
                                                                               # ]]]
        """).strip().split('\n')
        assert_raises_regexp(
            YamlRstReformatterError,
            r'^1 additional closing fold marker\.$',
            self.r._check_folds,
        )

    @log_capture(level=logging.WARNING)
    def test_check_folds_one_unclosed(self, log):
        self.r._lines = textwrap.dedent("""
            # .. envvar:: 1 [[[
            #
            1: []
                                                                               # ]]]
            # .. envvar:: 2 [[[
            #
            2: []
        """).strip().split('\n')
        self.r._check_folds(fatal=False)
        log.check(
            ('yaml4rst.reformatter', 'WARNING', '1 fold is unclosed.'),
        )

    @log_capture(level=logging.WARNING)
    def test_check_folds_multiple_unclosed(self, log):
        self.r._lines = textwrap.dedent("""
            # .. envvar:: 1 [[[
            # .. envvar:: 2 [[[
        """).strip().split('\n')
        self.r._check_folds(fatal=False)
        log.check(
            ('yaml4rst.reformatter', 'WARNING', '2 folds are unclosed.'),
        )

    @log_capture(level=logging.WARNING)
    def test_check_folds_one_unopened(self, log):
        self.r._lines = textwrap.dedent("""
            #
            1: []
                                                                               # ]]]
            #
            2: []
        """).strip().split('\n')
        self.r._check_folds(fatal=False)
        log.check(
            ('yaml4rst.reformatter', 'WARNING', '1 additional closing fold marker.'),
        )

    @log_capture(level=logging.WARNING)
    def test_check_folds_multiple_unopened(self, log):
        self.r._lines = textwrap.dedent("""
                                                                               # ]]]
            # ]]]
            # [[[
            # ]]]
            # ]]]
        """).strip().split('\n')
        self.r._check_folds(fatal=False)
        log.check(
            ('yaml4rst.reformatter', 'WARNING', '3 additional closing fold markers.'),
        )

    def test_add_folds_to_yaml_var_rst_docs(self):
        self.r._lines = textwrap.dedent("""
            # .. envvar:: role_name__I_failed_again_group_devices
            #
            # Host group definition list of encrypted filesystems.
            role_name__group_devices: []


            # .. envvar:: role_name__host_devices
            #
            # Host definition list of encrypted filesystems.
            role_name__host_devices: []
        """).strip().split('\n')
        self.r.reformat()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent("""
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__group_devices [[[
                #
                # Host group definition list of encrypted filesystems.
                role_name__group_devices: []

                                                                                   # ]]]
                # .. envvar:: role_name__host_devices [[[
                #
                # Host definition list of encrypted filesystems.
                role_name__host_devices: []
                                                                                   # ]]]
                                                                                   # ]]]
                """).strip().split('\n'),
            self.r._lines,
        )

    def test_add_folds_to_yaml_var_rst_docs_merge(self):
        self.r._lines = textwrap.dedent("""
            # Host group definition list of encrypted filesystems.
            role_name__group_devices: []


            # Host definition list of encrypted filesystems.
            role_name__host_devices: []

            # something
            role_name__host: []
        """).strip().split('\n')
        self.r.reformat()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent("""
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__group_devices [[[
                #
                # Host group definition list of encrypted filesystems.
                role_name__group_devices: []

                                                                                   # ]]]
                # .. envvar:: role_name__host_devices [[[
                #
                # Host definition list of encrypted filesystems.
                role_name__host_devices: []

                                                                                   # ]]]
                # .. envvar:: role_name__host [[[
                #
                # something
                role_name__host: []
                                                                                   # ]]]
                                                                                   # ]]]
                """).strip().split('\n'),
            self.r._lines,
        )

    @log_capture(level=logging.WARNING)
    def test_check_var_names(self, log):
        self.r._lines = textwrap.dedent("""
            wrong_namespace_something: []

            role_name__host_devices: []
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)
        self.r._reformat_variables(self.r._sections)
        self.r._check_var_names()

        log.check(
            (
                'yaml4rst.reformatter',
                'WARNING',
                "The variable 'wrong_namespace_something' is outside of the 'role_name' namespace."
                " All variables of a Ansible role should really be in the namespace of the Ansible role!"
                " Consider prefixing the variable with 'role_name_'"
                " or consider to follow the DebOps prefix convention with 'role_name__'"
                " which also works nicely with role dependencies."
            ),
        )

    def test_check_var_names_config_missing(self):
        self.r._config = {}
        self.r._check_var_names()

    def test_fix_closing_folds_new_lines(self):
        self.r._lines = textwrap.dedent("""
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst


            # .. envvar:: role_name__1 [[[
            #
            role_name__1: []


                                                                               # ]]]

            # .. envvar:: role_name__2 [[[
            #
            role_name__2: []
                                                                               # ]]]
            # .. envvar:: role_name__3 [[[
            #
            role_name__3: []

                                                                               # ]]]

                                                                               # ]]]
        """).strip().split('\n')
        self.r._remove_needless_newlines()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent("""
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__1 [[[
                #
                role_name__1: []


                                                                                   # ]]]
                # .. envvar:: role_name__2 [[[
                #
                role_name__2: []
                                                                                   # ]]]
                # .. envvar:: role_name__3 [[[
                #
                role_name__3: []
                                                                                   # ]]]
                                                                                   # ]]]
                """).strip().split('\n'),
            self.r._lines,
        )

    def test_add_rst_docs_to_yaml_vars(self):
        self.r._lines = textwrap.dedent("""
            role_name__1: []

            role_name__2: []
        """).strip().split('\n')
        self.r.reformat()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent("""
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__1 [[[
                #
                role_name__1: []

                                                                                   # ]]]
                # .. envvar:: role_name__2 [[[
                #
                role_name__2: []
                                                                                   # ]]]
                                                                                   # ]]]
                """).strip().split('\n'),
            self.r._lines,
        )

    def test_get_sections_for_lines(self):
        self.r._lines = textwrap.dedent("""
            # 0 test

            # 1 [[[

            # 1 test
            # ]]]

            # 2 [[[

            # 2 test

            # ]]]
            # 3 [[[
            # 3 test

            # ]]]

            # [[[
            # 4 test

            # ]]]
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)

        pprint.pprint(self.r._lines)
        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# 0 test']},
             {'fold_name': '1', 'lines': ['# 1 test']},
             {'fold_name': '2', 'lines': ['# 2 test']},
             {'fold_name': '3', 'lines': ['# 3 test']},
             {'fold_name': '', 'lines': ['# 4 test']}],
            self.r._sections,
        )

    def test_get_sections_for_lines_recursive(self):
        self.r._lines = textwrap.dedent("""
            # 2 [[[

            # 2 test

            # 2.1 [[[

            # 2.1 test

            test

            # ]]]

            # 2.2 [[[

            # 2.2 test

            # 2.1.1 [[[

            # 2.1.1 test

            # ]]]

            # ]]]

            # ]]]
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)

        pprint.pprint(self.r._lines)
        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '2',
              'lines': ['# 2 test'],
              'subsections': [{'fold_name': '2.1', 'lines': ['# 2.1 test', '', 'test']},
                              {'fold_name': '2.2',
                               'lines': ['# 2.2 test'],
                               'subsections': [{'fold_name': '2.1.1',
                                                'lines': ['# 2.1.1 test']}]}]}],
            self.r._sections,
        )

    def test_get_sections_for_lines_recursive_no_separation(self):
        self.r._lines = textwrap.dedent("""
            # 2 [[[
            # 2.1 [[[

            # 2.1 test

            # ]]]
            # ]]]
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)

        pprint.pprint(self.r._lines)
        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '2',
              'subsections': [{'fold_name': '2.1', 'lines': ['# 2.1 test']}]}],
            self.r._sections,
        )

    def test_get_sections_for_lines_line_after_section(self):
        self.r._lines = textwrap.dedent("""
            # Before section

            # Only includes role_name__1 [[[
            # ------------------------------

            role_name__1: 'test 1'

            # ]]]

            role_name__2: 'test 2'
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)

        pprint.pprint(self.r._lines)
        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# Before section']},
             {'fold_name': 'Only includes role_name__1',
              'lines': ['# ------------------------------', '', "role_name__1: 'test 1'"]},
             {'lines': ["role_name__2: 'test 2'"]}],
            self.r._sections,
        )

    def test_get_sections_for_lines_before_after(self):
        self.r._lines = textwrap.dedent("""
            # Before

            # .. envvar:: role_name__1 [[[
            #
            # Please write nice description here!
            role_name__1: |
              YAML text block, closing fold mark can not be indented or it would be included into this string!

            # ]]]

            # After
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# Before']},
             {'fold_name': '.. envvar:: role_name__1',
              'lines': ['#',
                        '# Please write nice description here!',
                        'role_name__1: |',
                        '  YAML text block, closing fold mark can not be indented or '
                        'it would be included into this string!']},
             {'lines': ['# After']}],
            self.r._sections,
        )

    def test_get_sections_for_lines_before_after_in_fold(self):
        expected_lines = textwrap.dedent("""
            # First level fold [[[

            # Begin level fold comment

            # .. envvar:: role_name__1 [[[
            #
            # Please write nice description here!
            role_name__1: |
              YAML text block, closing fold mark can not be indented or it would be included into this string!

            # ]]]

            # End level fold comment 1
            # End level fold comment 2

            # ]]]

            # EOF comment
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(expected_lines, 0)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': 'First level fold',
              'lines': ['# Begin level fold comment'],
              'subsections': [{'fold_name': '.. envvar:: role_name__1',
                               'lines': ['#',
                                         '# Please write nice description here!',
                                         'role_name__1: |',
                                         '  YAML text block, closing fold mark can '
                                         'not be indented or it would be included '
                                         'into this string!']},
                              {'lines': ['# End level fold comment 1',
                                         '# End level fold comment 2']}]},
             {'lines': ['# EOF comment']}],
            self.r._sections,
        )

        self.r._lines = self.r._get_lines_from_sections(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                # First level fold [[[
                # Begin level fold comment

                # .. envvar:: role_name__1 [[[
                #
                # Please write nice description here!
                role_name__1: |
                  YAML text block, closing fold mark can not be indented or it would be included into this string!

                # ]]]
                # End level fold comment 1
                # End level fold comment 2

                                                                                   # ]]]
                # EOF comment
            ''').strip().split('\n') + [''],
            self.r._lines,
        )

    def test_get_sections_for_lines_trailing_section_comments_unclosed_fold(self):
        expected_lines = textwrap.dedent("""
            # First level fold [[[

            # Begin level fold comment

            # .. envvar:: role_name__1 [[[
            #
            # Please write nice description here!
            role_name__1: |
              YAML text block, closing fold mark can not be indented or it would be included into this string!

            # ]]]

            # End level fold comment 1
            # End level fold comment 2
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(expected_lines, 0)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# First level fold [[[',
                        '',
                        '# Begin level fold comment',
                        '',
                        '# .. envvar:: role_name__1 [[[',
                        '#',
                        '# Please write nice description here!',
                        'role_name__1: |',
                        '  YAML text block, closing fold mark can not be indented or '
                        'it would be included into this string!',
                        '',
                        '# ]]]',
                        '',
                        '# End level fold comment 1',
                        '# End level fold comment 2']}],
            self.r._sections,
        )

    def test_reformat_variables_single(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    role_name__1:
                      - test: |
                          test
                """).strip().split('\n'),
            },
            {
                "lines": textwrap.dedent("""
                    # .. envvar:: role_name__2
                    #
                    role_name__2: 'test'
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [
                {
                    "fold_name": ".. envvar:: role_name__1",
                    "lines":
                        textwrap.dedent("""
                            role_name__1:
                              - test: |
                                  test
                        """).strip().split('\n')
                },
                {
                    "fold_name": ".. envvar:: role_name__2",
                    "lines":
                        textwrap.dedent("""
                            #
                            role_name__2: 'test'
                        """).strip().split('\n')
                },
            ],
            self.r._sections,
        )

    def test_reformat_variables_space_separated(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    role_name__1:
                      - 1

                      - 2
                    role_name__2: 'test 2'
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__1',
              'lines': ['role_name__1:', '  - 1', '', '  - 2']},
             {'fold_name': '.. envvar:: role_name__2',
              'lines': ["role_name__2: 'test 2'"]}],
            self.r._sections,
        )

    def test_reformat_variables_not_separated(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    role_name__1: 1
                    role_name__2: 2
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__1', 'lines': ['role_name__1: 1']},
             {'fold_name': '.. envvar:: role_name__2', 'lines': ['role_name__2: 2']}],
            self.r._sections,
        )

    def test_reformat_variables_not_separated_with_comments(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    role_name__1: 'test 1'
                    # First comment presumably for role_name__2.
                    # Second comment presumably for role_name__2.
                    role_name__2: 'test 2'
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__1',
              'lines': ["role_name__1: 'test 1'"]},
             {'fold_name': '.. envvar:: role_name__2',
              'lines': ['# First comment presumably for role_name__2.',
                        '# Second comment presumably for role_name__2.',
                        "role_name__2: 'test 2'"]}],
            self.r._sections,
        )

    def test_reformat_variables_with_unrelated_lines_before(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    # 1 unrelated comment before.

                    # First comment presumably for role_name__1.
                    # Second comment presumably for role_name__1.
                    role_name__1: 'test 1'
                """).strip().split('\n'),
            },
            {
                "lines": textwrap.dedent("""
                    # 1 unrelated comment before.

                    # 2 unrelated comment before.

                    # First comment presumably for role_name__2.
                    # Second comment presumably for role_name__2.
                    role_name__2: 'test 1'
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# 1 unrelated comment before.', '']},
             {'fold_name': '.. envvar:: role_name__1',
              'lines': ['# First comment presumably for role_name__1.',
                        '# Second comment presumably for role_name__1.',
                        "role_name__1: 'test 1'"]},
             {'lines': ['# 1 unrelated comment before.',
                        '',
                        '# 2 unrelated comment before.',
                        '']},
             {'fold_name': '.. envvar:: role_name__2',
              'lines': ['# First comment presumably for role_name__2.',
                        '# Second comment presumably for role_name__2.',
                        "role_name__2: 'test 1'"]}],
            self.r._sections,
        )

    def test_reformat_variables_with_unrelated_lines_after(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    # First comment presumably for role_name__1.
                    # Second comment presumably for role_name__1.
                    role_name__1: 'test 1'

                    # 1 unrelated comment after.
                """).strip().split('\n'),
            },
            {
                "lines": textwrap.dedent("""
                    # First comment presumably for role_name__1.
                    # Second comment presumably for role_name__1.
                    role_name__1: 'test 1'

                    # 1 unrelated comment after.
                    # 2 unrelated comment after.
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__1',
              'lines': ['# First comment presumably for role_name__1.',
                        '# Second comment presumably for role_name__1.',
                        "role_name__1: 'test 1'",
                        '']},
             {'lines': ['# 1 unrelated comment after.']},
             {'fold_name': '.. envvar:: role_name__1',
              'lines': ['# First comment presumably for role_name__1.',
                        '# Second comment presumably for role_name__1.',
                        "role_name__1: 'test 1'",
                        '']},
             {'lines': ['# 1 unrelated comment after.', '# 2 unrelated comment after.']}],
            self.r._sections,
        )

    def test_reformat_variables_with_unrelated_lines_mixed(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    # 1 unrelated comment before.
                    # 2 unrelated comment before.

                    # First comment presumably for role_name__1.
                    # Second comment presumably for role_name__1.
                    role_name__1: 'test 1'

                    # 1 unrelated comment after.

                    # 2 unrelated comment after.
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# 1 unrelated comment before.',
                        '# 2 unrelated comment before.',
                        '']},
             {'fold_name': '.. envvar:: role_name__1',
              'lines': ['# First comment presumably for role_name__1.',
                        '# Second comment presumably for role_name__1.',
                        "role_name__1: 'test 1'",
                        '']},
             {'lines': ['# 1 unrelated comment after.',
                        '',
                        '# 2 unrelated comment after.']}],
            self.r._sections,
        )

    def test_reformat_variables_with_subsections(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    # 1 unrelated comment before.
                    # 2 unrelated comment before.

                    # First comment presumably for role_name__1.
                    # Second comment presumably for role_name__1.
                    role_name__1: 'test 1'

                    # 1 unrelated comment after.

                    # 2 unrelated comment after.
                """).strip().split('\n'),
                "subsections": [
                    {
                        "lines": textwrap.dedent("""
                            role_name__1: 1
                            role_name__2: 2
                        """).strip().split('\n'),
                    },
                ],
            },
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# 1 unrelated comment before.',
                        '# 2 unrelated comment before.',
                        '']},
             {'fold_name': '.. envvar:: role_name__1',
              'lines': ['# First comment presumably for role_name__1.',
                        '# Second comment presumably for role_name__1.',
                        "role_name__1: 'test 1'",
                        '']},
             {'lines': ['# 1 unrelated comment after.',
                        '',
                        '# 2 unrelated comment after.'],
              'subsections': [{'fold_name': '.. envvar:: role_name__1',
                               'lines': ['role_name__1: 1']},
                              {'fold_name': '.. envvar:: role_name__2',
                               'lines': ['role_name__2: 2']}]}],
            self.r._sections,
        )

    def test_reformat_variables_move_to_subsection(self):
        self.r._sections = [
            {'lines': ['# Before section']},
            {'fold_name': 'Only includes role_name__1',
             'lines': ['# ------------------------------', '', "role_name__1: 'test 1'"]},
            {'lines': ["role_name__2: 'test 2'"]}
        ]
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['# Before section']},
             {'fold_name': 'Only includes role_name__1',
              'lines': ['# ------------------------------', ''],
              'subsections': [{'fold_name': '.. envvar:: role_name__1',
                               'lines': ["role_name__1: 'test 1'"]}]},
             {'fold_name': '.. envvar:: role_name__2',
              'lines': ["role_name__2: 'test 2'"]}],
            self.r._sections,
        )

    def test_reformat_vars(self):
        self.r._lines = textwrap.dedent("""
            role_name__1: 'test 1'
            role_name__2: 'test 2'

            role_name__3: 'test 3'


            role_name__4: 'test 4'
            role_name__5:
              - 1
              - 2

              - 3
            role_name__6:
              - 2_1

              - 2_2
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__1',
              'lines': ["role_name__1: 'test 1'"]},
             {'fold_name': '.. envvar:: role_name__2',
              'lines': ["role_name__2: 'test 2'", '']},
             {'fold_name': '.. envvar:: role_name__3',
              'lines': ["role_name__3: 'test 3'", '', '']},
             {'fold_name': '.. envvar:: role_name__4',
              'lines': ["role_name__4: 'test 4'"]},
             {'fold_name': '.. envvar:: role_name__5',
              'lines': ['role_name__5:', '  - 1', '  - 2', '', '  - 3']},
             {'fold_name': '.. envvar:: role_name__6',
              'lines': ['role_name__6:', '  - 2_1', '', '  - 2_2']}],
            self.r._sections,
        )

    def test_reformat_vars_and_sections(self):
        self.r._lines = textwrap.dedent("""
            role_name__1:
              - 1

              - 2
            role_name__2: 'test 2'
            role_name__3:
              - 1

              - 3
            # testing [[[
            # -----------

            # ]]]

            role_name__4:
              - 1

              - 3

            # testing2 [[[
            # ------------

            # ]]]
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)
        self.r._reformat_variables(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__1',
              'lines': ['role_name__1:', '  - 1', '', '  - 2']},
             {'fold_name': '.. envvar:: role_name__2',
              'lines': ["role_name__2: 'test 2'"]},
             {'fold_name': '.. envvar:: role_name__3',
              'lines': ['role_name__3:', '  - 1', '', '  - 3']},
             {'fold_name': 'testing', 'lines': ['# -----------']},
             {'fold_name': '.. envvar:: role_name__4',
              'lines': ['role_name__4:', '  - 1', '', '  - 3']},
             {'fold_name': 'testing2', 'lines': ['# ------------']}],
            self.r._sections,
        )

    def test_add_rst_docs_to_yaml_block_vars(self):
        self.r = YamlRstReformatter(
            config={
                'ansible_full_role_name': 'role_owner.role_name',
                'add_string_for_missing_comment': "Please write nice description here!",
            },
        )
        self.r._lines = textwrap.dedent("""
            role_name__1: |
              YAML text block, closing fold mark can not be indented or it would be included into this string!

            role_name__2:
              - text: |
                  YAML text block but limited by the following item.
              - special_number: 23

            role_name__3:
              - text: |
                  YAML text block, closing fold mark can not be indented or it would be included into this string!
        """).strip().split('\n')
        self.r.reformat()

        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent("""
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__1 [[[
                #
                # Please write nice description here!
                role_name__1: |
                  YAML text block, closing fold mark can not be indented or it would be included into this string!

                # ]]]
                # .. envvar:: role_name__2 [[[
                #
                # Please write nice description here!
                role_name__2:
                  - text: |
                      YAML text block but limited by the following item.
                  - special_number: 23

                                                                                   # ]]]
                # .. envvar:: role_name__3 [[[
                #
                # Please write nice description here!
                role_name__3:
                  - text: |
                      YAML text block, closing fold mark can not be indented or it would be included into this string!

                # ]]]
                # ]]]
                """).strip().split('\n'),
            self.r._lines,
        )

    def test_reformat_legacy_rst_sections_to_ignore(self):
        sections = [
            {
                "lines": textwrap.dedent("""
                    ---
                    # Default variables
                    # =================

                    # .. contents:: Sections
                    #    :local:
                """).strip().split('\n'),
            },
            {
                "lines": [
                ]
            },
            {
                "lines": [
                    "test",
                ]
            },
            {
                "lines": [
                    "# test",
                ]
            },
            {
                "lines": [
                    "# test",
                    "#",
                    "# test",
                ]
            },
            {
                "lines": [
                    "# test",
                    "#",
                ]
            },
            {
                "lines": [
                    "# test",
                    "# - some list",
                    "# - some list",
                ]
            },
        ]
        self.r._sections = deepcopy(sections)
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(self.r._sections, sections)

    def test_reformat_legacy_rst_sections(self):
        self.r._sections = [
            {
                "fold_name": ".. Required packages",
                "lines": textwrap.dedent("""
                    #
                    # ---------------------
                    #   Required packages
                    # ---------------------
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [
                {
                    "fold_name": "Required packages",
                    "lines": [
                        "# ---------------------",
                    ],
                },
            ],
            self.r._sections,
        )

    def test_reformat_legacy_rst_sections_no_fold(self):
        self.r._lines = textwrap.dedent("""
            # Required packages
            # --------------
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [
                {
                    "fold_name": "Required packages",
                    "lines": [
                        "# --------------",
                    ],
                },
            ],
            self.r._sections,
        )

    def test_reformat_legacy_rst_sections_no_fold_with_overline(self):
        self.r._lines = textwrap.dedent("""
            # ------------
            #   Required packages
            # -----------------------
        """).strip().split('\n')
        _, self.r._sections = self.r._get_sections_for_lines(self.r._lines, 0)
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [
                {
                    "fold_name": "Required packages",
                    "lines": [
                        "# ------------",
                    ],
                },
            ],
            self.r._sections,
        )

    @log_capture(level=logging.WARNING)
    def test_reformat_legacy_rst_sections_not_matching_heading_chars(self, log):
        sections = [
            {
                "lines": textwrap.dedent("""
                    # --------------------
                    #   Required headers
                    # ====================

                    # =====================
                    #   Required packages
                    # ---------------------
                """).strip().split('\n'),
            },
        ]
        self.r._sections = deepcopy(sections)
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(self.r._sections, sections)

        log.check(
            (
                'yaml4rst.reformatter',
                'WARNING',
                "Not modifying section heading with mismatching heading characters."
                " Top header character: '-'."
                " Bottom header character: '='.",
            ),
            (
                'yaml4rst.reformatter',
                'WARNING',
                "Not modifying section heading with mismatching heading characters."
                " Top header character: '='."
                " Bottom header character: '-'.",
            ),
        )

    def test_reformat_legacy_rst_sections_multiple(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    ---

                    # test

                    # section 1
                    # ---------

                    # test

                    # section 2
                    # ---------

                    # section 2 description

                    # section 3
                    # ---------
                """).strip().split('\n'),
            },
        ]
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['---', '', '# test']},
             {'fold_name': 'section 1', 'lines': ['# ---------', '', '# test']},
             {'fold_name': 'section 2',
              'lines': ['# ---------', '', '# section 2 description']},
             {'fold_name': 'section 3', 'lines': ['# ---------']}],
            self.r._sections)

    def test_reformat_legacy_rst_sections_with_subsections(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    ---

                    # test

                    # section 1
                    # ---------
                """).strip().split('\n'),
                'subsections': [{'fold_name': 'section 1.1',
                                 'lines': ['# """""""""""""'],
                                 'section_level': 2},
                                {'fold_name': 'section 1.2',
                                 'lines': ['# """""""""""""'],
                                 'section_level': 2}],
            },
        ]
        self.r._reformat_legacy_rst_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['---', '', '# test']},
             {'fold_name': 'section 1',
              'lines': ['# ---------'],
              'subsections': [{'fold_name': 'section 1.1',
                               'lines': ['# """""""""""""'],
                               'section_level': 2},
                              {'fold_name': 'section 1.2',
                               'lines': ['# """""""""""""'],
                               'section_level': 2}]}],
            self.r._sections)

    def test_get_section_level(self):
        assert_equal(0, self.r._get_section_level('='))
        assert_equal(0, self.r._get_section_level('='))
        assert_equal(1, self.r._get_section_level('-'))
        assert_equal(0, self.r._get_section_level('='))
        assert_equal(2, self.r._get_section_level('~'))

    def test_reformat_legacy_rst_sections_recursive(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent('''
                    ---

                    # test header

                    # section 1
                    # ---------

                    # test

                    # section 2
                    # ---------

                    # section 2 body

                    # section 2.1
                    # ~~~~~~~~~~~

                    # section 2.1 body

                    # section 2.2
                    # ~~~~~~~~~~~

                    # section 2.2 body

                    # section 2.2.1
                    # """""""""""""

                    # section 2.2.1 body

                    # section 2.3
                    # ~~~~~~~~~~~

                    # section 2.4
                    # ~~~~~~~~~~~

                    # section 2.4.1
                    # """""""""""""

                    # section 2.4.2
                    # """""""""""""

                    # section 2.5
                    # ~~~~~~~~~~~

                    # section 3
                    # ---------
                ''').strip().split('\n'),
            },
        ]
        self.r._reformat_legacy_rst_sections(self.r._sections)
        self.r._sort_section_levels(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'lines': ['---', '', '# test header']},
             {'fold_name': 'section 1', 'lines': ['# ---------', '', '# test']},
             {'fold_name': 'section 2',
              'lines': ['# ---------', '', '# section 2 body'],
              'subsections': [{'fold_name': 'section 2.1',
                               'lines': ['# ~~~~~~~~~~~', '', '# section 2.1 body'],
                               'section_level': 1},
                              {'fold_name': 'section 2.2',
                               'lines': ['# ~~~~~~~~~~~', '', '# section 2.2 body'],
                               'section_level': 1,
                               'subsections': [{'fold_name': 'section 2.2.1',
                                                'lines': ['# """""""""""""',
                                                          '',
                                                          '# section 2.2.1 body'],
                                                'section_level': 2}]},
                              {'fold_name': 'section 2.3',
                               'lines': ['# ~~~~~~~~~~~'],
                               'section_level': 1},
                              {'fold_name': 'section 2.4',
                               'lines': ['# ~~~~~~~~~~~'],
                               'section_level': 1,
                               'subsections': [{'fold_name': 'section 2.4.1',
                                                'lines': ['# """""""""""""'],
                                                'section_level': 2},
                                               {'fold_name': 'section 2.4.2',
                                                'lines': ['# """""""""""""'],
                                                'section_level': 2}]},
                              {'fold_name': 'section 2.5',
                               'lines': ['# ~~~~~~~~~~~'],
                               'section_level': 1}]},
             {'fold_name': 'section 3', 'lines': ['# ---------']}],
            self.r._sections,
        )

        self.r._lines = self.r._get_lines_from_sections(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---

                # test header

                # section 1 [[[
                # -------------

                # test

                                                                                   # ]]]
                # section 2 [[[
                # -------------

                # section 2 body

                # section 2.1 [[[
                # ~~~~~~~~~~~~~~~

                # section 2.1 body

                                                                                   # ]]]
                # section 2.2 [[[
                # ~~~~~~~~~~~~~~~

                # section 2.2 body

                # section 2.2.1 [[[
                # """""""""""""""""

                # section 2.2.1 body

                                                                                   # ]]]
                                                                                   # ]]]
                # section 2.3 [[[
                # ~~~~~~~~~~~~~~~

                                                                                   # ]]]
                # section 2.4 [[[
                # ~~~~~~~~~~~~~~~

                # section 2.4.1 [[[
                # """""""""""""""""

                                                                                   # ]]]
                # section 2.4.2 [[[
                # """""""""""""""""

                                                                                   # ]]]
                                                                                   # ]]]
                # section 2.5 [[[
                # ~~~~~~~~~~~~~~~

                                                                                   # ]]]
                                                                                   # ]]]
                # section 3 [[[
                # -------------

                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    @log_capture(level=logging.WARNING)
    def test_add_fixmes(self, log):
        self.r = YamlRstReformatter(
            config={
                'ansible_full_role_name': 'role_owner.role_name',
                'add_string_for_missing_comment': "Please write nice description here!",
            },
        )
        self.r._sections = [
            {
                "fold_name": ".. envvar:: role_name__host_devices",
                "lines": textwrap.dedent("""
                    #
                    #
                    # Host definition list of encrypted filesystems.
                    role_name__host_devices: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__host_devices",
                "lines": textwrap.dedent("""
                    #
                    role_name__host_devices: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__host_devices",
                "lines": textwrap.dedent("""
                    #
                    #
                    role_name__host_devices: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__host_devices",
                "lines": textwrap.dedent("""
                    #
                    #
                """).strip().split('\n'),
                "subsections": [
                    {
                        "fold_name": ".. envvar:: role_name__host_devices",
                        "lines": textwrap.dedent("""
                            #
                            role_name__host_devices: []
                        """).strip().split('\n'),
                    },
                    {
                        "fold_name": ".. envvar:: role_name__host_devices",
                        "lines": textwrap.dedent("""
                            #
                            # Host definition list of encrypted filesystems.
                            role_name__host_devices: []
                        """).strip().split('\n'),
                    },
                ],
            },
        ]
        self.r._add_fixmes(self.r._sections)

        pprint.pprint(self.r._sections)
        assert_equal(
            [{'fold_name': '.. envvar:: role_name__host_devices',
              'lines': ['#',
                        '#',
                        '# Host definition list of encrypted filesystems.',
                        'role_name__host_devices: []']},
             {'fold_name': '.. envvar:: role_name__host_devices',
              'lines': ['#',
                        '# Please write nice description here!',
                        'role_name__host_devices: []']},
             {'fold_name': '.. envvar:: role_name__host_devices',
              'lines': ['#',
                        '#',
                        '# Please write nice description here!',
                        'role_name__host_devices: []']},
             {'fold_name': '.. envvar:: role_name__host_devices',
              'lines': ['#', '#', '# Please write nice description here!'],
              'subsections': [{'fold_name': '.. envvar:: role_name__host_devices',
                               'lines': ['#',
                                         '# Please write nice description here!',
                                         'role_name__host_devices: []']},
                              {'fold_name': '.. envvar:: role_name__host_devices',
                               'lines': ['#',
                                         '# Host definition list of encrypted '
                                         'filesystems.',
                                         'role_name__host_devices: []']}]}],
            self.r._sections,
        )

        expeceted_log_entry = (
            'yaml4rst.reformatter',
            'WARNING',
            'Inserting FIXME note for missing comment. Be sure to replace "Please '
            'write nice description here!" with something meaningful.',
        )

        log.check(
            expeceted_log_entry,
            expeceted_log_entry,
            expeceted_log_entry,
            expeceted_log_entry,
        )

    def test_get_lines_from_sections(self):
        self.r._sections = [
            {
                "lines": textwrap.dedent("""
                    ---

                    # test

                    # section 1
                    # ---------

                    # test

                    # .. envvar:: role_name__host_devices
                    #
                    # Host definition list of encrypted filesystems.
                    role_name__host_devices: []

                    # section 2
                    # ---------

                    # section 2 description

                    # section 3
                    # ---------
                """).strip().split('\n'),
            },
        ]
        LOG.setLevel(logging.WARNING)
        self.r._reformat_legacy_rst_sections(self.r._sections)
        LOG.setLevel(logging.DEBUG)
        self.r._lines = self.r._get_lines_from_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---

                # test

                # section 1 [[[
                # -------------

                # test

                # .. envvar:: role_name__host_devices
                #
                # Host definition list of encrypted filesystems.
                role_name__host_devices: []

                                                                                   # ]]]
                # section 2 [[[
                # -------------

                # section 2 description

                                                                                   # ]]]
                # section 3 [[[
                # -------------

                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_get_lines_from_sections_envvar(self):
        self.r._sections = [
            {
                "fold_name": ".. envvar:: role_name__1",
                "lines": textwrap.dedent("""
                    # Comment 1.
                    role_name__1: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__2",
                "lines": textwrap.dedent("""
                    #
                    # Comment 2.
                    role_name__2: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__3",
                "lines": textwrap.dedent("""
                    #
                    #
                    # Comment 3.
                    role_name__3: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__4",
                "lines": textwrap.dedent("""
                    # Comment 4.
                    #
                    role_name__4: []
                """).strip().split('\n'),
            },
            {
                "fold_name": ".. envvar:: role_name__5",
                "lines": textwrap.dedent("""
                    #
                    # Comment 5.
                    #
                    role_name__5: []
                """).strip().split('\n'),
            },
        ]
        self.r._lines = self.r._get_lines_from_sections(self.r._sections)

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                # .. envvar:: role_name__1 [[[
                #
                # Comment 1.
                role_name__1: []

                                                                                   # ]]]
                # .. envvar:: role_name__2 [[[
                #
                # Comment 2.
                role_name__2: []

                                                                                   # ]]]
                # .. envvar:: role_name__3 [[[
                #
                #
                # Comment 3.
                role_name__3: []

                                                                                   # ]]]
                # .. envvar:: role_name__4 [[[
                #
                # Comment 4.
                #
                role_name__4: []

                                                                                   # ]]]
                # .. envvar:: role_name__5 [[[
                #
                # Comment 5.
                #
                role_name__5: []

                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_check_ends_with_yaml_block(self):
        lines = textwrap.dedent('''
            # .. envvar:: role_name__2 [[[
            #
            # Some documentation for :envvar:`role_name__2`.
            role_name__2: |
              Some text

            # ]]]
        ''').strip().split('\n')
        pprint.pprint(lines)
        assert_equal(True, self.r._check_ends_with_yaml_block(lines[:len(lines) - 0]))
        assert_equal(True, self.r._check_ends_with_yaml_block(lines[:len(lines) - 1]))
        assert_equal(True, self.r._check_ends_with_yaml_block(lines[:len(lines) - 2]))
        assert_equal(True, self.r._check_ends_with_yaml_block(lines[:len(lines) - 3]))
        assert_equal(False, self.r._check_ends_with_yaml_block(lines[:len(lines) - 4]))
        assert_equal(False, self.r._check_ends_with_yaml_block(lines[:len(lines) - 5]))
        assert_equal(False, self.r._check_ends_with_yaml_block(lines[:len(lines) - 6]))

    def test_reformat_bare_vars(self):
        self.r = YamlRstReformatter(
            config={
                'ansible_full_role_name': 'role_owner.role_name',
                'add_string_for_missing_comment':
                    "I don’t have a better description of what I am doing yet."
                    " Please change me!",
            },
        )

        self.r._lines = textwrap.dedent("""
            role_name__0: 'test 1'
            # I do already have a (completely meaningless) description :)
            role_name__1: 'test 2'

            role_name__2: 2
            role_name__3: { 'test': 3 }
            role_name__4: 'test 4'
        """).strip().split('\n')

        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__0 [[[
                #
                # I don’t have a better description of what I am doing yet. Please change me!
                role_name__0: 'test 1'

                                                                                   # ]]]
                # .. envvar:: role_name__1 [[[
                #
                # I do already have a (completely meaningless) description :)
                role_name__1: 'test 2'

                                                                                   # ]]]
                # .. envvar:: role_name__2 [[[
                #
                # I don’t have a better description of what I am doing yet. Please change me!
                role_name__2: 2

                                                                                   # ]]]
                # .. envvar:: role_name__3 [[[
                #
                # I don’t have a better description of what I am doing yet. Please change me!
                role_name__3: { 'test': 3 }

                                                                                   # ]]]
                # .. envvar:: role_name__4 [[[
                #
                # I don’t have a better description of what I am doing yet. Please change me!
                role_name__4: 'test 4'
                                                                                   # ]]]
                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_reformat_mixed(self):
        self.r._lines = textwrap.dedent("""
            role_name__0: 'test 0'
            # role_name__1 already has a (completely meaningless) description :)
            role_name__1: 'test 1'

            role_name__2: 2

            # section 2 [[[
            # -------------

            role_name__3: { 'test': 3 }

            # ]]]

            role_name__4: 'test 4'
        """).strip().split('\n')

        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__0 [[[
                #
                role_name__0: 'test 0'

                                                                                   # ]]]
                # .. envvar:: role_name__1 [[[
                #
                # role_name__1 already has a (completely meaningless) description :)
                role_name__1: 'test 1'

                                                                                   # ]]]
                # .. envvar:: role_name__2 [[[
                #
                role_name__2: 2

                                                                                   # ]]]
                # section 2 [[[
                # -------------

                # .. envvar:: role_name__3 [[[
                #
                role_name__3: { 'test': 3 }
                                                                                   # ]]]
                                                                                   # ]]]
                # .. envvar:: role_name__4 [[[
                #
                role_name__4: 'test 4'
                                                                                   # ]]]
                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_reformat_bare_vars_with_comments(self):
        self.r._lines = textwrap.dedent("""
            # Host group definition list of encrypted filesystems.
            role_name__group_devices: []


            # Host definition list of encrypted filesystems.
            role_name__host_devices: []

            # some
            # thing
            role_name__host: []
        """).strip().split('\n')

        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__group_devices [[[
                #
                # Host group definition list of encrypted filesystems.
                role_name__group_devices: []

                                                                                   # ]]]
                # .. envvar:: role_name__host_devices [[[
                #
                # Host definition list of encrypted filesystems.
                role_name__host_devices: []

                                                                                   # ]]]
                # .. envvar:: role_name__host [[[
                #
                # some
                # thing
                role_name__host: []
                                                                                   # ]]]
                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_reformat_multi_line_vars(self):
        self.r._lines = textwrap.dedent("""
            role_name__0:
              - 23

              - 42
            role_name__1: |

              Some text

              More text

            role_name__3: '{{ True and
                              True }}'
        """).strip().split('\n')

        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__0 [[[
                #
                role_name__0:
                  - 23

                  - 42

                                                                                   # ]]]
                # .. envvar:: role_name__1 [[[
                #
                role_name__1: |

                  Some text

                  More text

                # ]]]
                # .. envvar:: role_name__3 [[[
                #
                role_name__3: '{{ True and
                                  True }}'
                                                                                   # ]]]
                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_reformat_empty(self):
        self.r._lines = []
        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                                                                                   # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_reformat_no_vars_comment(self):
        self.r = YamlRstReformatter(
            config={
                'ansible_full_role_name': 'role_owner.role_name',
                'add_string_for_missing_comment': "Please write nice description here!",
            },
        )

        self.r._lines = textwrap.dedent("""
            # Some documentation for :envvar:`role_name__1`.
            role_name__1: 'test'

            role_name__2: 'string'

            role_name__0: |
              Some text 1


            # .. envvar:: role_name__2 [[[
            #
            role_name__3: |
              Some text

            # ]]]
        """).strip().split('\n')

        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(
            textwrap.dedent('''
                ---
                # .. vim: foldmarker=[[[,]]]:foldmethod=marker

                # role_owner.role_name default variables [[[
                # ==========================================

                # .. contents:: Sections
                #    :local:
                #
                # .. include:: includes/all.rst


                # .. envvar:: role_name__1 [[[
                #
                # Some documentation for :envvar:`role_name__1`.
                role_name__1: 'test'

                                                                                   # ]]]
                # .. envvar:: role_name__2 [[[
                #
                # Please write nice description here!
                role_name__2: 'string'

                                                                                   # ]]]
                # .. envvar:: role_name__0 [[[
                #
                # Please write nice description here!
                role_name__0: |
                  Some text 1

                # ]]]
                # .. envvar:: role_name__3 [[[
                #
                # Please write nice description here!
                role_name__3: |
                  Some text

                # ]]]
                # ]]]
            ''').strip().split('\n'),
            self.r._lines,
        )

    def test_reformat(self):
        self.r._lines = textwrap.dedent("""
            # ---------------------
            #   Required packages
            # ---------------------

            # Some documentation for :envvar:`role_name__1`.
            role_name__1: 'test'

            # Some documentation for :envvar:`role_name__x`.
            role_name__x: |
              Some text 1

            # Some documentation for :envvar:`role_name__2`.
            role_name__2: |
              Some text
        """).strip().split('\n')

        expected_output = textwrap.dedent('''
            ---
            # .. vim: foldmarker=[[[,]]]:foldmethod=marker

            # role_owner.role_name default variables [[[
            # ==========================================

            # .. contents:: Sections
            #    :local:
            #
            # .. include:: includes/all.rst


            # Required packages [[[
            # ---------------------

            # .. envvar:: role_name__1 [[[
            #
            # Some documentation for :envvar:`role_name__1`.
            role_name__1: 'test'

                                                                               # ]]]
            # .. envvar:: role_name__x [[[
            #
            # Some documentation for :envvar:`role_name__x`.
            role_name__x: |
              Some text 1

            # ]]]
            # .. envvar:: role_name__2 [[[
            #
            # Some documentation for :envvar:`role_name__2`.
            role_name__2: |
              Some text

            # ]]]
            # ]]]
            # ]]]
        ''').strip().split('\n')

        self.r.reformat()

        pprint.pprint(self.r._sections)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_output, self.r._lines)

        self.r._lines = deepcopy(expected_output)
        print('#######\n' + self.r.get_content() + '\n#######')
        assert_equal(expected_output, self.r._lines)
