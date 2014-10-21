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
import bitstring
from bitstringutils import *

class SigFile(object):
    """A class to load and store signatures in various formats"""

    def __init__(self, fileName, nb=1024):
        self.nb = nb
        self.fileName = fileName
        #self.open()
    
    def __destroy__(self):
        self.close()

    def close(self):
        try:
            self.f.close()
        except AttributeError as e:
            return False
        return True
    
    def open(self, fileName=None, mode='rb'):
        if (fileName):
            self.fileName = fileName

        if not os.path.isdir(os.path.split(self.fileName)[0]):
            os.makedirs(os.path.split(self.fileName)[0])
        self.f = open(self.fileName, mode)

    def next(self):
        if ('f' not in self.__dict__ or not self.f.mode.startswith('r')):
            self.open()
        bindata = self.f.read(self.nb/8)
        if (len(bindata) < self.nb/8):
            # Start back at the beginning 
            print "Hit EOF, starting back at the beginning"
            self.f.seek(0)
            bindata = self.f.read(self.nb/8)
            
        new_bits = bitstring.Bits(bytes=bindata)
        #print repr(new_bits)
            
        return new_bits

    def append(self, new_bits):
        # should check if file is open
        #if (self.f.closed or not self.f.mode.startswith('a')): 
            #self.f.open
        if ('f' in self.__dict__ and not self.f.closed):
            self.f.close()

        self.open(mode='ab')

        self.f.write(new_bits.bytes)
        self.f.flush() 
        os.fsync(self.f) # make sure it gets written now

    def __getitem__(self, index):
        offset = index * self.nb / 8 
        self.f.seek(offset)
        return self.next()

    # Not sure supporting __setitem__ makes sense 

    def save(self, fileName):
        if fileName.endswith('.dat'):
            self.bits.tofile(fileName)

