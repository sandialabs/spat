"""
chipidentify.py - A database-like object that stores information 
about PUF measurements on a sample of chips. This information can 
be loaded and stored in an XML format for persistence. Rudimentary
functions are provided to support statistical analysis. 
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
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import ParseError

import logging
_log = logging.getLogger('spat')

from bitstring import Bits, BitStream
from scipy.stats import gamma
# scipy-ref.pdf Section 5.13 on page 390

import spat.bitstringutils

class ChipIdentify:
    """This class is used to identify a chip's name based on a database of PUF signatures"""

    # static variables
    max_num_dists = 64 # should be at least 64 in practice

    def __init__(self, fileName = "chipsignatures.xml", n_bits=1024):
        self.n_bits = n_bits
        self.fileName = fileName
        self.setup()

        if (os.path.isfile(self.fileName)):
            try:
                self.load()
            except ParseError as pe:
                _log.error(pe)
            else:
                _log.info("Using signature database at '%s' with %d chip signatures" % (self.fileName, len(self)))
        else:
            _log.warning("No chip signatures found at '%s'" % self.fileName)
            if not os.path.isdir(os.path.split(self.fileName)[0]):
                os.makedirs(os.path.split(self.fileName)[0])

    def setup(self):
        # To map chip names to signatures:
        self.signatureMap = dict()
        # For each chip, we also want to have a list of noise and inter-chip distances
        self.noiseDistMap = dict()
        self.interChipDistMap = dict()
        # To keep track of the unstable bit positions
        self.unstableBits = dict()
        self.measCount = dict()

    def clear(self):
        self.setup()
        self.save()

    def __len__(self):
        return len(self.signatureMap)
            
    def load(self):
        """Load data from file"""
        try:
            mytree = etree.parse(self.fileName)
        except ParseError as pe:
            print pe
            return

        myroot = mytree.getroot()

        if myroot.tag != 'chip_list':
            raise NameError('Expecting this XML file to contain one <chip_list> element as its root')

        for subelement in myroot:
            if subelement.tag != 'chip':
                raise NameError('<chip_list> element must contain only <chip> elements')
            self.measCount[subelement.get('name')] = int(subelement.get('meas_count')) if 'meas_count' in subelement.attrib else 1
            for subsub in subelement:
                if subsub.tag == 'sig':
                    if subsub.attrib['encoding'] != 'hex':
                        raise NameError('Only hex encoding supported, add "encoding=hex" and use a hex string')
                    self.signatureMap[subelement.get('name')] = Bits("0x"+subsub.text)

                elif subsub.tag == 'noise':
                    if subelement.get('name') not in self.noiseDistMap:
                        self.noiseDistMap[subelement.get('name')] = []
                    for noise_dist in subsub:
                        if noise_dist.tag != 'dist':
                            raise NameError('Tags under <noise> must be <dist>')
                        self.noiseDistMap[subelement.get('name')].append(int(noise_dist.text))

                elif subsub.tag == 'inter_chip':
                    if subelement.get('name') not in self.interChipDistMap:
                        self.interChipDistMap[subelement.get('name')] = dict()
                    for other_name in subsub:
                        if other_name.tag != 'other':
                            raise NameError('Tags under <inter_chip> must be <other>')
                        if other_name.get('name') not in self.interChipDistMap[subelement.get('name')]:
                            self.interChipDistMap[subelement.get('name')][other_name.get('name')] = []
                        for other_dist in other_name:
                            if other_dist.tag != 'dist':
                                raise NameError('Tags under <other> must be <dist>')
                            self.interChipDistMap[subelement.get('name')][other_name.get('name')].append(int(other_dist.text))

                elif subsub.tag == 'unstable_bits':
                    if subsub.attrib['encoding'] != 'hex':
                        raise NameError('Only hex encoding supported, add "encoding=hex" and use a hex string')
                    self.unstableBits[subelement.get('name')] = Bits("0x"+subsub.text)

                else:
                    raise NameError('Unsupported tag %s' % subsub.tag)
        
    def save(self, altFileName=None):
        if altFileName != None: 
            self.fileName = altFileName
        chipListEl = etree.Element('chip_list')
        chipListEl.text = "\n\t"
        for name, sig in sorted(self.signatureMap.items(), key=lambda item: item[0] ):
            chipEl = etree.SubElement(chipListEl, 'chip', attrib={'name':name, 'meas_count':str(self.measCount[name])})
            chipEl.text = "\n" + 2*"\t"
            chipEl.tail = "\n" + "\t"
            sigEl = etree.SubElement(chipEl, 'sig', attrib={'encoding':'hex'})
            sigEl.text = sig.hex
            sigEl.tail = "\n" + 2*"\t"
            if name in self.noiseDistMap:
                noiseListEl = etree.SubElement(chipEl, 'noise')
                noiseListEl.tail = "\n" + 2*"\t"
                for dist in self.noiseDistMap[name]:
                    noiseEl = etree.SubElement(noiseListEl, 'dist')
                    noiseEl.text = str(dist)
            if name in self.interChipDistMap:
                interListEl = etree.SubElement(chipEl, 'inter_chip')
                interListEl.text = "\n" + 3*"\t"
                interListEl.tail = "\n" + 2*"\t"
                for other_name, dist_list in sorted(self.interChipDistMap[name].items(), key=lambda item: item[0] ):
                    otherNameEl = etree.SubElement(interListEl, 'other')
                    otherNameEl.attrib['name'] = other_name
                    otherNameEl.tail = "\n" + 3*"\t"
                    for dist in dist_list:
                        interEl = etree.SubElement(otherNameEl, 'dist')
                        interEl.text = str(dist)
                otherNameEl.tail = "\n" + 2*"\t"

            if name in self.unstableBits:
                unstableBitsEl = etree.SubElement(chipEl, 'unstable_bits', attrib={'encoding':'hex'})
                unstableBitsEl.text = self.unstableBits[name].hex
                unstableBitsEl.tail = "\n" + "\t"

        chipEl.tail = "\n"
                        
        _log.info('Saving chip signature database to \'%s\'' % self.fileName)
        xmlfile = open(self.fileName, 'w')
        #xml_extras.indent(chipListEl) # add white space to XML DOM to result in pretty printed string
        xmlfile.write('<?xml version="1.0" encoding="UTF-8" ?>\n' + etree.tostring(chipListEl))
        xmlfile.flush()
        xmlfile.close() # don't need to sync because we close here

    def Identify(self, bits):
        "This compares a bit string against all known chip signatures and returns the closest match"

        hd_dict = self.MatchMap(bits)
        return min(hd_dict.items(), key=lambda item: item[1]) 
    
    def MatchMap(self, bits):
        "This compares a bit string against all known chip signatures"

        hd_dict = dict()
        for key, value in self.signatureMap.items():
            relhd = float(bitstringutils.hd(bits, value))/self.n_bits
            hd_dict[key] = relhd

        return hd_dict

    def add(self, chip_name, sig):
        # I can store more than one <sig> per <chip> in the XML and do averaging, 
        # but since I'm using the minimum Hamming distance, there's no problem with 
        # just storing the first measured signature here
        self.signatureMap[chip_name] = sig
        self.measCount[chip_name] = 0

    def get_sig(self, chip_name):
        return self.signatureMap[chip_name]

    def process_sig (self, chip_name, sig):
        """This computes and records some greedy statistics on a given signature"""

        # add this chip if it is unknown
        if chip_name not in self.signatureMap.keys():
            self.add(chip_name, sig)
        else:
            # update unstable bit map
            if chip_name not in self.unstableBits:
                self.unstableBits[chip_name] = BitStream(uint=0, length=self.n_bits)
            if self.measCount[chip_name] > 0:
                self.unstableBits[chip_name] = self.unstableBits[chip_name] | (self.signatureMap[chip_name] ^ sig) 
        
        # Increment the measurement count for this chip
        self.measCount[chip_name] += 1

        # record 1 noise distance
        if chip_name not in self.noiseDistMap.keys():
            self.noiseDistMap[chip_name] = []
        else: 
            # assume that if we didn't have a list, that this is the first measurement, 
            # and therefore we need to wait for a subsequent one before we can compute a noise distance
            self.noiseDistMap[chip_name].append(bitstringutils.hd(sig, self.signatureMap[chip_name]))
            # for scalability, should truncate this list 
            if len(self.noiseDistMap[chip_name]) > self.max_num_dists:
                self.noiseDistMap[chip_name] = self.noiseDistMap[chip_name][-self.max_num_dists:]

        # and record (N_C - 1) inter-chip distances
        for other_chip_name in self.signatureMap.keys():
            if other_chip_name == chip_name:
                # don't compare to self 
                continue
            if chip_name not in self.interChipDistMap.keys():
                self.interChipDistMap[chip_name] = dict()
            if other_chip_name not in self.interChipDistMap[chip_name].keys():
                self.interChipDistMap[chip_name][other_chip_name] = []
            self.interChipDistMap[chip_name][other_chip_name].append(
                bitstringutils.hd(sig, self.signatureMap[other_chip_name]))
            # for scalability, I truncate this list 
            if len(self.interChipDistMap[chip_name][other_chip_name]) > self.max_num_dists:
                self.interChipDistMap[chip_name][other_chip_name] = self.interChipDistMap[chip_name][other_chip_name][-self.max_num_dists:]

    def get_meas_count(self, chip_name):
        if chip_name in self.measCount:
            return self.measCount[chip_name]
        else:
            return 0

    def get_num_unstable_bits (self, chip_name):
        return self.unstableBits[chip_name].count(1)

    def unstable_bits_valid (self, chip_name):
        return self.measCount[chip_name] > 1

    def get_noise_dist_avg (self, chip_name):
        return float(sum(self.noiseDistMap[chip_name]))/max(1,len(self.noiseDistMap[chip_name]))

    def get_inter_dist_avg (self, chip_name):
        inter_dists = [sum(inter_dist_list) for inter_dist_list in self.interChipDistMap[chip_name].values()]
        num_dists = [len(inter_dist_list) for inter_dist_list in self.interChipDistMap[chip_name].values()]
        return float(sum(inter_dists))/max(1, sum(num_dists))

    def get_all_noise_dists (self):
        all_noise_dists = []
        for chip_name, noise_dists in self.noiseDistMap.items():
            all_noise_dists.extend(noise_dists)
        return all_noise_dists

    def get_all_inter_chip_dists (self):
        all_inter_chip_dists = []
        for this_chip_name, dist_map in self.interChipDistMap.items():
            for other_chip_name, inter_chip_dists in dist_map.items():
                all_inter_chip_dists.extend(inter_chip_dists)
        return all_inter_chip_dists

    def prob_alias(self, plot=False):
        """Returns tuple (threshold, probability)"""

        if plot:
            import matplotlib.pyplot as plt
            plt.ion()
            plt.clf()

        nd = self.get_all_noise_dists()
        a, loc, scale = gamma.fit(nd)
        ndrv = gamma(a, loc, scale)
        if plot:
            plt.hist(nd, normed=True) # 'normed' might become 'density' later? 
            x = range(max(nd))
            plt.plot(x, ndrv.pdf(x))

        icd = self.get_all_inter_chip_dists()
        a, loc, scale = gamma.fit(icd)
        icdrv = gamma(a, loc, scale)
        if plot:
            plt.hist(icd, normed=True)
            x = range(max(icd))
            plt.plot(x, icdrv.pdf(x))

        # Here it goes!
        threshold = ndrv.ppf(0.997)
        if plot:
            plt.axvline(threshold)
        prob = icdrv.cdf(threshold)
        _log.info('Noise 99.7%% threshold: %f, probability of aliasing: %1.3e' % (threshold, prob))
        return threshold, prob

