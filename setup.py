#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

__version__ = None
__license__ = None
__author__ = None
exec(open('yaml4rst/_meta.py').read())
author = re.search(r'^(?P<name>[^<]+) <(?P<email>.*)>$', __author__)

# https://packaging.python.org/
setup(
    name='yaml4rst',
    version=__version__,
    description='Linting/reformatting tool for YAML files documented with inline RST',
    long_description=open(os.path.join(here, 'README.rst')).read(),
    url='https://github.com/ypid/yaml4rst',
    author=author.group('name'),
    author_email=author.group('email'),
    # Basically redundant but when not specified `./setup.py --maintainer` will
    # return "UNKNOWN".
    maintainer=author.group('name'),
    maintainer_email=author.group('email'),
    license=__license__,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: DFSG approved',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        # Could be supported but I don’t see a real need for this.
        # Unicode support would need to be worked around for Python 2 support.
        #  'Programming Language :: Python :: 2',
        #  'Programming Language :: Python :: 2.6',
        #  'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        #  'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Text Processing',
    ),
    keywords='YML YAML RST reStructuresText Ansible DebOps linting docs documentation',
    packages=find_packages(),
    install_requires=[
        # Debian packages: python-yaml python3-yaml python-jinja2 python3-jinja2
        'PyYAML',
        'Jinja2',
    ],
    extras_require={
        'test': [
            'nose',
            'nose2',
            'testfixtures',
            'tox',
            'flake8',
            'pylint',
            'coverage',
            'yamllint',
        ],
        #  'docs': [],  # See docs/requirements.txt
    },
    entry_points={
        'console_scripts': [
            'yaml4rst = yaml4rst.cli:main',
        ],
    },
)
