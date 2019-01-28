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

from bitstring import Bits, BitArray
from spat.simulator.ropuf import Simulator, NoiseWorker
from spat.tests.simulator.test_abstractsimulator import AbstractSimulatorUnitTests


class ROPUFSimulatorUnitTests(AbstractSimulatorUnitTests):
    'Unit tests for the spat.simulator.ropuf.Simulator class'

    target_class = 'spat.simulator.abstractsimulator.AbstractSimulator'
    target_class = Simulator

    def test_characterize(self):
        sim = self.makeMockSimulator()
        cid = MagicMock()

        with patch('Tkinter.Toplevel') as m_toplevel, \
                patch('Tkinter.Label') as m_label, \
                patch('ttk.Progressbar') as m_progressbar:
            sim.characterize(cid, 2)

        m_toplevel.assert_called()
        m_toplevel().title.assert_called()
        self.assertEqual(m_label.call_args[0][0], m_toplevel())
        self.assertIn('Measuring', m_label.call_args[1]['text'])
        m_label().pack.assert_called()
        m_progressbar.assert_called_with(m_toplevel(), maximum=sim.numVirtChips)
        m_progressbar().pack.assert_called()

        cid.process_sig.assert_has_calls([
            call('v001', BitArray('0b11')),
            call('v001', BitArray('0b11')),
            call('v002', BitArray('0b11')),
            call('v002', BitArray('0b11'))])

        m_progressbar().step.assert_has_calls([
            call(),
            call()])
        m_toplevel().update.assert_has_calls([
            call(),
            call()])

        m_progressbar().stop.assert_called()
        m_toplevel().destroy.assert_called()

    def test_next(self):
        pass
