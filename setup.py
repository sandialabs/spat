#!/usr/bin/env python

"""
A Python TkInter GUI for visually measuring and
demonstrating physical uncloneable functions
---

Copyright (2014) Sandia Corporation. Under the terms of Contract
DE-AC04-94AL85000, there is a non-exclusive license for use of this
work by or on behalf of the U.S. Government. Export of this program
may require a license from the United States Government.

GPL Version 3
-------------
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import platform
import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requires = [
    'bitstring>=3.1,<3.2'
    ]

test_requires = []

if int(platform.python_version_tuple()[0]) < 3:
    requires.extend(['unittest2', 'mock'])
    test_requires.extend(['unittest2', 'mock'])

setup(
    name = "spat",
    version = "1.3-dev",
    author = "Ryan Helinski, Mitch Martin, Jason Hamlet, Todd Bauer and Bijan Fakhri",
    author_email = "rlhelinski@gmail.com",
    description = ("A Python TkInter GUI for visually measuring and "
                   "demonstrating physical uncloneable functions (PUFs)"),
    license = "GPLv3",
    keywords = "education hardware security random physical unclonable function",
    url = "http://github.com/sandialabs/spat",
    packages=['spat'],
    install_requires=requires,
    tests_require=test_requires,
    test_suite='spat.tests',
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Education",
        "Topic :: Security",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
)
