"""
sigfile.py - A class for loading and storing PUF signatures to files.
Multiple file formats could be implemented here. 
"""

__license__ = """
GPL Version 3

Copyright (2014) Sandia Corporation. Under the terms of Contract
DE-AC04-94AL85000, there is a non-exclusive license for use of this
work by or on behalf of the U.S. Government. Export of this program
may require a license from the United States Government.

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

__version__ = "1.2"

__author__ = "Ryan Helinski and Mitch Martin"

import os
from bitstring import Bits
from .bitstringutils import *

import logging
_log = logging.getLogger('spat')

class SigFile(object):
    """A class to load and store signatures in various formats"""
    mode_map = {'r': 'rb', 'a': 'ab'}

    def __init__(self, fileName, n_bits=1024, mode='r'):
        self.n_bits = n_bits
        self.fileName = fileName
        self.open(mode)
    
    def __destroy__(self):
        self.close()

    def close(self):
        if not self.f.mode.startswith('r'):
            self.save()
        self.f.close()
    
    def open(self, mode='r'):
        if mode not in self.mode_map.keys():
            raise ValueError('Mode needs to be one of \'r\' or \'a\'')

        dirname = os.path.dirname(self.fileName)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        self.f = open(self.fileName, self.mode_map[mode])

    def next(self):
        def getdata():
            return bytes(self.f.read(self.n_bits/8))

        bindata = getdata()
        if (len(bindata) < self.n_bits/8):
            # Start back at the beginning 
            _log.info('Hit EOF of "%s", starting back at the beginning' % self.fileName)
            self.f.seek(0)
            bindata = getdata()

        return Bits(bytes=bindata)

    def append(self, new_bits):
        if self.f.closed or self.f.mode.startswith('r'):
            raise Exception('File must be open in append mode')

        self.f.seek(0, 2) # Seek to the file end
        self.f.write(new_bits.bytes)

    def __getitem__(self, index):
        offset = index * self.n_bits / 8 
        self.f.seek(offset)
        return self.next()

    # __setitem__ not implemented

    def save(self):
        self.f.flush() 
        os.fsync(self.f) # make sure it gets written now
