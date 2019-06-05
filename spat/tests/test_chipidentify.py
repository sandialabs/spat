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
from numpy.testing import assert_almost_equal
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
        with patch('builtins.open' if sys.version_info[0] > 2 \
                else '__builtin__.open', m_open, create=True):
            self.ci.save()

        m_open.assert_called_with(os.path.abspath(self.ci.fileName), 'w')

        m_open_load = mock_open(read_data=m_open().write.call_args_list[0][0][0])
        with patch('builtins.open' if sys.version_info[0] > 2 \
                else '__builtin__.open', m_open_load, create=True), \
                patch('os.path.isfile', return_value=True):
            test_ci = ChipIdentify(fileName=resource_filename('spat.tests', 'bogus'))

        self.assertEqual(self.ci, test_ci)

    def test_identify(self):
        mm_d = {'t1': 0.5, 't2': 0.3, 't3': 0.1}
        with patch.object(self.ci, 'match_map', return_value=mm_d) as m_match_map:
            retval = self.ci.identify('foo')

        m_match_map.assert_called_with('foo')
        self.assertEqual(retval, ('t3', 0.1))

    def test_match_map(self):
        self.ci.signatureMap = {
                'd1': Bits('0xdeadbeef'),
                'd2': Bits('0xfa1afe13'),
                'd3': Bits('0x00010203')
                }
        retval = self.ci.match_map(Bits('0xdeedbeaf'))

        self.assertEqual(
                retval,
                {
                    'd1': 0.001953125,
                    'd2': 0.0146484375,
                    'd3': 0.01953125
                })

    def test_add(self):
        self.assertNotIn('test', self.ci.signatureMap)
        self.assertNotIn('test', self.ci.measCount)
        self.ci.add('test', Bits('0xf00d200b'))
        self.assertIn('test', self.ci.signatureMap)
        self.assertEqual(self.ci.signatureMap['test'], Bits('0xf00d200b'))
        self.assertIn('test', self.ci.measCount)
        self.assertEqual(self.ci.measCount['test'], 0)

    def test_get_sig(self):
        self.ci.signatureMap['foo'] = 'bar'
        self.assertEqual(self.ci.get_sig('foo'), 'bar')

    def test_process_sig(self):
        self.ci.signatureMap['foo'] = 'baz'
        self.ci.measCount['foo'] = 42
        with patch.object(self.ci, 'add') as m_add, \
                patch.object(self.ci, 'update_noise_dist') as m_noise, \
                patch.object(self.ci, 'update_unstable_bitmap') as m_unstable, \
                patch.object(self.ci, 'update_interchip_dists') as m_interchip:
            self.ci.process_sig('foo', 'bar')

        self.assertEqual(self.ci.measCount['foo'], 43)
        m_unstable.assert_called_with('foo', 'bar')
        m_noise.assert_called_with('foo', 'bar')
        m_interchip.assert_called_with('foo', 'bar')

    def test_get_meas_count(self):
        self.ci.fileName = resource_filename('spat.tests', 'data/signatures.xml')
        self.ci.load()

        self.assertEqual(self.ci.get_meas_count('v001'), 34)
        self.assertEqual(self.ci.get_meas_count('bogus'), 0)

    def test_num_unstable_bits(self):
        self.ci.unstableBits['foo'] = Bits('0b00010101')

        self.assertEqual(self.ci.get_num_unstable_bits('foo'), 3)

    def test_unstable_bits_valid(self):
        self.assertEqual(self.ci.unstable_bits_valid('foo'), False)

    def test_unstable_bits_valid_1(self):
        self.ci.measCount['foo'] = 1
        self.assertEqual(self.ci.unstable_bits_valid('foo'), False)

    def test_unstable_bits_valid_2(self):
        self.ci.measCount['foo'] = 2
        self.assertEqual(self.ci.unstable_bits_valid('foo'), True)

    def test_get_noise_dist_avg(self):
        self.ci.noiseDistMap['foo'] = range(5)

        self.assertEqual(self.ci.get_noise_dist_avg('foo'), 2)

    def test_get_inter_dist_avg_empty(self):
        self.ci.interChipDistMap = {
                'v%03d' % x: {
                    'v%03d' % y: [x*x + y] for y in range(1) if x!=y
                    } for x in range(10)
                }

        self.assertAlmostEqual(
                self.ci.get_inter_dist_avg('v001'),
                1)

    def test_get_inter_dist_avg(self):
        self.ci.interChipDistMap = {
                'v%03d' % x: {
                    'v%03d' % y: [x*x + y] for y in range(10) if x!=y
                    } for x in range(10)
                }

        self.assertAlmostEqual(
                self.ci.get_inter_dist_avg('v003'),
                13.666666666666666)

