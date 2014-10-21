#!/usr/local/bin/python
"""
abstractsimulator.py - A class that simulates a sample of PUFs. 
This file serves as an abstract type from which actual simulator
classes can be defined. Please note that it does NOT work as-is. 

This program features a self-test that is executed when this file 
is executed, rather than being imported. 
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

import os, bitstring, random
from bitstringutils import *
import xml.etree.ElementTree as etree

class AbstractSimulator(object):
    """An abstract class for PUF simulators."""

    def __init__(self, nb=1024):
        self.nb = nb
        self.bit_flips = None
        self.setupFile = 'data/Simulator/simulator_setup.xml'
        if (not os.path.isdir(os.path.dirname(self.setupFile))):
            os.makedirs(os.path.dirname(self.setupFile))

    def setup(self, param_mu=10, param_sd=0.00001, noise_mu=0, noise_sd=0.025, numVirtChips=32):
        self.params = {'param_mu':param_mu, 'param_sd':param_sd, 'noise_mu':noise_mu, 'noise_sd':noise_sd}
        if (os.path.isfile(self.setupFile)):
            self.loadFromFile()
        else:
            self.generateSetup()
        print "Done."

    def loadFromFile(self):
        print "Loading simulator state... ",
        mytree = etree.parse(self.setupFile)
        myroot = mytree.getroot()

        self.realValues = []
        self.chipNames = []
        for child in myroot:
            if (child.tag == 'setup'):
                self.params = dict(zip(child.attrib.keys(), [float(val) for val in child.attrib.values()]))
            elif (child.tag == 'virtchip'):
                self.chipNames.append(child.attrib['name'])
                for chipchild in child:
                    if (chipchild.tag == 'realvalues'):
                        chipRealValues = []
                        for value in chipchild:
                            chipRealValues.append(float(value.text.strip()))
                        self.realValues.append(chipRealValues)
        self.numVirtChips = len(self.realValues)
        self.numElements = len(self.realValues[0])

    def generateSetup(self):
        raise NotImplemented()

    def close(self):
        """For compatibility with other bit sources"""
        return True

    def getChipName(self, index):
        return 'v%03d' % (index+1)

    def makeSigFile (self, sigFile='simulator_sigs.xml'):
        chipListEl = etree.Element('chip_list')
        chipListEl.text = "\n"
        chipListEl.tail = "\n"
        for index in range(self.numVirtChips):
            chipEl = etree.SubElement(chipListEl, 'chip', attrib={'name':self.getChipName(index)})
            chipEl.text = "\n"
            chipEl.tail = "\n"
            sigEl = etree.SubElement(chipEl, 'sig', attrib={'encoding':'hex'})
            sigEl.text = self.next(index).hex 
            sigEl.tail = "\n"
            
        xmlparent = os.path.split(sigFile)[0]
        if not os.path.isdir(xmlparent):
            os.makedirs(xmlparent)
        xmlfile = open(sigFile, 'w')
        xmlfile.write('<?xml version="1.0" encoding="UTF-8" ?>\n' + etree.tostring(chipListEl))
        xmlfile.flush()
        xmlfile.close()

    def getSetupStr(self):
        return "P_mu=%1.1f, P_sd=%1.1f, E_mu=%1.3f, E_sd=%1.3f" % (
                        self.params['param_mu'], self.params['param_sd'], self.params['noise_mu'], self.params['noise_sd'])

    def noise(self):
        return random.normalvariate(self.params['noise_mu'], self.params['noise_sd'])

    def next(self, virtChipIndex=0):
        raise NotImplemented()

    def characterize(self, chipIdentifier, numMeas=32):
        import ttk, Tkinter
        dlg = Tkinter.Toplevel()
        dlg.title("Simulator Progress")
        l = Tkinter.Label(dlg, text="Measuring each chip %d times" % numMeas)
        l.pack()
        w = ttk.Progressbar(dlg, maximum=self.numVirtChips)
        w.pack()
        for ci in range(self.numVirtChips):
            print 'Measuring chip # %d %d times' % (ci, numMeas)
            for ri in range(numMeas):
                sig = self.next(ci)
                chipIdentifier.process_sig(self.getChipName(ci), sig)
            w.step()
            dlg.update()
        w.stop()
        dlg.destroy()


def NoiseWorker(argTuple):
    """Measure one of the chips multiple times. For use with multiprocessor.pool """

    chipIndex, iterations = argTuple
    # Instead of generating the number of iterations for each process, I could create my own iterator object and pass that in as the argument
    mySim = AbstractSimulator()
    mySim.setup()
    enrollment = mySim.next(chipIndex)
    noise_hds = [hd(enrollment, mySim.next(chipIndex)) for measIndex in range(iterations)]
    print "Chip v%03d (of %d): %d / %d = %0.3f %%" % (chipIndex+1, mySim.numVirtChips, sum(noise_hds), iterations * mySim.nb, (100 * float(sum(noise_hds)) / iterations / mySim.nb))
    return float(sum(noise_hds)) / iterations / mySim.nb

# A self-test routine that characterizes the population statistics resulting from the setup parameters
if __name__=="__main__":
    import multiprocessing, itertools
    print "Running self-test"
    mySim = AbstractSimulator()
    mySim.setup() # setup with defaults
    p = multiprocessing.Pool(multiprocessing.cpu_count())
    argIter = itertools.izip(range(mySim.numVirtChips), itertools.repeat(2 ** 6))
    results = p.map(NoiseWorker, argIter)
    
    print "Average noise Hamming distance: %f" % (sum(results) / mySim.numVirtChips)
    print "Test done"

