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

Tests for module spat.sigfile
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

import numpy as np
from bitstring import Bits
from spat.chipidentify import ChipIdentify

def vname(x):
    return 'v%03d'%(x+1)

class ChipIdentifyTests(TestCase):
    'ChipIdentify unit tests'

    def setUp(self):
        self.ci = ChipIdentify(fileName=resource_filename('spat.tests', 'data/example_setup.xml'))

    def test_init(self):
        with patch('spat.chipidentify.ChipIdentify.load') as m_load, \
                patch('os.path.isfile') as m_isfile, \
                patch('spat.chipidentify.ChipIdentify.__len__') as m_len, \
                patch('spat.chipidentify.ChipIdentify.setup') as m_setup:
            m_isfile.return_value = True
            m_len.return_value = 3

            ci = ChipIdentify('foo', 10)


        self.assertEqual(ci.n_bits, 10)
        self.assertEqual(ci.fileName, 'foo')

        m_load.assert_called()
        m_isfile.assert_called_with('foo')
        m_len.assert_called()
        m_setup.assert_called()


    def test_init_parse_error(self):
        with patch('spat.chipidentify.ChipIdentify.load') as m_load, \
                patch('os.path.isfile') as m_isfile, \
                patch('spat.chipidentify.ChipIdentify.__len__') as m_len, \
                patch('spat.chipidentify.ChipIdentify.setup') as m_setup:
            m_isfile.return_value = True
            m_len.return_value = 3
            m_load.side_effect = ParseError

            ci = ChipIdentify('bar', 100)

        m_isfile.assert_called_with('bar')
        m_load.assert_called()


    def test_init_no_file(self):
        with patch('os.path.isfile') as m_isfile, \
                patch('spat.chipidentify.ChipIdentify.__len__') as m_len, \
                patch('os.path.isdir') as m_isdir, \
                patch('os.makedirs') as m_makedirs, \
                patch('spat.chipidentify.ChipIdentify.setup') as m_setup:
            m_isfile.return_value = False
            m_len.return_value = 3
            m_isdir.return_value = False

            ci = ChipIdentify('baz/lur', 10)

        m_isfile.assert_called_with('baz/lur')
        m_isdir.assert_called_with('baz')
        m_makedirs.assert_called_with('baz')


    def test_setup(self):
        self.ci.setup()

        self.assertIsInstance(self.ci.signatureMap, dict)
        self.assertIsInstance(self.ci.noiseDistMap, dict)
        self.assertIsInstance(self.ci.interChipDistMap, dict)
        self.assertIsInstance(self.ci.unstableBits, dict)
        self.assertIsInstance(self.ci.measCount, dict)

    def test_clear(self):
        with patch.object(self.ci, 'setup') as m_setup, \
                patch.object(self.ci, 'save') as m_save:
            self.ci.clear()

        m_setup.assert_called()
        m_save.assert_called()

    def test_len(self):
        with patch.object(self.ci, 'signatureMap') as m_signatureMap:
            retval = len(self.ci)

        m_signatureMap.__len__.assert_called()
        self.assertEqual(retval, 0)

    def test_load(self):

        self.ci.fileName = resource_filename('spat.tests', 'data/signatures.xml')
        self.ci.load()

        self.assertEqual(self.ci.n_bits, 1024)
        self.assertEqual(len(self.ci.noiseDistMap), 32)
        self.assertEqual(len(self.ci.signatureMap), 32)
        self.assertEqual(len(self.ci.unstableBits), 32)

        for i in range(32):
            iname = vname(i)
            self.assertIn(iname, self.ci.measCount)
            self.assertGreater(self.ci.measCount[iname], 32)

            self.assertEqual(len(self.ci.interChipDistMap[iname]), 31)
            for j in range(32):
                if i == j:
                    continue

                jname = vname(j)
                self.assertGreater(len(self.ci.interChipDistMap[iname][jname]), 31)
                ic_avg = np.mean(self.ci.interChipDistMap[iname][jname])
                self.assertGreater(ic_avg, 200)
                self.assertLess(ic_avg, 800)

            self.assertGreater(len(self.ci.noiseDistMap[iname]), 30)
            nd_avg = np.mean(self.ci.noiseDistMap[iname])
            self.assertGreater(nd_avg, 1)
            self.assertLess(nd_avg, 20)

            self.assertEqual(len(self.ci.signatureMap[iname]), 1024)
            sig_hw = self.ci.signatureMap[iname].count(1)
            self.assertGreater(sig_hw, 384)
            self.assertLess(sig_hw, 640)

            self.assertEqual(len(self.ci.unstableBits[iname]), 1024)
            sig_hw = self.ci.unstableBits[iname].count(1)
            self.assertGreater(sig_hw, 0)
            self.assertLess(sig_hw, 96)

    def test_save(self):
        self.ci.fileName = resource_filename('spat.tests', 'data/signatures.xml')
        self.ci.load()

        m_open = mock_open()
        with patch('__builtin__.open', m_open, create=True):
            self.ci.save()

        m_open.assert_called_with(os.path.abspath(self.ci.fileName), 'w')
        with open(self.ci.fileName, 'r') as f_expect:
            expect = f_expect.read()
        self.assertEqual(expect, m_open().write.call_args_list[0][0][0])
