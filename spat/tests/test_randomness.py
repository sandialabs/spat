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
import spat.randomness
from spat.chipidentify import ChipIdentify

SP800_22_examples = [
        # page 2-3 (PDF 25)
        {
            'fun':spat.randomness.monobit,
            'input':Bits(bin='1011010101'),
            'output':0.527089},
        {
            'fun':spat.randomness.monobit,
            'input':Bits(bin='1100100100001111110110101010001000100001011010001100001000110100110001001100011001100010100010111000'),
                'output':0.109599},
        # page 2-33 (PDF 55)
        {       'fun':spat.randomness.cum_sum,
                'input':Bits(bin='1011010111'),
                'output':0.4116588},
        {       'fun':spat.randomness.cum_sum,
                'input':Bits(bin='1100100100001111110110101010001000100001011010001100001000110100110001001100011001100010100010111000'),
                'output':0.219194},
        # page 2-7 (PDF 29)
        {       'fun':spat.randomness.runs_test,
                'input':Bits(bin='1001101011'),
                'output':0.147232},
        {       'fun':spat.randomness.runs_test,
                'input':Bits(bin='1100100100001111110110101010001000100001011010001100001000110100110001001100011001100010100010111000'),
                'output':0.500798},
        ]

def randBitString(length):
    return Bits(uint=random.getrandbits(length), length=length)

class RandomnessTests(TestCase):
    'randomness functions tests'

    def setUp(self):
        self.ci = ChipIdentify(fileName=resource_filename('spat.tests', 'data/example_setup.xml'))

    def test_sp800_22_examples(self):
        "SP800-22rev1a Examples"
        for example in SP800_22_examples:
            with self.subTest(name=example['fun'].__name__):
                our_output = example['fun'](example['input'])[0]
                assert_almost_equal(example['output'], our_output, 6)

    def test_random_inputs(self):
        numBits = 2**10
        numTrials = 2**12

        # For timing the execution
        startTime = datetime.now()
        print("Number of bits in each string: %d, "
            "number of trials: %d" % (numBits, numTrials))

        randBitStrings = list(map(randBitString, itertools.repeat(numBits, numTrials)))

        for randomness_fun in [
                spat.randomness.entropy,
                spat.randomness.min_entropy,
                spat.randomness.monobit,
                spat.randomness.runs_test,
                spat.randomness.runs_test2,
                spat.randomness.cum_sum]:

            results = map(randomness_fun, randBitStrings)
            result_values, result_pass = zip(*results)
            result_values_a = np.fromiter(result_values, np.float)
            result_pass_a = np.fromiter(result_pass, np.float)

            print("%20s: Average p-value: %f, pass: %f" % (
                randomness_fun.__name__,
                result_values_a.mean(),
                result_pass_a.mean()))

        print(__name__+' time: '+str(datetime.now() - startTime))
