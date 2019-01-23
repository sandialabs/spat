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

Tests for module spat.simulator.abstractsimulator
'''

from __future__ import print_function
try:
    from unittest.mock import patch, call, MagicMock, mock_open
    from unittest import TestCase, main, skipIf
    PY3 = True
except ImportError:
    from mock import patch, call, MagicMock, mock_open
    from unittest2 import TestCase, main, skipIf
    PY3 = False

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import os
import xml.etree.ElementTree as etree
import pkg_resources

from bitstring import Bits
from spat.simulator.abstractsimulator import AbstractSimulator, NoiseWorker


class AbstractSimulatorUnitTests(TestCase):
    'sigfile unit tests'

    @patch('os.path.isdir')
    @patch('os.makedirs')
    def test_init(self, m_makedirs, m_isdir):
        m_isdir.return_value = False

        o = AbstractSimulator(36)

        self.assertEqual(o.n_bits, 36)
        self.assertIsNone(o.bit_flips)
        self.assertEqual(o.setup_file, 'data/Simulator/simulator_setup.xml')
        m_isdir.assert_called_with('data/Simulator')
        m_makedirs.assert_called_with('data/Simulator')

    @patch('os.path.isfile')
    def test_setup(self, m_isfile):
        m_isfile.return_value = True

        o = AbstractSimulator()
        with patch.object(o, 'loadFromFile') as m_loadFromFile:
            o.setup(1, 2, 3, 5, 7)

        self.assertEqual(o.params, {
            'param_mu': 1,
            'param_sd': 2,
            'noise_mu': 3,
            'noise_sd': 5
        })
        m_isfile.assert_called_with(o.setup_file)
        m_loadFromFile.assert_called()

        m_isfile.return_value = False

        with patch.object(o, 'generateSetup') as m_generateSetup:
            o.setup(1, 2, 3, 5, 7)

        self.assertEqual(o.params, {
            'param_mu': 1,
            'param_sd': 2,
            'noise_mu': 3,
            'noise_sd': 5
        })
        m_isfile.assert_called_with(o.setup_file)
        m_generateSetup.assert_called_with(7)

    def makeMockSimulator(self):
        ex_file_path = pkg_resources.resource_filename('spat.tests', 'data/example_setup.xml')
        obj = etree.parse(ex_file_path)

        with patch('spat.simulator.abstractsimulator.AbstractSimulator.__init__',
                return_value=None) as m_init:
            sim = AbstractSimulator()

        sim.setup_file = 'foo'
        with patch('xml.etree.ElementTree.parse', return_value=obj) as m_parse:
            sim.loadFromFile()

        m_parse.assert_called_with('foo')

        return sim

    def test_loadFromFile(self):
        sim = self.makeMockSimulator()

        self.assertEqual(sim.realValues, [[1, 2, 3], [7, 11, 17]])
        self.assertEqual(sim.chipNames, ['t001', 't002'])
        self.assertEqual(sim.params,
            {'noise_sd': 0.1,
             'param_mu': 13.0,
             'noise_mu': 0.0,
             'param_sd': 5.0})
        self.assertEqual(sim.numVirtChips, 2)
        self.assertEqual(sim.numElements, 3)

    def test_getChipName(self):
        with patch('spat.simulator.abstractsimulator.AbstractSimulator.__init__',
                return_value=None) as m_init:
            sim = AbstractSimulator()
        self.assertEqual(sim.getChipName(5), 'v006')

    def test_makeSigFile(self):
        sim = self.makeMockSimulator()
        
        with patch(('builtins' if PY3 else '__builtin__') + '.open',
                new_callable=mock_open()) as m_open, \
            patch('os.makedirs') as m_makedirs, \
            patch.object(sim, 'next') as m_next:
            m_next.return_value.hex = 'foo'
            sim.makeSigFile('bar')

        m_open.assert_called_with('bar', 'wb')
        m_open().write.assert_called_with(
            b'<?xml version="1.0" encoding="UTF-8" ?>\n'
            b'<chip_list>\n'
            b'<chip name="v001">\n'
            b'<sig encoding="hex">foo</sig>\n'
            b'</chip>\n'
            b'<chip name="v002">\n'
            b'<sig encoding="hex">foo</sig>\n'
            b'</chip>\n'
            b'</chip_list>\n')
        m_open().close.assert_called()

    def test_getSetupStr(self):
        sim = self.makeMockSimulator()

        self.assertEqual(
            sim.getSetupStr(),
            'P_mu=13.0, P_sd=5.0, E_mu=0.000, E_sd=0.100')

    def test_noise(self):
        sim = self.makeMockSimulator()

        with patch('random.normalvariate') as m_normvar:
            retval = sim.noise()

        m_normvar.assert_called_with(sim.params['noise_mu'], sim.params['noise_sd'])
        self.assertEqual(retval, m_normvar())

    def test_next(self):
        sim = self.makeMockSimulator()
        with self.assertRaises(NotImplementedError):
            sim.next()
