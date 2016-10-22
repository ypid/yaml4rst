# -*- coding: utf-8 -*-

"""
Reformatting class of yaml4rst
"""

from __future__ import absolute_import, division, print_function

import logging
import re
import os
import sys
import textwrap
from copy import deepcopy
#  from distutils.util import strtobool
import pprint

#  if sys.version_info[0] == 2:  # pragma: no cover
#      from io import open  # pylint: disable=redefined-builtin


import yaml
#  yaml.scan does not return YAML comments which is what we need here ;)
#  Ref: https://buguroo.com/why-parser-generator-tools-are-mostly-useless-in-static-analysis

import jinja2


from .defaults import DEFAULTS
from .helpers import get_first_match, get_last_index, insert_list, strip_list

__all__ = ['YamlRstReformatterError', 'YamlRstReformatter', 'YAML_RST_REFORMATTER_FEATURES']

# Before making pprint calls in debug logging, LOG.isEnabledFor(logging.DEBUG)
# should be checked for performance reasons.
LOG = logging.getLogger(__name__)


class YamlRstReformatterError(Exception):
    """Exception which is thrown by YamlRstReformatter when a unrecoverable error occurred."""
    pass


# Redundant. Places: /README.rst and /yaml4rst/reformatter.py
YAML_RST_REFORMATTER_FEATURES = textwrap.dedent("""
    Checks for:

    * Reasonable variable namespace
    * Undocumented variables

    Automatically fixes:

    * RST sections which are not folds
    * Undocumented variables (adds a FIXME for the user)
    * Documented variables which are not folds
    * YAML documents without a defined header
    * Spacing between variables and sections
""").strip()


