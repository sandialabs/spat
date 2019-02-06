#!/usr/local/bin/python
from __future__ import print_function
"""
simulator.py - A class that simulates a sample of PUFs. Currently, the Ring
Oscillator PUF is modeled. Mean oscillator frequencies are first created for a
sample of virtual chips. Then, the RO PUF model is used to create PUF signatures
with realistic noise. The virtual chip sample parameters are saved to an XML
file so the same sample of chips can be used later. 

The architecture is an implementation of a system published by G. Suh and S.
Devadas, "Physical unclonable functions for device authentication and secret key
generation", in Proc. DAC'07, pp. 9-14, 2007.

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

import os
import numpy
import bitstring
from spat.bitstringutils import *
import xml.etree.ElementTree as etree
from spat.simulator.abstractsimulator import AbstractSimulator

class Simulator(AbstractSimulator):
    """A PUF-simulating class. Produces simulated PUF responses."""

    def genRealValues(self):
        return numpy.random.normal(
                self.params['param_mu'],
                self.params['param_sd'],
                size=(self.numVirtChips, self.numElements))


    def genSetupXML(self):
        myxml = etree.Element('xml', attrib={'version':'1.0', 'encoding':'UTF-8'})
        myxml.text = "\n"
        myxml.tail = "\n"
        setupEl = etree.SubElement(
                myxml,
                'setup',
                attrib=dict(zip(self.params.keys(),
                                [str(val) for val in self.params.values()])))
        setupEl.tail = "\n"
        for index in range(self.numVirtChips):
            virtChipEl = etree.SubElement(myxml, 'virtchip', attrib={'name':self.chipNames[index]})
            virtChipEl.text = "\n    "
            virtChipEl.tail = "\n"
            valsEl = etree.SubElement(virtChipEl, 'realvalues')
            valsEl.text = "\n        "
            valsEl.tail = "\n"
            for param in self.realValues[index]:
                child = etree.SubElement(valsEl, 'value')
                child.text = str(param)
                child.tail = "\n        "
            child.tail = "\n    "

        return etree.tostring(myxml)


    def writeSetupFile(self):
        with open(self.setup_file, 'wb') as xmlfile:
            xmlfile.write(self.genSetupXML())


    def generateSetup(self):
        print("Generating virtual chips...", end='')
        self.numElements = self.n_bits + 1
        self.realValues = self.genRealValues()
        self.chipNames = [('v%03d' % (index + 1)) for index in range(self.numVirtChips)]

        self.writeSetupFile()


    def next(self, virtChipIndex=0):
        if type(virtChipIndex) == str:
            virtChipIndex = int(virtChipIndex[1:4]) - 1
        bits = bitstring.BitArray()

        noiseValues = [self.noise() for i in range(self.n_bits+1)]
        # This is the linear RO PUF architecture which avoids redundant 
        # bits which are inherent in the all possible combinations approach
        # i.e., comparisons a ? b and b ? c may render a ? c redundant
        # Instead, we use (NB + 1) ring oscillators and only compare adjacent 
        # oscillators (i) and (i+1) for i in (0, NB).
        for i in range(0, self.n_bits):
            lhs = self.realValues[virtChipIndex][i] + noiseValues[i]
            rhs = self.realValues[virtChipIndex][i+1] + noiseValues[i+1]
            bits.append(bitstring.Bits(bool=(lhs < rhs)))

        return bits
