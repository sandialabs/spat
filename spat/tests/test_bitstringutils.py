'''
NOTICE

Copyright 2018 National Technology & Engineering Solutions of Sandia, LLC
(NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
Government retains certain rights in this software.

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

---

Tests for module spat.randomness
'''

from __future__ import print_function
import os
import sys
from pkg_resources import resource_filename
if sys.version_info[0] > 2:
    from unittest.mock import patch, call, MagicMock, mock_open
    from unittest import TestCase, main, skipIf
    from io import StringIO
else:
    from mock import patch, call, MagicMock, mock_open
    from unittest2 import TestCase, main, skipIf
    from StringIO import StringIO
from xml.etree.ElementTree import ParseError
import random
import itertools

from datetime import datetime

import numpy as np
from numpy import isclose
from numpy.testing import assert_almost_equal
from bitstring import Bits
import spat.bitstringutils as utils


class BitstringUtilsTests(TestCase):
    'bitstring utilities tests'

    def test_hd(self):
        self.assertEqual(utils.hd(Bits('0b0101'), Bits('0b1010')), 4)
        self.assertEqual(utils.hd(Bits('0b0101'), Bits('0b0100')), 1)

    def test_hw(self):
        self.assertEqual(utils.hw(Bits('0b0101')), 2)
        self.assertEqual(utils.hw(Bits('0b0100')), 1)

    def test_as_ints(self):
        bs = Bits('0b0101')
        self.assertEqual(utils.as_ints(bs), '0101')
