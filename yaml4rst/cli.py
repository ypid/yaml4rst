# -*- coding: utf-8 -*-

"""
Command line interface of yaml4rst
"""

from __future__ import absolute_import, division, print_function

import logging
import textwrap
import argparse
import re
import traceback

from ._meta import __version__
from .reformatter import YamlRstReformatter, YamlRstReformatterError, LOG
from .defaults import DEFAULTS

__all__ = ['main']


def parse_kv(vars_string):
    extra_vars = {}
    if vars_string:
        for kv in re.split(r'[,;]\s*', vars_string):
            k, v = kv.split('=')
            extra_vars[k] = v
    return extra_vars


WARNING_COUNT = 0  # pylint: disable=global-statement


def count_warning(*args, **kwargs):  # pylint: disable=unused-argument
    global WARNING_COUNT  # pylint: disable=global-statement
    WARNING_COUNT += 1


def get_args_parser():
    args_parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
            Linting/reformatting tool for YAML files documented with inline RST
        """),
        # epilog=__doc__,
    )
    args_parser.add_argument(
        '-V', '--version',
        action='version',
        version=__version__,
    )
    args_parser.add_argument(
        '-d', '--debug',
        help="Write debugging and higher to STDOUT|STDERR.",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )
    args_parser.add_argument(
        '-v', '--verbose',
        help="Write information and higher to STDOUT|STDERR.",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
    )
    args_parser.add_argument(
        '-q', '--quiet', '--silent',
        help="Only write errors and higher to STDOUT|STDERR.",
        action="store_const",
        dest="loglevel",
        const=logging.ERROR,
    )
    args_parser.add_argument(
        '-n', '--no-warn-summary',
        help="If multiple warnings occur in quiet mode,"
        " a summary error message is emitted."
        " This switch suppresses it.",
        dest="warning_summary",
        action='store_false',
        default=True,
    )
    args_parser.add_argument(
        'input_file',
        help="One or more file paths to be processed."
        " '-' will read from STDIN.",
        nargs='+',
    )
    args_parser.add_argument(
        '-o', '--output-file',
        help="One or more file paths where the output should be written to."
        " Defaults to '-' which will write the output from a single input file to STDOUT."
        " If multiple input files where given, and --in-place is not used then the number of"
        " output files must match the number of input files.",
        default=['-'],
        nargs='+',
    )
    args_parser.add_argument(
        '-i', '--in-place',
        help="Edit the input file(s) in place.",
        action='store_true',
        default=False,
    )
    args_parser.add_argument(
        '-p', '--preset',
        help="Which preset to use."
        " Default: %(default)s.",
        default=DEFAULTS['preset'],
    )
    args_parser.add_argument(
        '-e', '--config-kv',
        help="Additional configuration,"
        " refer to the docs of yaml4rst for details.",
        action='append',
    )

    return args_parser


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()
    if args.loglevel is None:
        args.loglevel = logging.WARNING
    logging.basicConfig(
        format='%(levelname)s{}: %(message)s'.format(
            ' (%(filename)s:%(lineno)s)' if args.loglevel <= logging.DEBUG else '',
        ),
        level=args.loglevel,
    )
    if not LOG.isEnabledFor(logging.WARNING):
        LOG.warning = count_warning

    if not args.in_place and len(args.input_file) != len(args.output_file):
        args_parser.error(
            "The number of input files does not match the number of output files in non-in-place mode."
        )

    for ind, input_file in enumerate(args.input_file):
        reformatter = YamlRstReformatter(
            preset=args.preset,
            config=parse_kv(', '.join(args.config_kv)) if args.config_kv else {},
        )

        try:
            reformatter.read_file(input_file)
            reformatter.reformat()

            reformatter.write_file(
                input_file if args.in_place else args.output_file[ind],
            )
        except YamlRstReformatterError as err:
            LOG.debug(traceback.format_exc())
            LOG.error(err)
        except NotImplementedError as err:
            LOG.debug(traceback.format_exc())
            LOG.error(err)

    if args.warning_summary and WARNING_COUNT > 1:
        logging.error("You missed {} warnings in quiet mode!".format(
            WARNING_COUNT
        ))

if __name__ == '__main__':
    main()
