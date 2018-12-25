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
try:
    from unittest.mock import patch, call, MagicMock, mock_open
    from unittest import TestCase, main, skipIf
    PY3 = True
except ImportError:
    from mock import patch, call, MagicMock, mock_open
    from unittest2 import TestCase, main, skipIf
    PY3 = False

from bitstring import Bits
from spat import sigfile

class SigFileTest(TestCase):
    'sigfile unit tests'

    magna_carta = 'birdseeddirtfeet'

    @patch('spat.sigfile.SigFile.open')
    def test_init(self, m_open):
        fn = 'foo'; nb = 42; md='bar'
        sf = sigfile.SigFile(fn, nb, md)
        self.assertEqual(sf.fileName, fn)
        self.assertEqual(sf.n_bits, nb)
        m_open.assert_called_with(md)

    @patch('spat.sigfile.SigFile.save')
    def test_close(self, m_save):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('foo')
        sf.f = MagicMock()
        sf.f.mode = 'ab'

        sf.close()

        m_save.assert_called()
        sf.f.close.assert_called()

    @patch('os.path.isdir')
    def test_open_normal(self, m_isdir):
        m_isdir.return_value = True
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        with patch(('builtins' if PY3 else '__builtin__') + '.open',
               new_callable=mock_open()) as m_open:
            sf.open()
        m_open.assert_called_with('/path/to/foo', 'rb')
        m_isdir.assert_called_with('/path/to')

    @patch('os.path.isdir')
    @patch('os.makedirs')
    def test_open_mkdir(self, m_makedirs, m_isdir):
        m_isdir.return_value = False
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        with patch(('builtins' if PY3 else '__builtin__') + '.open',
               new_callable=mock_open()) as m_open:
            sf.open()
        m_open.assert_called_with('/path/to/foo', 'rb')
        m_isdir.assert_called_with('/path/to')
        m_makedirs.assert_called_with('/path/to')

    @patch('os.path.isdir')
    def test_next(self, m_isdir):
        m_isdir.return_value = True
        with patch(('builtins' if PY3 else '__builtin__') + '.open',
               mock_open(read_data='food')) as m_open:
            sf = sigfile.SigFile('/path/to/foo', 24)
        with patch.object(sf.f, 'read', MagicMock(side_effect=['foo', 'bar', 'no', 'baz'])):
            retval = sf.next()
            self.assertEqual(retval, Bits(bytes='foo'))
            retval = sf.next()
            self.assertEqual(retval, Bits(bytes='bar'))
            retval = sf.next()
            self.assertEqual(retval, Bits(bytes='baz'))
            sf.f.seek.assert_called_once_with(0)