class YamlRstReformatter(object):
    __doc__ = textwrap.dedent("""
        YAML+RST linting/reformatting class with the following features:

        {features}
    """).format(
        features=YAML_RST_REFORMATTER_FEATURES,
    )

    _RE_HEADING_CHARS = re.compile(
        r'^#\s(?P<heading_char>[^a-zA-Z0-9]){3,999}$',
    )

    _HEADER_END_LINES = {
        'debops/ansible': [
            '# Default variables',
            '#    :local:',
            '# .. contents:: Sections',
            '# .. include:: includes/all.rst'
        ],
    }

    def __init__(
            self,
            preset=deepcopy(DEFAULTS['preset']),
            template_path=deepcopy(DEFAULTS['template_path']),
            config=None,
    ):

        self._preset = preset
        self._template_path = template_path

        self._config = deepcopy(DEFAULTS['config'])
        if config is not None:
            self._config.update(config)
        self._auto_complete_config()

        self._lines = []
        self._sections = []
        self._section_levels = []
        self._var_names = set()

        self._last_line_fold_yaml_block = False

    def read_file(self, input_file):
        """Read the given input file path and save its content for later processing."""
        with open(input_file, 'r') as file_fh:
            self._lines = [l.rstrip() for l in file_fh]

            # Since this parser is very rudimentary, we check at the beginning
            # if the file we got is even valid YAML.
            yaml.load(self.get_content())

    def get_content(self):
        """Return one string containing all lines."""
        return '\n'.join(self._lines)

    def reformat(self):
        """Process (check/lint/reformat) the saved lines."""
        self._check_folds()
        _, self._sections = self._get_sections_for_lines(self._lines, 0, section_lines=[])
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('sections after _get_sections_for_lines:\n{}'.format(
                pprint.pformat(self._sections),
            ))
        self._reformat_legacy_rst_sections(self._sections)
        self._reformat_variables(self._sections)
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('sections after _reformat_variables:\n{}'.format(
                pprint.pformat(self._sections),
            ))
        self._sort_section_levels(self._sections)
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('sections after _sort_section_level:\n{}'.format(
                pprint.pformat(self._sections),
            ))
        self._add_fixmes(self._sections)
        self._lines = self._get_lines_from_sections(self._sections)
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('lines after _get_lines_from_sections:\n{}'.format(
                pprint.pformat(self._lines),
            ))
        self._update_header()
        self._remove_needless_newlines()

        self._check_var_names()

        # Just to ensure that we did not make a mistake.
        self._check_folds()
        yaml.load(self.get_content())

    def write_file(self, output_file):
        """Write the saved lines to the given output file path and save its content for later processing."""
        if output_file == '-':
            sys.stdout.write(self.get_content() + '\n')
        else:
            with open(output_file, 'w', encoding='utf-8') as output_fh:
                output_fh.write(self.get_content() + '\n')

    def _auto_complete_config(self):
        if 'ansible_full_role_name' in self._config:
            if len(self._config['ansible_full_role_name'].split('.')) == 2:
                self._config.setdefault(
                    'ansible_role_owner',
                    self._config['ansible_full_role_name'].split('.')[0],
                )
                self._config.setdefault(
                    'ansible_role_name',
                    '.'.join(self._config['ansible_full_role_name'].split('.')[1:]),
                )
            else:
                LOG.warning(
                    "The config option 'ansible_full_role_name' has a invalid format."
                    " Expected 'ROLE_OWNER.ROLE_NAME'."
                    " Got {} (no '.').".format(
                        self._config['ansible_full_role_name'],
                    )
                )

    def _get_rendered_template(self, template_name):
        template_dir_path = os.path.abspath(os.path.join(
            self._template_path,
            self._preset,
        ))
        template_loader = jinja2.FileSystemLoader(
            searchpath=template_dir_path,
        )
        template_env = jinja2.Environment(
            loader=template_loader,
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
        )
        template = template_env.get_template(template_name + '.j2')

        try:
            rendered_template = template.render(self._config)
        except jinja2.exceptions.UndefinedError as err:
            raise YamlRstReformatterError(
                "{}. Consider providing the variable as config option.".format(err)
            )

        return rendered_template

    @staticmethod
    def _get_line_fold(line):
        return_dict = {
            'change': 0,
            'name': None,
            'level': None,
        }

        _fold_open_re = re.search(r'^\s*#\s*(?P<fold_name>(?:\.{2})?\s*.*?)\s*[[({]{3}(?P<fold_level>\d*)$', line)
        if _fold_open_re:
            if _fold_open_re.group('fold_level') != '':
                raise NotImplementedError(
                    "Found explicit fold level. See under known limitations in the docs.")
            return_dict = {
                'change': +1,
                'name': _fold_open_re.group('fold_name'),
                'level': _fold_open_re.group('fold_level'),
            }
        elif re.search(r'^\s*#\s*(?:\.{2})?\s*[\])}]{3}$', line):
            return_dict['change'] = -1

        return return_dict

    def _check_folds(self, lines=None, fatal=True):
        if lines is None:
            lines = self._lines

        fold_level = 0
        for line in lines:
            fold_level += self._get_line_fold(line)['change']

        msg = None
        if fold_level > 1:
            msg = "{} folds are unclosed.".format(abs(fold_level))
        elif fold_level == 1:
            msg = "{} fold is unclosed.".format(abs(fold_level))
        elif fold_level == -1:
            msg = "{} additional closing fold marker.".format(abs(fold_level))
        elif fold_level < -1:
            msg = "{} additional closing fold markers.".format(abs(fold_level))

        if msg is not None:
            if fatal:
                raise YamlRstReformatterError(msg)
            else:
                LOG.warning(msg)

        return fold_level

    def _check_var_names(self):
        if 'ansible_role_owner' not in self._config:
            return

        for var_name in sorted(self._var_names):
            if not var_name.startswith(self._config['ansible_role_name'] + '_'):
                LOG.warning(
                    "The variable '{var}' is outside of the '{ns}' namespace."
                    " All variables of a Ansible role should really be in the namespace of the Ansible role!"
                    " Consider prefixing the variable with '{prefix}'"
                    " or consider to follow the DebOps prefix convention with '{debops_prefix}'"
                    " which also works nicely with role dependencies.".format(
                        var=var_name,
                        ns=self._config['ansible_role_name'],
                        prefix=self._config['ansible_role_name'] + '_',
                        debops_prefix=self._config['ansible_role_name'] + '__',
                    )
                )

    def _get_closing_folds(self, closing_folds, yaml_block=False):
        lines = []

        if closing_folds > 0:
            if yaml_block:
                closing_fold_format_spec = '{}'
            else:
                closing_fold_format_spec = self._config['closing_fold_format_spec']
            for _ in range(closing_folds):
                lines.append(closing_fold_format_spec.format('# ]]]'))
            closing_folds = 0

        LOG.debug('_get_closing_folds returns: {}'.format(lines))
        return lines

    def _get_sections_for_lines(self, input_lines, ind, section_lines=None, inside_fold=False):
        LOG.debug('call input: {}'.format(input_lines))
        LOG.debug('call ind: {}'.format(ind))
        LOG.debug('call section_lines: {}'.format(section_lines))

        if section_lines is None:
            section_lines = []

        new_section = {}
        sections = []
        subsections = []
        fold_level = 0
        ind -= 1
        while True:
            ind += 1
            if ind >= len(input_lines):
                break
            line = input_lines[ind]
            LOG.debug("processing line: '{}'".format(line))

            fold = self._get_line_fold(line)
            fold_level += fold['change']
            LOG.debug('ind: {}, fold: {}, fold change: {}, name: {}, inside: {}'.format(
                ind,
                fold_level,
                fold['change'],
                fold['name'],
                inside_fold,
            ))

            if fold['change'] == 0:
                if len(subsections) > 0 and line != '':
                    start_ind = ind
                    while True:
                        ind += 1
                        if ind >= len(input_lines):
                            break

                        line = input_lines[ind]
                        fold = self._get_line_fold(line)

                        if fold['change'] != 0 or not line.startswith('#'):
                            break

                    subsections.append({
                        'lines': input_lines[start_ind:ind],
                    })
                    continue

                section_lines.append(line)
                LOG.debug('section_lines: {}'.format(section_lines))
            elif fold['change'] == +1:
                if 'fold_name' not in new_section and len(strip_list(section_lines)) == 0:
                    new_section['fold_name'] = fold['name']

            if fold_level > 1 and fold['change'] == +1:
                fold_level -= 1
                LOG.debug('sub: {} ({}), inside: {}'.format(ind, input_lines[ind], inside_fold))
                ind, new_subsections = self._get_sections_for_lines(
                    input_lines,
                    ind,
                    section_lines=[],
                    inside_fold=True
                )
                try:
                    LOG.debug('sub return: {} ({}), inside: {}'.format(ind, input_lines[ind], inside_fold))
                except IndexError:  # pragma: no cover
                    LOG.debug('sub return: {} ({}), inside: {}'.format(ind, 'eof', inside_fold))
                subsections.extend(new_subsections)

            eof = ind+1 not in range(len(input_lines))
            if (fold['change'] == -1 and (len(section_lines) > 0 or len(subsections) > 0) or
                    fold['change'] == 1 and 'fold_name' not in new_section) or eof:
                section_lines = strip_list(section_lines)
                LOG.debug('section_lines (strip): {}'.format(section_lines))
                if len(subsections) > 0:
                    new_section['subsections'] = subsections
                    subsections = []
                if len(section_lines) > 0:
                    new_section['lines'] = section_lines
                    section_lines = []
                sections.append(new_section)
                LOG.debug('sections: {}'.format(sections))
                new_section = {}
                if 'fold_name' not in new_section and fold['name'] is not None:
                    new_section['fold_name'] = fold['name']
                if inside_fold:
                    break

        if len(sections) == 0:
            LOG.debug("return lines as they where passed: {}".format(input_lines))
            return ind, [{
                'lines': input_lines,
            }]
        else:
            LOG.debug("return sections: {}".format(sections))
            return ind, sections

    def _get_lines_from_sections(self, sections):
        lines = []
        closing_folds = 0
        opening_fold = ''
        for section in sections:

            if 'fold_name' in section:
                opening_fold = '# {name}[[['.format(
                    name=(section['fold_name'] + ' ') if (section['fold_name'] != '') else '',
                )
                closing_folds += 1
                lines.append(opening_fold)

            if len(section.get('lines', [])) > 0:
                section_lines = list(section['lines'])
                if 'fold_name' in section:
                    if section_lines[0] != '#':
                        _re = self._RE_HEADING_CHARS.search(section_lines[0])
                        if section['fold_name'].startswith('.. '):
                            lines.append('#')
                        elif _re:
                            section_lines[0] = '# {}'.format(
                                _re.group('heading_char') * (len(opening_fold) - 2),
                            )
                lines.extend(strip_list(section_lines))
                lines.append('')

            if 'subsections' in section:
                lines.extend(self._get_lines_from_sections(section['subsections']))

            if closing_folds > 0:
                LOG.debug("Writing {} closing folds".format(closing_folds))
                self._last_line_fold_yaml_block = self._check_ends_with_yaml_block(lines)
                LOG.debug('self._last_line_fold_yaml_block: {}'.format(self._last_line_fold_yaml_block))
                lines.extend(self._get_closing_folds(
                    closing_folds,
                    self._last_line_fold_yaml_block,
                ))
                closing_folds = 0

        LOG.debug("Returning lines:\n{}".format(lines))
        return lines

    def _add_fixmes(self, sections):
        for section in sections:
            if 'subsections' in section:
                self._add_fixmes(section['subsections'])

            if len(section.get('lines', [])) == 0:
                continue

            if not section.get('fold_name', '').startswith('.. '):
                continue

            found_comment = False
            last_comment_ind = None
            for ind, line in enumerate(section['lines']):
                LOG.debug("Processing: {}, line: {}".format(ind, line))
                if not line.startswith('#'):
                    break

                if line == '#':
                    last_comment_ind = ind
                    continue
                else:
                    found_comment = True

            if not found_comment and self._config.get('add_string_for_missing_comment', '') != '':
                LOG.warning(
                    "Inserting FIXME note for missing comment."
                    " Be sure to replace \"{string}\" with something meaningful.".format(
                        string=self._config['add_string_for_missing_comment'],
                    )
                )
                section['lines'].insert(
                    last_comment_ind + 1 if last_comment_ind is not None else 0,
                    '# {}'.format(self._config['add_string_for_missing_comment']),
                )

    def _remove_needless_newlines(self):
        """Remove needless newlines near closing folds in self._lines."""

        state = 'before'
        ind = -1
        empty_lines_before = []
        closing_folds = 0
        while True:
            ind += 1
            try:
                line = self._lines[ind]
            except IndexError:
                break

            if not line.startswith(' '):
                empty_lines_before = []

            if line == '':
                empty_lines_before.append(ind)
            else:
                fold = self._get_line_fold(line)
                if fold['change'] == -1:
                    closing_folds += 1
                    state = 'in'

            if state == 'in':
                ind += 1
                for _ in range(ind, len(self._lines)):
                    fold = self._get_line_fold(self._lines[ind])
                    if self._lines[ind] == '':
                        del self._lines[ind]
                    elif fold['change'] == -1:
                        ind += 1
                        closing_folds += 1
                    else:
                        state = 'before'
                        break

                wanted_empty_line_count = int(self._config['wanted_empty_lines_between_items'])
                deleted_empty_lines = 0
                LOG.debug("Detected {} closing folds".format(closing_folds))
                for empty_ind in reversed(empty_lines_before):
                    if closing_folds + len(empty_lines_before) - deleted_empty_lines <= wanted_empty_line_count:
                        LOG.debug("breaking out of delete empty line loop at line: {}".format(
                            self._lines[empty_ind-1],
                        ))
                        break

                    del self._lines[empty_ind]
                    deleted_empty_lines += 1

                empty_lines_before = []
                closing_folds = 0

    def _get_section_level(self, heading_char):
        if heading_char in self._section_levels:
            return self._section_levels.index(heading_char)
        else:
            self._section_levels.append(heading_char)
            return len(self._section_levels) - 1

    def _sort_section_levels(self, sections, section_level=0):

        while True:
            done = True

            sec_ind = -1
            while True:
                sec_ind += 1
                try:
                    section = sections[sec_ind]
                except IndexError:
                    LOG.debug("break")
                    break

                if 'subsections' in section:
                    self._sort_section_levels(section['subsections'], section_level=section_level + 1)

                if section.get('section_level', section_level) > section_level:
                    LOG.debug("Moving section {} into subsection of previous section".format(
                        section
                    ))
                    sections[sec_ind-1].setdefault('subsections', [])
                    sections[sec_ind-1]['subsections'].append(section)
                    del sections[sec_ind]
                    sec_ind -= 1
                    done = False

            if done:
                break

    def _reformat_legacy_rst_sections(self, sections):
        """Reformat RST sections and generate folds out of them.

        Ref: http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections
        """

        sec_ind = -1
        while True:
            sec_ind += 1
            try:
                section = sections[sec_ind]
            except IndexError:
                LOG.debug("break")
                break
            if len(section.get('lines', [])) == 0:
                continue

            LOG.debug('sec_ind: {}, section: {}'.format(sec_ind, section['lines']))

            heading_char = None
            heading_char_inds = []
            heading = None
            heading_ind = None

            # States:
            #
            # * before (After the heading is before the heading :)
            # * heading
            state = 'before'
            ind = -1

            if sec_ind == 0 and self._get_header_end_ind(section['lines']) is not None:
                header_end = self._get_header_end_ind(section['lines'])
                LOG.debug('header_end_ind: {}'.format(header_end))
                # Don’t rewrite the header. self._update_header also wants something to do ;)
                ind = header_end

            while True:
                ind += 1
                try:
                    line = section['lines'][ind]
                except IndexError:
                    LOG.debug("break")
                    break

                if state == 'before':
                    heading_char = None
                    heading_char_inds = []
                    heading = None
                    heading_ind = None

                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug("processing line: '{}'".format(line))
                    LOG.debug("sections: \n{}".format(pprint.pformat(sections)))
                    LOG.debug(
                        'ind: {}, state: {}, heading_char: {}, heading_char_inds: {},'
                        ' heading: {}, heading_ind: {}'.format(
                            ind, state, heading_char, heading_char_inds, heading, heading_ind,
                        )
                    )

                if line == '#' and state == 'before':
                    del section['lines'][ind]
                    ind -= 1
                    continue

                _re_heading_chars = self._RE_HEADING_CHARS.search(line)
                _re_heading = re.search(r'#\s+(?P<heading>[^\s].+)$', line)
                if _re_heading_chars:
                    LOG.debug('_re_heading_chars')
                    if heading_char is not None and heading_char != _re_heading_chars.group('heading_char'):
                        LOG.warning(
                            "Not modifying section heading with mismatching heading characters."
                            " Top header character: '{top_heading_char}'."
                            " Bottom header character: '{bottom_heading_char}'.".format(
                                top_heading_char=heading_char,
                                bottom_heading_char=_re_heading_chars.group('heading_char'),
                            )
                        )
                        state = 'before'
                        continue
                    heading_char = _re_heading_chars.group('heading_char')
                    heading_char_inds.append(ind)
                    state = 'heading'
                elif _re_heading and (state == 'heading' or len(heading_char_inds) == 0):
                    heading = _re_heading.group('heading')
                    LOG.debug('_re_heading: {}'.format(heading))
                    heading_ind = ind
                    state = 'heading'
                else:
                    state = 'before'

                eof = ind+1 not in range(len(section['lines']))
                if len(heading_char_inds) >= 1 and heading is not None and (eof or state == 'before'):
                    LOG.debug('Deleting lines at: {}'.format([heading_ind] + heading_char_inds[1:]))
                    ind_offset = 0
                    for del_ind in [heading_ind] + heading_char_inds[1:]:
                        LOG.debug("Deleting line: {}".format(section['lines'][del_ind + ind_offset]))
                        del section['lines'][del_ind + ind_offset]
                        ind_offset -= 1
                    ind += ind_offset

                    priv_fold_name = section.get('fold_name', None)

                    last_section_end = get_last_index(
                        section['lines'][:ind],
                        [''],
                        fallback=ind,
                    )

                    if last_section_end is None or ind < 2:
                        section['fold_name'] = heading
                    else:
                        LOG.debug('Creating new fold')
                        new_section = {
                            'lines': section['lines'][last_section_end + 1:],
                            'fold_name': heading,
                        }
                        section_level = self._get_section_level(heading_char)
                        if section_level != 0:
                            new_section['section_level'] = section_level
                        if 'subsections' in section:
                            new_section['subsections'] = section['subsections']
                            del section['subsections']
                        LOG.debug('section start: {}'.format(last_section_end))
                        LOG.debug('section level: {}'.format(section_level))
                        LOG.debug('new section: {}'.format(new_section))
                        section['lines'] = section['lines'][:last_section_end]
                        sections.insert(sec_ind + 1, new_section)

                    if (priv_fold_name is not None and
                            priv_fold_name.startswith('..') and
                            priv_fold_name.endswith(heading)):
                        section['fold_name'] = heading

                    state = 'before'
                    LOG.debug('state: {}, ind: {}'.format(state, ind))

    def _get_header_end_ind(self, lines):
        return get_last_index(lines, self._HEADER_END_LINES[self._preset])

    def _update_header(self):

        ind = -1
        while True:
            ind += 1

            try:
                line = self._lines[ind]
            except IndexError:
                break

            if line in ['---', '']:
                del self._lines[ind]
                ind -= 1
            else:
                break

        header_start = 0
        header_end = self._get_header_end_ind(self._lines)
        header_fold_unbalance = 0

        if header_end is not None:
            for _ in range(header_start, header_end + 1):
                fold = self._get_line_fold(self._lines[header_start])
                header_fold_unbalance -= fold['change']
                del self._lines[header_start]

        header = self._get_rendered_template('defaults_header').split('\n')
        for line in header:
            fold = self._get_line_fold(line)
            header_fold_unbalance += fold['change']
            LOG.debug('fold change: {}, line: {}'.format(fold['change'], line))
        LOG.debug('header_fold_unbalance in from _get_rendered_template: {}'.format(
            header_fold_unbalance,
        ))

        header_end = insert_list(
            self._lines,
            header_start,
            header,
        )

        # Separate header and body by empty lines.
        eof = header_end+1 not in range(len(self._lines))
        if eof:
            self._lines.append('')

        if self._lines[header_end+1] == '#':
            self._lines[header_end+1] = ''

        # not eof and not self._lines[header_end+1].startswith('#') or
        empty_line_count = 0
        wanted_empty_line_count = int(self._config['wanted_empty_lines_between_items'])
        for ind, line in enumerate(self._lines[header_end+1:]):
            if line == '':
                empty_line_count += 1
            else:
                break

        if empty_line_count < wanted_empty_line_count:
            self._lines[header_end + 1:header_end + 1] = [''] * (wanted_empty_line_count - empty_line_count)
        else:
            for _ in range(wanted_empty_line_count, empty_line_count):
                del self._lines[header_end + 1]

        LOG.debug('self._last_line_fold_yaml_block: {}'.format(self._last_line_fold_yaml_block))
        self._lines.extend(self._get_closing_folds(
            header_fold_unbalance,
            self._last_line_fold_yaml_block,
        ))

    @staticmethod
    def _check_ends_with_yaml_block(lines):
        previous_leading_spaces = 0
        leading_spaces = 0
        yaml_block = False
        for line in lines:
            if line in ['', '# ]]]']:
                continue

            previous_leading_spaces = leading_spaces
            leading_spaces = len(line) - len(line.lstrip(' '))

            if leading_spaces < previous_leading_spaces:
                yaml_block = False
            elif line.endswith(': |'):
                yaml_block = True

        return yaml_block

    def _reformat_variables(self, sections):
        LOG.debug('Called _reformat_variables with sections: {}'.format(sections))
        sec_ind = -1
        while True:
            sec_ind += 1
            try:
                section = sections[sec_ind]
            except IndexError:
                LOG.debug("break")
                break

            LOG.debug('Processing sec_ind: {}, section: {}'.format(sec_ind, section))

            lines = section.get('lines', [])
            ind = -1
            while True:
                ind += 1
                try:
                    line = lines[ind]
                except IndexError:
                    break

                if re.search(r'^# \.\. envvar::', line):
                    del lines[ind]
                    ind -= 1
                    continue

                variable_name_re = re.search(
                    r'^(?P<var_name>\w+):\s*(?P<yaml_block>\|?)',
                    line,
                )
                if not variable_name_re:
                    continue

                LOG.debug('sections: {}'.format(sections))
                LOG.debug('Processing section: {}'.format(section))
                LOG.debug('Processing line: {}'.format(line))

                new_section = {}
                var_name = variable_name_re.group('var_name')
                self._var_names.add(var_name)
                LOG.debug('Found variable {} at line: {}'.format(var_name, ind))

                begin_section_line_ind = ind
                for rsearch_ind, rsearch_line in reversed(list(enumerate(lines[:ind]))):
                    if rsearch_line.startswith('#'):
                        begin_section_line_ind = rsearch_ind
                    else:
                        break
                LOG.debug("begin_section_line_ind: {}".format(begin_section_line_ind))

                new_section['fold_name'] = '.. envvar:: {var_name}'.format(
                    var_name=var_name,
                )

                next_entry_start_ind = get_first_match(
                    r'^[^ ]',
                    lines[ind + 1:],
                    ind_offset=ind + 1,
                )
                LOG.debug('next_entry_start_ind: {}, line: {}'.format(
                    next_entry_start_ind,
                    lines[next_entry_start_ind] if next_entry_start_ind is not None else '%',
                ))

                if begin_section_line_ind == 0:
                    LOG.debug('Updating current section with: {}'.format(new_section))
                    section.update(new_section)

                    if next_entry_start_ind is not None:
                        LOG.debug("Splitting section into two sections. Moving next part into its own section")
                        new_section['lines'] = lines[next_entry_start_ind:]
                        sections[sec_ind + 1:sec_ind + 1] = [deepcopy(section)]

                        sections[sec_ind + 1].pop('fold_name', None)
                        sections[sec_ind + 1]['lines'][0:next_entry_start_ind] = []

                        section['lines'][next_entry_start_ind:] = []
                        section.pop('subsections', None)

                else:
                    sections[sec_ind + 1:sec_ind + 1] = [deepcopy(section)]

                    sections[sec_ind + 1].pop('fold_name', None)
                    sections[sec_ind + 1]['lines'][0:begin_section_line_ind] = []
                    section['lines'][begin_section_line_ind:] = []

                    if 'fold_name' in section:
                        LOG.debug("Splitting section into two sections. Moving variable start into new subsection.")
                        section.setdefault('subsections', [])
                        section['subsections'].append(sections[sec_ind + 1])
                        del sections[sec_ind + 1]
                    else:
                        LOG.debug("Splitting section into two sections. Moving variable start into new section.")
                        section.pop('subsections', None)

            if 'subsections' in section:
                self._reformat_variables(section['subsections'])
