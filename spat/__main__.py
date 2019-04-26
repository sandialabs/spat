#!/usr/local/bin/python

"""
spat.py - A Python TkInter GUI for visually measuring and
demonstrating physical uncloneable functions
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

__copyright__ = """
Copyright (2014) Sandia Corporation. Under the terms of Contract
DE-AC04-94AL85000, there is a non-exclusive license for use of this
work by or on behalf of the U.S. Government. Export of this program
may require a license from the United States Government.
"""

__credits__ = ["Ryan Helinski", "Mitch Martin", "Jason Hamlet", "Todd Bauer", "Bijan Fakhri"]

from Tkinter import *
import tkFont
import tkFileDialog
import tkSimpleDialog
import tkMessageBox
import math
import os
import time
from collections import OrderedDict

# Local packages
from sigfile import *
from quartus import *
from chipidentify import *
import bitstring
from simulator.ropuf import *
import bch_code
import randomness

def fmtFractionPercent(num, den):
    return '%d / %d = %.3f%%' % (num, den, 100*(float(num) / den))

class Application(Frame):
    # static variables
    numMatchScores = 8
    colorMapImmDiff = OrderedDict( [('00', '#000000'),
                    ('10', '#ffffff'),
                    ('01', '#ff0000'),
                    ('11', '#ffff00')] )
    colorMapGray = OrderedDict( [('0%', '#000000'),
                    ('50%', '#808080'),
                    ('100%', '#ffffff')] )
    sourceList = ('Simulator', 'File', 'ROPUF', 'ARBR')
    quartusSources = {
            'ROPUF' : {'tclFile' : 'measureROPUF.tcl',
                    'cdf_filename' : 'BeMicroII_ROPUF.cdf'},
            'ARBR' : {'tclFile' : 'measureARBR.tcl',
                    'cdf_filename' : 'BeMicroII_ARBR_Controller.cdf'}
            }
    colorMapList = ('Grayscale', 'Imm. Diff.')
    distHistTypeList = ('Simple', 'Split', 'Cumulative')
    maxAvgDepth = 32
    noiseThreshold = 0.25
    randomnessFunMap = OrderedDict([
                    ('Entropy', randomness.entropy),
                    ('Min. Entropy', randomness.min_entropy),
                    ('Monobit', randomness.monobit),
                    ('Runs Test', randomness.runs_test),
                    ('Runs Test 2', randomness.runs_test2),
                    ('Cumul. Sums', randomness.cum_sum)
            ])
    outputPath = 'data'


    def __init__(self, master=None):
        self.nb = 1024
        self.chipNum = 0
        self.bitFlips = None
        self.bits = bitstring.BitStream(uint=0, length=self.nb)
        self.reset()
        self.bigfont = tkFont.Font(family="Helvetica", size=12)
        self.font = tkFont.Font(family="Helvetica", size=10)
        self.squareSize = int(math.sqrt(self.nb))
        self.zoomFactor = int(480/self.squareSize)
        self.colorMapFun = self.mapBitGrayscale
        Frame.__init__(self, master)
        master.protocol("WM_DELETE_WINDOW", self._delete_window)
        self.statusStr = 'Not Connected'
        self.updateTitle()
        self.grid()
        self.createWidgets()

    def reset(self):
        self.measurementCounter = 0
        self.bitFlips = None
        self.bitAvgs = [bitstring.BitArray() for x in range(self.nb)]

    def updateTitle(self, statusStr=None):
        if statusStr:
            self.statusStr = statusStr
        self.master.title(" - ".join(["PUF Visual Interface", self.statusStr]))

    def _delete_window(self):
        print 'Caught delete_window event'
        self.save()
        self.master.destroy()

    def _destroy(self, event=None):
        print 'Caught destroy event'
        if event:
            print event
        self.save()

    def quit(self, event=None):
        self.save()
        self.master.quit()
        self.destroy()

    def save(self, event=None):
        if 'chipIdentifier' in self.__dict__:
            self.chipIdentifier.save()

    def mapBitImmDiff(self, index):
        # TODO performance could be improved
        return self.colorMapImmDiff[ str(int(self.bits[index])) + str(int(self.chipIdentifier.unstableBits[self.lastRead][index])) ]

    def mapBitGrayscale(self, index):
        return '#' + ('%02x' % (255*float(hw(self.bitAvgs[index]))/max(1, len(self.bitAvgs[index]))) * 3)

    def destroyLegend(self):
        self.colorMapLegend.destroy()
        self.colorMapLabels = []
        self.colorMapIcons = []

    def buildColorMapLegend(self, colorMap):
        if 'colorMapLegend' in self.__dict__:
            self.destroyLegend()
        self.colorMapLegend = Frame(self.colorMapFrame)

        # Create the legend
        for i in range(len(colorMap)):
            code = colorMap.keys()[i]
            color = colorMap[code]
            self.colorMapIcons.append(Canvas(self.colorMapLegend, width=self.zoomFactor, height=self.zoomFactor, bd=2, relief="groove", bg=color))
            self.colorMapIcons[i].grid(row=0, column=(2*i)+1)
            self.colorMapLabels.append(Label(self.colorMapLegend, text='%s %s' % (
                    'Stable' if (code[1] == '0') else 'Unstable',
                    code[0]
                    ), font=self.font))
            self.colorMapLabels[i].grid(row=0, column=(2*i)+2)
        self.colorMapLegend.grid(row=0, column=1)

    def buildGrayScaleLegend(self):
        if 'colorMapLegend' in self.__dict__:
            self.destroyLegend()
        self.colorMapLegend = Frame(self.colorMapFrame)

        # Create the legend
        for i in range(len(self.colorMapGray)):
            code = self.colorMapGray.keys()[i]
            color = self.colorMapGray[code]
            self.colorMapIcons.append(Canvas(self.colorMapLegend, width=self.zoomFactor, height=self.zoomFactor, bd=2, relief="groove", bg=color))
            self.colorMapIcons[i].grid(row=0, column=(2*i)+1)
            self.colorMapLabels.append(Label(self.colorMapLegend, text=code, font=self.font))
            self.colorMapLabels[i].grid(row=0, column=(2*i)+2)
        self.colorMapLegend.grid(row=0, column=1)

    def createWidgets(self):
        self.master.option_add('*tearOff', FALSE)
        # Menu Bar
        self.menuBar = Menu(self)
        # Source Menu
        self.menuBarSource = Menu(self.menuBar)

        self.sourceSelected = StringVar()
        self.sourceSelected.set(self.sourceList[0])
        self.sourceSelected.trace('w', self.onModeSelect)
        self.menuBarSourceSelect = Menu(self.menuBarSource)
        for i, source in enumerate(self.sourceList):
            self.menuBarSourceSelect.add_radiobutton(label=source, variable=self.sourceSelected, value=source)
        self.menuBarSource.add_cascade(label="Select", menu=self.menuBarSourceSelect)
        self.menuBarSource.add_command(label="Open", command=self.open, accelerator="O")
        self.bind_all("<o>", self.open)

        # For choosing a virtual chip from the virtual lot
        self.virtChipNumVar = StringVar()
        self.menuBarSourceSimulator = Menu(self.menuBarSource)
        self.menuBarSourceSimulatorSelect = Menu(self.menuBarSourceSimulator)
        self.menuBarSourceSimulator.add_cascade(label='Virtual Chip', menu=self.menuBarSourceSimulatorSelect)
        self.menuBarSourceSimulator.add_command(label='Random Chip', command=self.simulatorPickRandom, accelerator='R')
        self.bind_all('<r>', self.simulatorPickRandom)

        self.menuBarSourceSimulator.add_command(label='Measure All', command=self.simulatorMeasureAll)
        self.menuBarSource.add_cascade(label='Simulator', menu=self.menuBarSourceSimulator)
        self.menuBarSource.entryconfig('Simulator', state=DISABLED)

        self.correctVar = IntVar()
        self.menuBarSource.add_checkbutton(label='ECC', variable=self.correctVar, command=self.selectECC)

        self.menuBarSource.add_command(label='Next', command=self.next, accelerator="Space")
        self.menuBarSource.entryconfig('Next', state=DISABLED)
        self.bind_all("<space>", self.next)

        self.menuBarSource.add_command(label='Disconnect', command=self.close)
        self.menuBarSource.entryconfig('Disconnect', state=DISABLED)
        self.menuBarSource.add_separator()
        self.menuBarSource.add_command(label="Quit", command=self.quit, accelerator="Ctrl+Q")
        self.bind_all("<Control-q>", self.quit)
        self.menuBar.add_cascade(label="Source", menu=self.menuBarSource)

        # Chip DB Menu
        self.menuBarChipDB = Menu(self.menuBar)
        self.menuBarChipDB.add_command(label="Open", command=self.loadSigFile, accelerator="Ctrl+O")
        self.bind_all("<Control-o>", self.loadSigFile)
        self.menuBarChipDB.add_command(label="Save", command=self.save, accelerator="Ctrl+S")
        self.bind_all("<Control-s>", self.save)
        self.menuBarChipDB.add_command(label="Clear", command=self.clearSigFile, accelerator="Ctrl+N")
        self.menuBarChipDB.entryconfig('Clear', state=DISABLED)
        self.bind_all("<Control-n>", self.clearSigFile)

        self.menuBar.add_cascade(label="Chip DB", menu=self.menuBarChipDB)

        # View Menu
        self.menuBarView = Menu(self.menuBar)
        self.menuBarView.add_command(label='Scale Bitmap', command=self.setScale)
        self.menuBarView.add_command(label='Font Size', command=self.setFontSize)

        self.colorMapSelected = StringVar()
        self.colorMapSelected.set(self.colorMapList[0])
        self.menuBarLegend = Menu(self.menuBarView)
        for colorMap in self.colorMapList:
            self.menuBarLegend.add_radiobutton(label=colorMap, variable=self.colorMapSelected, value=colorMap)
        self.menuBarView.add_cascade(label='Color Map', menu=self.menuBarLegend)
        self.menuBar.add_cascade(label='View', menu=self.menuBarView)

        # Allow the user to disable the probability of aliasing statistic on the front panel
        self.probAliasEnVar = IntVar()
        self.probAliasEnVar.set(1)
        self.menuBarView.add_checkbutton(label='Prob. Alias', variable=self.probAliasEnVar)

        # Analyze Menu
        self.menuBarAnalyze = Menu(self.menuBar)
        self.menuBarAnalyze.add_command(label='Randomness Checks', command=self.runRandomnessCheck)
        self.menuBarAnalyze.entryconfig('Randomness Checks', state=DISABLED)
        self.menuBarAnalyze.add_separator()
        self.menuBarAnalyzeHistogram = Menu(self.menuBarAnalyze)
        self.distHistSelected = StringVar()
        self.distHistSelected.set(self.distHistTypeList[0])
        for distHist in self.distHistTypeList:
            self.menuBarAnalyzeHistogram.add_radiobutton(label=distHist, variable=self.distHistSelected, value=distHist)
        self.menuBarAnalyzeHistogram.add_separator()
        self.distHistFractions = IntVar()
        self.distHistFractions.set(1)
        self.menuBarAnalyzeHistogram.add_checkbutton(label='Relative Distances', variable=self.distHistFractions)
        self.menuBarAnalyze.add_cascade(label='Histogram Type', menu=self.menuBarAnalyzeHistogram)
        self.menuBarAnalyze.add_command(label='Draw Histograms', command=self.runDistHist)
        self.menuBarAnalyze.entryconfig('Draw Histograms', state=DISABLED)
        self.menuBarAnalyze.add_separator()
        self.menuBarAnalyze.add_command(label='Save Report', command=self.writeReport)
        self.menuBarAnalyze.entryconfig('Save Report', state=DISABLED)
        self.menuBar.add_cascade(label='Analyze', menu=self.menuBarAnalyze)

        # display the menu bar
        root.config(menu=self.menuBar)

        # Main Frame
        self.sigVis = self.make_pi()
        self.sigCanvas = Canvas(self, width=self.squareSize*self.zoomFactor,
                height=self.squareSize*self.zoomFactor)
        self.sigCanvas.grid(row=0, column=0)
        self.sigCanvas.create_image(0, 0, image=self.sigVis, anchor=NW)

        # Legend for color map
        self.colorMapFrame = Frame(self)
        self.colorMapFrame.grid(row=2, column=0)
        self.colorMapLabels = []
        self.colorMapIcons = []
        # add a select menu for color map style
        self.colorMapPicker = OptionMenu(self.colorMapFrame, self.colorMapSelected, *self.colorMapList)
        self.colorMapPicker.grid(row=0, column=0)
        self.colorMapSelected.trace('w', self.onColorMapSelect)
        # add the actual legend
        self.buildGrayScaleLegend()

        self.tempVar = StringVar()
        self.tempLabel = Label (self, textvariable=self.tempVar, font=self.font)
        self.tempLabel.grid(row=3, column=0)

        # Group of buttons (PUF Type, Open, ECC, Next, Disconnect, Quit)
        self.buttonFrame = Frame(self)
        self.buttonFrame.grid(row=6, column=0, columnspan=1)
        bpad = 4

        self.sourceSelect = OptionMenu(self.buttonFrame, self.sourceSelected, *self.sourceList)
        self.sourceSelect.grid(row=0, column=0)
        self.oldMode = self.sourceSelected.get() # for detecting a change in the value

        self.programButton = Button (self.buttonFrame, text='Open', command=self.open)
        self.programButton.grid(row=0, column=1, padx=bpad, pady=bpad)

        self.correctButton = Checkbutton(self.buttonFrame, text='ECC', variable=self.correctVar, command=self.selectECC)
        self.correctButton.grid(row=0, column=3, padx=bpad, pady=bpad)

        self.nextButton = Button (self.buttonFrame, text='Next', command=self.next)
        self.nextButton.grid(row=0, column=4, padx=bpad, pady=bpad)
        self.nextButton.config(state=DISABLED)

        self.closeButton = Button (self.buttonFrame, text='Disconnect', command=self.close)
        self.closeButton.grid(row=0, column=5, padx=bpad, pady=bpad)
        self.closeButton.config(state=DISABLED)

        # Score board
        self.scoreFrame = Frame(self)
        self.scoreFrame.grid(row=0, column=1, rowspan=3, sticky=N+W)
        self.matchHeadingLabel = Label(self.scoreFrame, text='Similarity (% Bits):', font=self.bigfont)
        self.matchHeadingLabel.grid(row=0, column=0, columnspan=2, sticky='W')
        self.matchLabelVars = []
        self.matchLabels = []
        self.matchScoreLabelVars = []
        self.matchScoreLabels = []
        for i in range(self.numMatchScores):
            self.matchLabelVars.append(StringVar())
            self.matchLabels.append(Label (self.scoreFrame, textvariable=self.matchLabelVars[i], font=self.font))
            self.matchLabels[i].grid(row=i+1, column=0, sticky='N')
            self.matchScoreLabelVars.append(StringVar())
            self.matchScoreLabels.append(Label (self.scoreFrame, textvariable=self.matchScoreLabelVars[i], font=self.font))
            self.matchScoreLabels[i].grid(row=i+1, column=1, sticky='NE')



        # Bit Buffer Statistics
        self.bitFlipVar = StringVar()
        self.bitFlipLabel = Label(self.scoreFrame, text='Number of flipped bits:', font=self.bigfont)
        self.bitFlipLabel.grid(row=self.numMatchScores+1, column=0, sticky='W', padx=bpad, pady=bpad, columnspan=2)
        self.bitFlipLabelVar = Label(self.scoreFrame, textvariable=self.bitFlipVar, font=self.font)
        self.bitFlipLabelVar.grid(row=self.numMatchScores+2, column=0, sticky='E', padx=bpad, pady=bpad, columnspan=2)

        self.unstableBitVar = StringVar()
        self.unstableBitLabel = Label(self.scoreFrame, text='Number of unstable bits:', font=self.bigfont)
        self.unstableBitLabel.grid(row=self.numMatchScores+3, column=0, sticky='W', padx=bpad, pady=bpad, columnspan=2)
        self.unstableBitLabelVar = Label(self.scoreFrame, textvariable=self.unstableBitVar, font=self.font)
        self.unstableBitLabelVar.grid(row=self.numMatchScores+4, column=0, sticky='E', padx=bpad, pady=bpad, columnspan=2)


        # Chip and chip sample statistics
        self.noiseDistVar = StringVar()
        self.noiseDistLabel = Label(self.scoreFrame, text='Avg. Noise HD:', font=self.bigfont)
        self.noiseDistLabel.grid(row=self.numMatchScores+5, column=0, sticky='W', padx=bpad, pady=bpad, columnspan=2)
        self.noiseDistLabelVar = Label(self.scoreFrame, textvariable=self.noiseDistVar, font=self.font)
        self.noiseDistLabelVar.grid(row=self.numMatchScores+6, column=0, sticky='E', padx=bpad, pady=bpad, columnspan=2)

        self.interChipDistVar = StringVar()
        self.interChipDistLabel = Label(self.scoreFrame, text='Avg. Inter-Chip HD:', font=self.bigfont)
        self.interChipDistLabel.grid(row=self.numMatchScores+7, column=0, sticky='W', padx=bpad, pady=bpad, columnspan=2)
        self.interChipDistLabelVar = Label(self.scoreFrame, textvariable=self.interChipDistVar, font=self.font)
        self.interChipDistLabelVar.grid(row=self.numMatchScores+8, column=0, sticky='E', padx=bpad, pady=bpad, columnspan=2)

        self.probAliasingVar = StringVar()
        self.probAliasingLabel = Label(self.scoreFrame, text='Probability of Alias:', font=self.bigfont)
        self.probAliasingLabel.grid(row=self.numMatchScores+9, column=0, sticky='W', padx=bpad, pady=bpad, columnspan=2)
        self.probAliasingLabelVar = Label(self.scoreFrame, textvariable=self.probAliasingVar, font=self.font)
        self.probAliasingLabelVar.grid(row=self.numMatchScores+10, column=0, sticky='E', padx=bpad, pady=bpad, columnspan=2)

        # Print measurement iterator at bottom
        self.measNumVar = StringVar()
        self.measNumLabel = Label(self, textvariable=self.measNumVar, font=self.font)
        self.measNumLabel.grid(row=6, column=1, padx=bpad, pady=bpad)

    def updateMenuBarSimulate(self):
        for chipName in self.bitSource.chipNames:
            self.menuBarSourceSimulatorSelect.add_radiobutton(label=chipName, variable=self.virtChipNumVar, value=chipName)

    def simulatorMeasureAll(self, event=None):
        self.bitSource.characterize(self.chipIdentifier)

    def simulatorPickRandom(self, event=None):
        if 'bitSource' in self.__dict__ and type(self.bitSource) == type(Simulator()):
            import random
            self.virtChipNumVar.set("v%03d" % random.randint(1, len(self.bitSource.chipNames)))

    def selectECC(self):
        print "ECC: " + ("Off" if self.correctVar.get() == 0 else "On")

    def onModeSelect(self, *args):
        if self.sourceSelected.get() != self.oldMode:
            self.close()
            self.oldMode = self.sourceSelected.get()
            self.updateChipPicker()

    def onColorMapSelect(self, *args):
        if self.colorMapSelected.get() == 'Imm. Diff.':
            self.colorMapFun = self.mapBitImmDiff
            self.buildColorMapLegend(self.colorMapImmDiff)
        else:
            self.colorMapFun = self.mapBitGrayscale
            self.buildGrayScaleLegend()
        self.updateWidgets()

    def make_pi(self, bits=None):
        "Rebuild the PhotoImage from the PUF signature"

        sigVis = PhotoImage(width=self.squareSize, height=self.squareSize)

        row = 0; col = 0
        for i in range(0, self.nb):
            sigVis.put(self.colorMapFun(i), (row, col))
            col +=1
            if col == self.squareSize:
                row += 1; col = 0

        sigVis = sigVis.zoom(self.zoomFactor,self.zoomFactor)

        return sigVis

    def updateBitAvgs(self):
        """Remember the current signature so that average bit values can be calculated"""
        for i in range(self.nb):
            self.bitAvgs[i].append(bitstring.BitArray(bool=self.bits[i]))
            if len(self.bitAvgs[i]) > self.maxAvgDepth:
                # truncate to last 'n' bits
                self.bitAvgs[i] = self.bitAvgs[i][-self.maxAvgDepth:]

    def setSigVis (self):
        self.sigVis = self.make_pi()

    def updateStatus(self):
        self.statusStr = (
                'Using Simulator' if self.sourceSelected.get() == 'Simulator' else
                'Reading from File "%s"' % os.path.basename(self.bitSource.fileName) if self.sourceSelected.get() == 'File' else
                'Connected to ROPUF' if self.sourceSelected.get() == 'ROPUF' else
                'Connected to ARBR' if self.sourceSelected.get() == 'ARBR' else
                'Not Connected'
                )
        self.updateTitle()
        print self.statusStr

    def updateWidgets(self):
        scores = sorted(self.chipIdentifier.match_map(self.bits).items(), key=lambda item: item[1])[0:self.numMatchScores]
        self.updateStatus()

        # Show matches on GUI
        for i in range(self.numMatchScores):
            if (i < len(scores)):
                self.matchLabelVars[i].set(scores[i][0])
                self.matchScoreLabelVars[i].set('%0.2f %%' % (100-scores[i][1]*100))
            else:
                # Clear out unused slots
                self.matchLabelVars[i].set('')
                self.matchScoreLabelVars[i].set('')

        self.tempVar.set(
                ("Board Temperature: %0.2f deg. C, %0.2f deg. F" % \
                        (self.bitSource.get_temp(), self.bitSource.get_temp("F")) ) \
                if ('bitSource' in self.__dict__ and type(self.bitSource) == type(QuartusCon())) else \
                        ('%s' % self.bitSource.getSetupStr()) \
                if ('bitSource' in self.__dict__ and type(self.bitSource) == type(Simulator())) else \
                        "")

        self.setSigVis()
        self.sigCanvas.create_image(0, 0, image=self.sigVis, anchor=NW)

        if(self.measurementCounter>0):
            self.bitFlipVar.set(fmtFractionPercent(self.bitFlips, self.nb))
        else:
            self.bitFlipVar.set('')

        if(self.chipIdentifier.unstable_bits_valid(self.lastRead)):
            self.unstableBitVar.set(fmtFractionPercent(self.chipIdentifier.get_num_unstable_bits(self.lastRead), self.nb))
            self.noiseDistVar.set(fmtFractionPercent(self.chipIdentifier.get_noise_dist_avg(self.lastRead), self.nb))
        else :
            self.unstableBitVar.set('')
            self.noiseDistVar.set('')

        if (self.lastRead in self.chipIdentifier.interChipDistMap):
            self.interChipDistVar.set(fmtFractionPercent(self.chipIdentifier.get_inter_dist_avg(self.lastRead), self.nb))
        else:
            self.interChipDistVar.set('')


        if self.probAliasEnVar.get() and self.chipIdentifier.get_meas_count(self.lastRead) > 2 and len(self.chipIdentifier) > 2:
            self.probAliasingVar.set( "%.1e" % (self.chipIdentifier.prob_alias()[1]) )
        else:
            self.probAliasingVar.set( "N/A" )

        self.measNumVar.set("Meas. #: %d" % (self.chipIdentifier.get_meas_count(self.lastRead)))

        self.update()

        if 'randomnessWindow' in self.__dict__:
            self.updateRandomnessWindow()


    def writeReport(self):
        reportFile = tkFileDialog.asksaveasfile(mode='w',
                                defaultextension=".txt",
                                filetypes=[("ASCII Text", ".txt")],
                                title="Save Report As...")

        def fmtHeadingString(title, decorator="-"):
            return "\n" + title + "\n" + decorator*len(title) + "\n"

        def fmtNameAndSig(name, sig):
            return "Chip Name: " + name + "\n\nResponse: " + sig.hex

        def fmtUnstableBitMap(unstableBits):
            return "\nUnstable Bit Map: " + unstableBits.hex

        print >> reportFile, fmtHeadingString("PUF Analysis Report File", "=")


        if ('bitSource' in self.__dict__ and type(self.bitSource) == type(QuartusCon())):
            print >> reportFile, "Board Temperature: %0.2f deg. C, %0.2f deg. F" % \
                    (self.bitSource.get_temp(), self.bitSource.get_temp("F"))
        elif ('bitSource' in self.__dict__ and type(self.bitSource) == type(Simulator())):
            print >> reportFile, 'Simulator Setup: %s' % self.bitSource.getSetupStr()

        print >> reportFile, fmtHeadingString("Current Measurement")
        # Could draw an ASCII representation here
        print >> reportFile, fmtNameAndSig(self.lastRead, self.bits)
        print >> reportFile, fmtUnstableBitMap(self.chipIdentifier.unstableBits[self.lastRead])

        print >> reportFile, fmtHeadingString("Scoreboard")
        scores = sorted(self.chipIdentifier.match_map(self.bits).items(), key=lambda item: item[1])[0:self.numMatchScores]
        for i in range(len(scores)):
            print >> reportFile, scores[i][0], "\t", '%0.2f %%' % (100-scores[i][1]*100)

        print >> reportFile, fmtHeadingString('PUF Metrics')
        if(self.measurementCounter>0):
            print >> reportFile, "Bit Flips: " + fmtFractionPercent(self.bitFlips, self.nb)

        if(self.chipIdentifier.unstable_bits_valid(self.lastRead)):
            print >> reportFile, "Unstable Bits: " + fmtFractionPercent(self.chipIdentifier.get_num_unstable_bits(self.lastRead), self.nb)
            print >> reportFile, "Average Noise Distance: " + fmtFractionPercent(self.chipIdentifier.get_noise_dist_avg(self.lastRead), self.nb)

        if (self.lastRead in self.chipIdentifier.interChipDistMap):
            print >> reportFile, "Average Inter-Chip Distance: " + fmtFractionPercent(self.chipIdentifier.get_inter_dist_avg(self.lastRead), self.nb)

        if self.chipIdentifier.get_meas_count(self.lastRead) > 2 and len(self.chipIdentifier) > 2:
            print >> reportFile, "Probability of Aliasing: " + ( "%.3e" % (self.chipIdentifier.prob_alias()[1]) )

        print >> reportFile, "Measurement Count: " + ("Meas. #: %d" % (self.chipIdentifier.get_meas_count(self.lastRead)))

        print >> reportFile, fmtHeadingString("Randomness Checks")
        for i, (name, fun) in enumerate(self.randomnessFunMap.items()):
            fun_metric, fun_pass = fun(self.bits)
            print >> reportFile, "%20s %.10e" % (name, fun_metric), fun_pass

        print >> reportFile, fmtHeadingString("Other Signatures")
        for name, signature in self.chipIdentifier.signatureMap.items():
            if (name != self.lastRead):
                print >> reportFile, fmtNameAndSig(name, signature)+"\n"

    def updateChipPicker(self):
        """This updates the optionmenu for picking a virtual chip from the sample of virtual chips. Applies only to the simulator. """
        if (self.sourceSelected.get() == 'Simulator') and ('bitSource' in self.__dict__) and (type(self.bitSource) == Simulator):
            self.virtChipSelect = OptionMenu(self.buttonFrame, self.virtChipNumVar, *self.bitSource.chipNames)
            self.virtChipNumVar.set(self.bitSource.chipNames[0])
            self.virtChipNumVar.trace('w', self.onVirtChipSelect)
            self.virtChipSelect.grid(row=0, column=2, padx=4, pady=4)
        elif ('virtChipSelect' in self.__dict__):
            self.virtChipSelect.grid_forget()

    def onVirtChipSelect(self, *args):
        """Handler for when new virtual chip has been selected"""
        self.reset()

    def open(self, event=None):
        """Open one of the available interfaces"""

        # Clean up if a connection is already open
        if ('bitSource' in self.__dict__):
            self.bitSource.close()
            del self.bitSource
        error = False

        # Reset error correction
        if ('corrector' in self.__dict__):
            del self.corrector

        sigFileName = os.path.join(self.outputPath, self.sourceSelected.get(), 'signatures.xml')

        if (self.sourceSelected.get() == 'Simulator'):
            self.bitSource = Simulator()
            self.bitSource.setup()
            if (not os.path.isfile(sigFileName)):
                print "Generating signature DB for simulator virtual chips...",
                self.bitSource.makeSigFile(sigFileName)
                print "OK"
        elif (self.sourceSelected.get() == 'File'):
            filename = tkFileDialog.askopenfilename(
                            defaultextension=".dat",
                            filetypes=[("Binary Data", ".dat")],
                            title="Choose PUF Data File")
            if filename:
                self.bitSource = SigFile(filename, self.nb)
                sigFileName = self.loadSigFile()
                if not sigFileName:
                    sigFileName = os.path.join(os.path.split(filename)[0], 'signatures.xml')
            else:
                error = True
        elif (self.sourceSelected.get() in self.quartusSources.keys()):
            self.bitSource = QuartusCon(
                    tclFile=self.quartusSources[self.sourceSelected.get()]['tclFile'],
                    cdf_filename=self.quartusSources[self.sourceSelected.get()]['cdf_filename'])
            self.bitSource.program()
        else:
            print 'Invalid source'

        if (not error):
            self.lastRead = ""
            self.chipIdentifier = ChipIdentify(sigFileName)
            self.reset()
            self.nextButton.config(state=NORMAL)
            self.closeButton.config(state=NORMAL)
            self.menuBarSource.entryconfig('Next', state=NORMAL)
            self.menuBarSource.entryconfig('Disconnect', state=NORMAL)
            self.menuBarChipDB.entryconfig('Clear', state=NORMAL)
            if (self.sourceSelected.get() == 'Simulator'):
                self.menuBarSource.entryconfig('Simulator', state=NORMAL)
                self.updateMenuBarSimulate()
            self.menuBarAnalyze.entryconfig('Save Report', state=NORMAL)
            self.updateStatus()
            self.updateChipPicker()

    def close(self, event=None):
        if ('bitSource' in self.__dict__):
            self.bitSource.close()
            del self.bitSource
        self.nextButton.config(state=DISABLED)
        self.closeButton.config(state=DISABLED)
        self.menuBarSource.entryconfig('Next', state=DISABLED)
        self.menuBarSource.entryconfig('Disconnect', state=DISABLED)
        self.menuBarAnalyze.entryconfig('Randomness Checks', state=DISABLED)
        self.menuBarAnalyze.entryconfig('Draw Histograms', state=DISABLED)
        self.menuBarChipDB.entryconfig('Clear', state=DISABLED)
        self.menuBarSource.entryconfig('Simulator', state=DISABLED)
        self.menuBarAnalyze.entryconfig('Save Report', state=DISABLED)
        self.updateChipPicker()

    def getChipDatPath(self, chip_name):
        return os.path.join(self.outputPath, self.sourceSelected.get(), str(chip_name) + '.dat')

    def next(self, event=None):
        if 'bitSource' not in self.__dict__:
            return

        if self.sourceSelected.get() == 'Simulator':
            new_bits = self.bitSource.next(self.virtChipNumVar.get())
        else:
            new_bits = self.bitSource.next()

        # Determine chip's name
        if len(self.chipIdentifier)>0:
            chip_name, match_dist = self.chipIdentifier.identify(new_bits)
            print "Best match for signature: %s with %6f Hamming distance" % (chip_name, match_dist)
        if len(self.chipIdentifier)==0 or match_dist > self.noiseThreshold:
            # Don't know this chip
            chip_name = tkSimpleDialog.askstring('Enter Chip Name', 'The noise threshold (%02d %%) has been exceeded or this is a new chip.\nPlease enter its name:' % (100*self.noiseThreshold), initialvalue=chip_name if len(self.chipIdentifier)>0 else '')
            self.chipIdentifier.add(chip_name, new_bits)
            self.chipIdentifier.save() # don't really need to do this until we close
        self.chipIdentifier.process_sig(chip_name, new_bits) # compute some greedy statistics

        # Don't write the bits in case of file read-back
        if self.sourceSelected.get() != 'File':
            if chip_name != self.lastRead:
                if 'sigFileWriter' in self.__dict__:
                    self.sigFileWriter.close()
                filePath = self.getChipDatPath(chip_name)
                print "Saving PUF data to '%s'" % filePath
                self.sigFileWriter = SigFile(filePath, mode='a')
            self.sigFileWriter.append(new_bits)
            self.sigFileWriter.save() # TODO delay this

        # Error correction filter
        if (self.correctVar.get() == 1):
            if ('corrector' not in self.__dict__ or chip_name != self.lastRead):
                self.corrector = bch_code.bch_code()
                if (self.chipIdentifier.get_meas_count(self.lastRead)):
                    self.corrector.setup(self.chipIdentifier.get_sig(self.lastRead))
                else:
                    self.corrector.setup(new_bits)
                    print "ECC Enrollment: ",
                print "Syndrome:\n" + self.corrector.syndrome

            if (self.chipIdentifier.get_meas_count(self.lastRead) > 1):
                print "ECC Recovery: ",
                numErrors = hd(new_bits, self.chipIdentifier.get_sig(self.lastRead))
                print "Errors from enrollment: %d" % numErrors
                if numErrors > self.corrector.t:
                    print "ERROR: Error Correction Code strength %d not enough to correct %d errors" % (self.corrector.t, numErrors)
                else:
                    try:
                        corrected = self.corrector.decode(new_bits)
                        print "Errors corrected: %d" % hd(new_bits, corrected)
                        print "Errors after correction: %d" % hd(self.bits, corrected)
                        new_bits = corrected
                    except ValueError as e:
                        print "Call to ECC process failed!"

        self.lastRead = chip_name

        # Report on unstable bits
        if self.chipIdentifier.unstable_bits_valid(self.lastRead):
            print "Unstable bits: %d / %d = %.3f %%" % (self.chipIdentifier.get_num_unstable_bits(self.lastRead), self.nb, (float(self.chipIdentifier.get_num_unstable_bits(self.lastRead))/self.nb)*100)
            print "Unstable bit map:"
            print repr(self.chipIdentifier.unstableBits[self.lastRead])

        print "Measurement number: ", self.chipIdentifier.get_meas_count(chip_name)

        if (self.measurementCounter > 0):
            self.bitFlips = hd(self.bits, new_bits)
        elif (self.chipIdentifier.get_meas_count(chip_name) > 0):
            self.measurementCounter = self.chipIdentifier.get_meas_count(chip_name)
            self.bitFlips = hd(self.chipIdentifier.signatureMap[chip_name], new_bits)

        self.bits = new_bits
        self.updateBitAvgs()

        self.menuBarAnalyze.entryconfig('Randomness Checks', state=NORMAL)
        self.menuBarAnalyze.entryconfig('Draw Histograms', state=NORMAL)
        self.updateWidgets()
        self.measurementCounter += 1

    def setScale(self, event=None):
        self.zoomFactor = max([int(tkSimpleDialog.askstring('Enter Scale', 'Current scale: %d, current square dimension: %d\nEnter new scale (scale >= 1):' % (self.zoomFactor, self.squareSize))), 1])
        self.sigCanvas.config(width=self.squareSize*self.zoomFactor,
                        height=self.squareSize*self.zoomFactor)
        self.make_pi()
        if self.measurementCounter > 0:
            self.updateWidgets()

    def setFontSize(self, event=None):
        newFontSize = max([4, int(tkSimpleDialog.askstring('Enter Font Size', 'Current font size: %d\nEnter new font size (minimum 4):' % self.font['size']))])
        self.font.configure(size=newFontSize)
        self.bigfont.configure(size=newFontSize+2)


    def loadSigFile(self, event=None):
        sigFileName = tkFileDialog.askopenfilename(
                defaultextension=".xml",
                filetypes=[("Signature XML File", ".xml")],
                title="Choose Signature DB File")
        if sigFileName != '':
            self.chipIdentifier = ChipIdentify(sigFileName)

        return sigFileName

    def clearSigFile(self):
        if tkMessageBox.askyesno("Confirm", "Are you sure you want to clear the Signature DB\nat '%s'?" % self.chipIdentifier.fileName):
            self.chipIdentifier.clear()
        self.updateWidgets()

    # This has enough functions and variables to become its own object
    def runRandomnessCheck(self):
        if 'randomnessWindow' not in self.__dict__:

            self.randomnessWindow = Toplevel()
            self.randomnessWindow.title("Randomness Checks")
            self.randomnessWindow.protocol("WM_DELETE_WINDOW", self.closeRandomnessWindow)

            self.randomnessLabels = []
            self.randomnessFields = []
            self.randomnessFieldVars = []
            self.randomnessPass = []
            self.randomnessPassVars = []
            for i, (name, fun) in enumerate(self.randomnessFunMap.items()):
                self.randomnessLabels.append (Label(self.randomnessWindow, text=name, font=self.font))
                self.randomnessLabels[i].grid(row=i, column=0, sticky='W')
                self.randomnessFieldVars.append(StringVar())
                self.randomnessFields.append (Label(self.randomnessWindow, textvariable=self.randomnessFieldVars[i], font=self.font))
                self.randomnessFields[i].grid(row=i, column=1)
                self.randomnessPassVars.append(StringVar())
                self.randomnessPass.append( Label(self.randomnessWindow, textvariable=self.randomnessPassVars[i], font=self.font))
                self.randomnessPass[i].grid(row=i, column=2)

        self.updateRandomnessWindow()

    def updateRandomnessWindow(self):
        for i, (name, fun) in enumerate(self.randomnessFunMap.items()):
            fun_metric, fun_pass = fun(self.bits)
            print "%20s %.5e" % (name, fun_metric), fun_pass
            self.randomnessFieldVars[i].set("%f" % fun_metric)
            self.randomnessPassVars[i].set("Pass" if fun_pass else "Fail")
        self.randomnessWindow.update()

    def closeRandomnessWindow(self):
        self.randomnessWindow.destroy()
        del self.randomnessWindow

    def runDistHist(self):
        import numpy
        import matplotlib.pyplot as plt

        frac_bits = self.distHistFractions.get() != 0
        plt.ion() # switch to interactive mode, else plot functions block GUI operation

        noise_dists = numpy.array(self.chipIdentifier.get_all_noise_dists(), numpy.double)
        inter_chip_dists = numpy.array(self.chipIdentifier.get_all_inter_chip_dists(), numpy.double)

        noise_threshold, prob_alias = self.chipIdentifier.prob_alias()
        title = "Noise and Inter-Chip Hamming Distances\nProbability of Aliasing: %1.3e" % prob_alias
        noise_label = 'Noise $\\mu=$' + \
                ('%0.3f' % float(sum(noise_dists)/len(noise_dists)/self.nb) if frac_bits else
                        ('%d' % (sum(noise_dists)/len(noise_dists)) ) ) + \
                ', $N=$%d' % len(noise_dists)
        inter_chip_label = 'Inter-Chip $\\mu=$' + \
                ('%0.3f' % float(sum(inter_chip_dists)/len(inter_chip_dists)/self.nb) if frac_bits else
                        ('%d' % (sum(inter_chip_dists)/len(inter_chip_dists)) ) ) + \
                ', $N=$%d' % len(inter_chip_dists)
        noise_threshold_label = "Noise Threshold = " + \
                (("%1.3f" % (float(noise_threshold)/self.nb)) if frac_bits else
                        ('%d' % math.ceil(noise_threshold)))
        xlabel = "Relative Hamming Distance (Response Length Fraction)" if frac_bits else "Hamming Distance"

        plt.clf()

        if self.distHistSelected.get() == 'Simple':
            plt.xlim(0, 1 if frac_bits else self.nb)
            plt.hist(noise_dists/(self.nb if frac_bits else 1), normed=True, cumulative=False, color='r', label=noise_label)
            plt.hist(inter_chip_dists/(self.nb if frac_bits else 1), normed=True, cumulative=False, color='b', label=inter_chip_label)
            plt.axvline(noise_threshold/(self.nb if frac_bits else 1), color='g', label=noise_threshold_label)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel("Probability")
            plt.legend()
        elif self.distHistSelected.get() == 'Split':
            plt.subplot(211)
            plt.title(title)
            plt.hist(noise_dists/(self.nb if frac_bits else 1), normed=True, cumulative=False, color='r', label=noise_label)
            plt.axvline(noise_threshold/(self.nb if frac_bits else 1), color='g', label=noise_threshold_label)
            plt.ylabel("Probability")
            plt.legend()

            plt.subplot(212)
            plt.hist(inter_chip_dists/(self.nb if frac_bits else 1), normed=True, cumulative=False, color='b', label=inter_chip_label)
            plt.xlabel(xlabel)
            plt.ylabel("Probability")
            plt.legend()
        elif self.distHistSelected.get() == 'Cumulative':
            nd_hist, nd_bin_edges = numpy.histogram(noise_dists, density=True)
            nd_hist_cum = nd_hist.cumsum().astype(float) / sum(nd_hist)
            plt.plot(numpy.append(nd_bin_edges, self.nb)/(self.nb if frac_bits else 1), numpy.append(nd_hist_cum, [1, 1]), drawstyle='steps', color='r', label=noise_label)

            icd_hist, icd_bin_edges = numpy.histogram(inter_chip_dists, density=True)
            icd_hist_cum = icd_hist.cumsum().astype(float) / sum(icd_hist)
            plt.plot(numpy.append(icd_bin_edges, self.nb)/(self.nb if frac_bits else 1), numpy.append(icd_hist_cum, [1, 1]), drawstyle='steps', color='b', label=inter_chip_label)

            plt.axvline(noise_threshold/(self.nb if frac_bits else 1), color='g')

            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel("Probability")
            plt.legend(loc='lower right') # show the legend
            plt.axis([0, 1 if frac_bits else self.nb, 0, 1])


print __copyright__
root = Tk()
app = Application(master=root)
app.mainloop()
