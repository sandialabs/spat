# bch_code.py
# Copyright (2014) Sandia Corporation. Under the terms of Contract
# DE-AC04-94AL85000, there is a non-exclusive license for use of this
# work by or on behalf of the U.S. Government. Export of this program
# may require a license from the United States Government.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os, bitstring, random, math
import subprocess

from bitstringutils import *

class bch_code(object):
    """An error-correcting class"""
    
    def __init__(self, nb=1024, fileName='bch_code_log.dat'):
        self.nb = nb
        self.bit_flips = None
        self.logFileName = fileName
        self.logFile = open(self.logFileName, 'ab')
    
    def __destroy__(self):
        self.close()

    def close(self):
        if (not self.logFile.closed):
            self.logFile.close()

    def setup(self, first_measurement, MM=13, TT=20, KK=1024, PP=8):
        """A function to enroll the PUF with the error corrector object
        
    Arguments:
    MM <field>:  Galois field, GF, for code.  Code length is 2^<field>-1.
         The default value is 13 for a code length 8191.  If the parameter is
         set to 0, the program will estimate the value based upon the values
         chosen for k and t.
    TT <correct>:  Correction power of the code.  Default = 4
    KK <data bits>:  Number of data bits to be encoded. Must divide 4.
         The default value is the maximum supported by the code which
         depends upon the field (-m) and the correction (-t) chosen.
    PP <parallel>:  Parallelism in encoder.  Does not effect results but
         does change the algorithm used to generate them.  Default = 8"""

        self.m = MM; self.t = TT; self.k = KK; self.p = PP
        p = subprocess.Popen("bch_encoder.exe -m %d -t %d -k %d -p %d" % (self.m, self.t, self.k, self.p), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.stdin.write(first_measurement.hex)
        output, errors = p.communicate()
        codeword, syndrome = output.split()
        self.syndrome = syndrome
        return self.syndrome
    
    def decode(self, response):
        p = subprocess.Popen("bch_decoder.exe -m %d -t %d -k %d -p %d" % (self.m, self.t, self.k, self.p), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.stdin.write(response.hex + self.syndrome + "\n")
        p.stdin.close()
        output, errors = p.communicate()
        if len (output.strip()) != self.nb / 4:
            raise ValueError ("Invalid signature returned from decoder")

        return bitstring.Bits(hex="0x"+output.strip())
        
if __name__=="__main__":
    print "Running self-test"

    import simulator
    mySim = simulator.Simulator()
    mySim.setup()

    firstMeasurement = mySim.next()
    print firstMeasurement.hex
    myCoder = bch_code()
    helper_data = myCoder.setup(firstMeasurement) # setup with defaults

    print "Syndrome: " + myCoder.syndrome

    newMeasurement = mySim.next()
    print "(Possibly-) Errored Measurement:\n" + newMeasurement.hex
    print "Errors: " + str(hd(firstMeasurement, newMeasurement))
    print "Recovered:\n" + myCoder.decode(newMeasurement).hex
    print "Reduced errors: " + str(hd(firstMeasurement, myCoder.decode(newMeasurement)))
    
    print "Done!"
