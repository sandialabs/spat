"""
quartus.py - A class for interfacing with Altera's Quartus software
and communicating with a PUF over the Virtual JTAG Interface (VJI). 
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

import os, subprocess, glob, time
import logging
import bitstring
from .bitstringutils import *

quartus_path = "C:\\altera\\10.1sp1\\quartus\\bin"

quartus_pgm = quartus_path + "\quartus_pgm"
quartus_stp = quartus_path + "\quartus_stp"

_log = logging.getLogger(__name__)

def try_syscall (cmd, max_tries=32):
    num_tries = 0 
    
    while (num_tries < max_tries):
        _log.info("> " + cmd)
        retval = os.system(cmd)
        if (retval == 0):
            break
        else:
            "Error returned, re-trying"
            num_tries += 1
            time.sleep(1)
        
    if (num_tries > max_tries):
        _log.error("Gave up trying")
    else:
        _log.info("Command returned OK")
        
    return retval

def conv_temp_f (degs_c):
    return float(degs_c) * 9 / 5 + 32

class QuartusCon(object):
    "A class to connect to an FPGA via Quartus"

    def __init__(self, nb=1024, tclFile="measureARBR.tcl", cdf_filename='BeMicroII_schem.cdf'):
        self.nb = nb
        self.tclFile = tclFile
        self.cdf_filename = cdf_filename
    
    def __destroy__(self):
        self.close()
            
    def close(self):
        if (self.subProcess.returncode == None):
            try:
                self.subProcess.stdin.write("q\n")
                self.subProcess.stdin.close()
                if self.subProcess.wait() != 0:
                    _log.error("Subprocess did not return 0")
            except IOError as e:
                _log.error("Failed to close gracefully")
            
    def program(self):
        retval = try_syscall("%s --cable=\"USB-Blaster\" --mode=\"JTAG\" --operation=p %s" % (quartus_pgm, self.cdf_filename))

        if (retval == 0):
            stp_args = [quartus_stp, '-t', self.tclFile]
            _log.info("Pipe> " + " ".join(stp_args))
            self.subProcess = subprocess.Popen(stp_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for i in range(2):
                _log.info(self.subProcess.stdout.readline())

        return retval

    def next(self):
        self.subProcess.stdin.write("\n")
        self.subProcess.stdin.flush()
        for i in range(1):
            _log.info(self.subProcess.stdout.readline())
        myline = self.subProcess.stdout.readline().strip()
        _log.info(myline)
        new_bits = bitstring.Bits(hex='0x' + myline[0:(self.nb/4)])
        
        (self.time, self.temp) = self.subProcess.stdout.readline().split(" ")
        
        return new_bits
   
    def get_temp(self, format="C"):
        try:
            if (format=="F"):
                return conv_temp_f(self.temp)
            else:
                return float(self.temp)
        except (AttributeError):
            return ""

