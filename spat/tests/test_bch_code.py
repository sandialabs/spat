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
from binascii import a2b_hex, b2a_hex

import numpy as np
from numpy import isclose
from numpy.testing import assert_almost_equal
from bitstring import Bits
import spat.randomness
from spat.chipidentify import ChipIdentify

from bchlib import BCH
from spat.simulator.ropuf import Simulator
from spat.bitstringutils import hd
from spat import bitstringutils
from spat.bch_code import bch_code

class BCHTests(TestCase):
    'BCH encode/decode tests'

    def setUp(self):
        self.mySim = Simulator(setup_file=resource_filename('spat.tests', 'data/simulator_setup.py'))
        self.mySim.setup()

    def test_bchlib(self):
        firstMeasurement = self.mySim.next()
        print('First measurement:\n'+firstMeasurement.hex)
        myCoder = BCH(0x25AF, 20)
        helper_data = myCoder.encode(firstMeasurement.bytes)
        print("Helper data: "+str(b2a_hex(helper_data)))

        newMeasurement = self.mySim.next()
        print('Probably-Errored Measurement:\n' + newMeasurement.hex)
        n_err = hd(firstMeasurement, newMeasurement)
        print('Actual Bit Errors: '+str(n_err))
        self.assertLess(0, n_err)
        self.assertLess(n_err, 20)
        n_err_detected, corrected, _ = myCoder.decode(newMeasurement.bytes, helper_data)
        print('Detected Bit Errors: '+str(n_err_detected))
        print('Recovered:\n'+str(b2a_hex(corrected)))
        n_err_remaining = hd(firstMeasurement, corrected)
        print('Remaining errors: '+str(n_err_remaining))
        self.assertEqual(n_err_remaining, 0)

    def test_error_correction_repeat(self):
        first_meas = self.mySim.next()
        myCorrector = bch_code(first_meas)
        for _ in range(2**6):
            regen_meas = myCorrector.regenerate(self.mySim.next())
            self.assertEqual(regen_meas, first_meas)
