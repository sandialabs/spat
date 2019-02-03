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
if sys.version_info[0] > 2:
    from unittest.mock import patch, call, MagicMock, mock_open
    from unittest import TestCase, main, skipIf
    from io import StringIO
    builtin_pkg = 'builtins'
else:
    from mock import patch, call, MagicMock, mock_open
    from unittest2 import TestCase, main, skipIf
    from StringIO import StringIO
    builtin_pkg = '__builtin__'

from bitstring import Bits
from spat import sigfile

class SigFileUnitTests(TestCase):
    'sigfile unit tests'

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
        with patch(builtin_pkg + '.open',
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
        with patch(builtin_pkg + '.open',
               new_callable=mock_open()) as m_open:
            sf.open()
        m_open.assert_called_with('/path/to/foo', 'rb')
        m_isdir.assert_called_with('/path/to')
        m_makedirs.assert_called_with('/path/to')

    def test_open_bad_mode(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        self.assertRaises(ValueError, sf.open, 'x')

    @patch('os.path.isdir')
    def test_next(self, m_isdir):
        m_isdir.return_value = True
        with patch(builtin_pkg + '.open',
               mock_open(read_data='chair')) as m_open:
            sf = sigfile.SigFile('/path/to/foo', 24)
        with patch.object(sf.f, 'read', MagicMock(side_effect=[b'foo', b'bar', b'no', b'baz'])):
            retval = sf.next()
            self.assertEqual(retval, Bits(bytes=b'foo'))
            retval = sf.next()
            self.assertEqual(retval, Bits(bytes=b'bar'))
            retval = sf.next()
            self.assertEqual(retval, Bits(bytes=b'baz'))
            sf.f.seek.assert_called_once_with(0)

    def test_append_closed(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        sf.f = MagicMock()
        with patch.object(sf.f, 'closed', True):
           self.assertRaises(Exception, sf.append, 'foo')
        with patch.object(sf.f, 'mode', 'rfoo'):
           self.assertRaises(Exception, sf.append, 'foo')

    def test_append(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        sf.f = MagicMock()
        sf.f.closed = False
        sf.f.mode = 'ab'
        foo = MagicMock()
        sf.append(foo)
        sf.f.seek.assert_called_with(0, 2)
        sf.f.write.assert_called_with(foo.bytes)

    def test_getitem(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        sf.f = MagicMock()
        with patch.object(sf, 'next') as m_next:
            val = sf[42]
        sf.f.seek.assert_called_with(42*1024/8)
        m_next.assert_called()

    def test_save(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        sf.f = MagicMock()
        with patch('os.fsync') as m_fsync:
            sf.save()
        sf.f.flush.assert_called()
        m_fsync.assert_called_with(sf.f)

    def test_destroy(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo')
        with patch.object(sf, 'close') as m_close:
            sf.__destroy__()
            m_close.assert_called()

class SigFileIntegrationTests(TestCase):
    'sigfile integration tests'

    n_bits=24
    n_sigs=5
    example_sig_file = os.urandom(n_sigs*n_bits>>3)

    def test_read(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo', n_bits=self.n_bits)
        sf.f = StringIO(self.example_sig_file)

        mult = self.n_bits>>3
        for i in range(self.n_sigs):
            sig = sf.next()
            self.assertEqual(sig.bytes, self.example_sig_file[i*mult:(i+1)*mult])

        sig = sf.next()
        self.assertEqual(sig.bytes, self.example_sig_file[0:mult])

    def test_write(self):
        with patch('spat.sigfile.SigFile.open') as m_sigfile_open:
            sf = sigfile.SigFile('/path/to/foo', n_bits=self.n_bits)
        sf.f = StringIO()
        sf.f.mode = 'ab'
        sig_file = b''

        for i in range(self.n_sigs):
            sig = os.urandom(self.n_bits>>3)
            sig_file += sig
            sf.append(Bits(bytes=sig))

        self.assertEqual(sf.f.getvalue(), sig_file)
