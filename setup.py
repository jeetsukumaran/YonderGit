#! /usr/bin/env python

############################################################################
##  setup.py
##
##  Copyright 2008 Jeet Sukumaran and Mark T. Holder.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this programm. If not, see <http://www.gnu.org/licenses/>.
##
############################################################################

"""
Package setup and installation.
"""
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup
from setuptools import find_packages

import sys
import os
import subprocess

version = "1.1.0"

setup(name='YonderGit',
      version=version,
      author='Jeet Sukumaran',
      author_email='jeetsukumaran@gmail.com',
      description="""\
Remote Git repository management utilities.""",
      license='GPL 3+',
      packages=[],
      package_dir={},
      package_data={},
      scripts=['scripts/ygit.py'],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      long_description="""\
Simplify the management of remote Git repositories by wrapping lower-level
filesystem and repository maintenance operations.""",
      classifiers = [
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU Library or  General Public License (GPL)",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            ],
      keywords='Git version control',
      )