# Parameters used to generate data file:
# <setup noise_mu="0.0" noise_sd="0.1" param_mu="13.0" param_sd="5.0" />
    def test_get_all_noise_dists(self):
        self.ci.fileName = resource_filename('spat.tests', 'data/signatures.xml')
        self.ci.load()

        val = self.ci.get_all_noise_dists()

        self.assertEqual(len(val), 2001)
        self.assertLess(6.5, np.mean(val))
        self.assertLess(np.mean(val), 26)
        self.assertLess(1, np.std(val))
        self.assertLess(np.std(val), 10)

    def test_get_all_inter_chip_dists(self):
        self.ci.fileName = resource_filename('spat.tests', 'data/signatures.xml')
        self.ci.load()

        val = self.ci.get_all_inter_chip_dists()

        self.assertEqual(len(val), 64015)
        self.assertLess(448, np.mean(val))
        self.assertLess(np.mean(val), 576)
        self.assertLess(1, np.std(val))
        self.assertLess(np.std(val), 32)

    def test_prob_alias(self):
        self.ci.fileName = resource_filename('spat.tests', 'data/signatures.xml')
        self.ci.load()

        threshold, prob = self.ci.prob_alias(False)
        self.assertLess(10, threshold)
        self.assertLess(threshold, 30)
        self.assertLess(prob, 1e-20)

    def test_prob_alias_plot(self):
        self.ci.interChipDistMap = {
                'v%03d' % x: {
                    'v%03d' % y: [x**2 + y] for y in range(3) if x!=y
                    } for x in range(3)
                }
        self.ci.noiseDistMap = {
                'v%03d' % x: range(x*2, (x+1)*2) for x in range(2)
                }


        with patch('matplotlib.pyplot.ion') as m_ion, \
                patch('matplotlib.pyplot.clf') as m_clf, \
                patch('matplotlib.pyplot.hist') as m_hist, \
                patch('matplotlib.pyplot.plot') as m_plot, \
                patch('matplotlib.pyplot.axvline') as m_axvline:
            threshold, prob = self.ci.prob_alias(True)

        m_ion.assert_called_with()
        m_clf.assert_called_with()
        assert_almost_equal(
                sorted(m_hist.call_args_list[0][0][0]),
                range(4))
        self.assertEqual(
                m_hist.call_args_list[0][1],
                {'normed':True})
        assert_almost_equal(
                sorted(m_hist.call_args_list[1][0][0]),
                [1, 1, 2, 3, 4, 5])
        self.assertEqual(
                m_hist.call_args_list[1][1],
                {'normed':True})
        self.assertEqual(
                m_plot.call_args_list[0][0][0],
                range(0, 3))
        self.assertEqual(
                m_plot.call_args_list[1][0][0],
                range(0, 5))
        assert_almost_equal(
                m_plot.call_args_list[0][0][1],
                np.array([0.145192 , 0.3229238, 0.3227597]))
        assert_almost_equal(
                m_plot.call_args_list[1][0][1],
                np.array([0.0, 4.19025371e+06, 2.17501421e-01,
                           7.01039980e-02, 2.63226824e-02]), 2)
# TODO there must be something random about pyplot.hist()
        m_axvline.assert_called_with(threshold)

