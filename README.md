
Sandia National Laboratories PUF Analysis Tool
==============================================

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

<a href="https://travis-ci.com/sandialabs/spat">
    <img src="https://api.travis-ci.com/sandialabs/spat.svg?branch=py2to3" 
         alt="Travis CI Build Status">
</a>

Introduction
------------

This program is a graphical user interface for measuring and performing inter-
active analysis of physical unclonable functions (PUFs). It is intended for
demonstration and education purposes. See license.txt for license details.

The program features a PUF visualization that demonstrates how signatures
differ between PUFs and how they exhibit noise over repeated measurements. A
similarity scoreboard shows the user how close the current measurement is to
the closest chip signatures in the database. Other metrics such as average
noise and inter-chip Hamming distances are presented to the user. Randomness
tests published in NIST SP 800-22 can be computed and displayed. Noise and
inter-chip histograms for the sample of PUFs and repeated PUF measurements can
be drawn.

Application
-----------

The program was designed to be used in an educational setting to allow users
to interact with PUFs and analyze their performance. This framework serves as
a step to making PUFs more practical and more broadly understood. 

Requirements
------------

SPAT requires Python 2. It is tested with Python 2.7. Python is freely
available from the Python Software Foundation at:

    www.python.org

The following packages for Python are required for additional features:

    tkinter numpy matplotlib scipy

These packages are available on most GNU/Linux distributions. Unofficial Windows
binaries for these packages are available from UCI at:

    http://www.lfd.uci.edu/~gohlke/pythonlibs/

Otherwise, these packages are available from their respective websites:

    NumPy at www.numpy.org

    matplotlib at matplotlib.org

    SciPy at scipy.org

Installation
------------

Extract the program files from the ZIP distribution to somewhere you have
read/write access. In a shell or command prompt (Windows), execute the
'spat.py' file with the Python interpreter:

    python spat.py

For convenience, a batch file is included for Windows, although this file may
have to be edited if you installed Python 2.7 to a non-standard location. Just
double-click:

    spat.bat

### Ubuntu

  > apt install python python-pip python-tk

### Red Hat

  > yum install tkinter


Tutorial
========

Once the GUI is up and running, you can begin to experiment with the built-in
PUF simulator. Read the following steps and follow along with the GUI.

Note that the simulator is the default choice from the Source Select drop-down
menu. With the simulator selected, click the Open button or press the <O> key.

Choose a virtual chip from the Source Simulator Virtual Chip drop-down menu.
With a real PUF, you would choose one and connect it at this time.

Click Next or press the space bar to get the first measurement. If this is the
first time that this virtual chip has been measured, a dialog will pop up
asking you to name the device. The program does not associate the virtual chip
selection with the signature metrics and instead asks the user if it is not
sure which chip has been measured. If this were a real chip, you would enter
its serial number. The PUF signature bitmap will update. Note the legend at the
bottom center of the bitmap. The color scheme can also be changed here.

Note that the simulator parameters are printed at the bottom of the screen
below the legend. P stands for parametric (as in, one of a set of measurable
factors), and E stands for error. In our simulator terminology, a PUF consists
of a set of parametrics that exhibit a level of noise when they are measured. 
Hence, measurements of the parametrics are modeled by a distribution which has
a mean value P_mu and a standard deviation P_sd, and noise is added to this 
which follows another distribution with mean E_mu and standard deviation E_sd. 
Other PUF sources can display other information here on the front panel.

Continue clicking Next or pressing the space bar to advance the measurement.
Until a significant number of chips are measured a number of times, there may
be some runtime warnings that display in the console. These can be safely
ignored. Note that some bits flip between measurements and that the metrics on
the right-hand side are being updated. The number of total measurements made on
this virtual chip is printed on the bottom-right-hand side.

Next, choose another virtual chip from the Source Simulator Virtual Chip drop-
down menu. Alternatively, you may select Source -> Simulator -> Random Chip or
press the <R> key to choose one at random. As before, click Next or press the
space bar a few times. There will now be at least two chips on the similarity
scoreboard. Note that the similarity of the current measurement with the
virtual chip that is selected should be near 100% and the similarity with
the other virtual chips should be down near 50%.

You may continue measuring a few other virtual chips in this fashion or select
Source -> Simulator -> Measure All. The Measure All command will measure each
virtual chip several times so that the sample of chips is fully characterized.

Next, select Analyze -> Randomness Checks from the menu. This will pop up a new
window that displays a few of the randomness metrics from NIST SP 800-22 "A
Statistical Test Suite for Random and Pseudorandom Number Generators for
Cryptographic Applications". These metrics will be updated whenever a new
measurement is made as long as the Randomness Checks window is open. Please
note that it is normal for some of these checks to fail most of the time for a
given PUF architecture. 

Next, select Analyze -> Draw Histograms from the menu. A new window will pop up
displaying the noise and inter-chip histograms. Each time a measurement is
made, a noise distance and several inter-chip distances are stored. If it is not
the first measurement, a noise distance is stored. If there have been other
chips measured, one inter-chip distance is stored for each other chip that is
known. Unlike the Randomness Checks window, this display will not update when
you click Next. This decision was made to keep the amount of time required to
update the display low. There are several historgram types which can be
selected. These are simple, split and cumulative, which all display the same 
information in different ways. The simple option plots the inter-chip and noise
distributions directly. The split option shows the inter-chip and noise
distributions in separate plots that are stacked vertically. The cumulative 
option shows the effective cumulative distribution function for the samples of
inter-chip and noise distances. 

Finally, select Analyze -> Save Report if you would like to output all of the
metrics to a file.


Description of Commands
=======================

All of the controls can be accessed via the "file menu". Some are repeated at
the bottom of the front panel for convenience. The outputs consist of the
signature visualization (the main feature of the GUI), the similarity
scoreboard and other statistics on the right-hand side, the randomness checks
window, the histograms window, the signature log files and statistics files
(XMLs) and the Report.

Source Submenu
--------------

Within the source submenu, you may select the PUF source, open and close the
connection, take a measurement and enable error correction coding (ECC). The
Simulator submenu has functions for facilitating choosing a virtual chip from
the virtual lot.

Chip DB Submenu
---------------

The chip database tracks the names and responses of the PUFs that are measured.
It also tracks things such as a map of unstable bits for each PUF, statistics
such as the number of measurements made for each PUF, and noise and inter-chip
distances. By default, the data is stored in XML format at the following path:

data/[Source Name]/signatures.xml

Under the Chip DB menu, you can click Open to load an alternative XML file.
Click save to write the current data to the XML file (this is normally done
upon exit). Click Clear to erase the signatures in the database and all of the
statistics.

View Submenu
------------

Within the View submenu, options for the front panel can be selected. The PUF
signature bitmap can be scaled. The fonts can also be scaled. These options are
provided for presentation purposes.

The colormap can be selected under the View menu or on the front panel. The two
color schemes are "grayscale" and "immediate difference". The default color
scheme, "greyscale", represents the average value for each bit, with black
representing 0 and white representing 1. Unstable bits will be shown with a gray
value in between. In the immediate difference scheme, stable 0 bits are shown
with black and stable 1 bits are shown in white. If a bit position has ever
flipped, it is marked unstable, and is shown in red or yellow if it is
currently 0 or 1, respectively.

The last item in this menu allows the user to disable the probability of
aliasing metric display on the front panel. This display should be disabled
when there are a large number of chips in the signature database. This metric
is computed each time a measurement is made and can make the interface very
slow when using a large number of chips. 

Analyze Submenu
---------------

In the Analyze menu, the Randomness checks window can be opened, a number of
histogram types can be plotted, and a report can be generated.

The Randomness checks are metrics published in NIST SP 800-22 and can help the
user decide if the current PUF response is random or not. Please note that it
is normal for some of these checks to fail most of the time for a given PUF
architecture. 

The histograms help the user decide the PUF signal to noise ratio. The ideal
Hamming distance between two PUF responses is 50% of the bits. The ideal Hamming
distance between any two measurements of the same PUF is zero. The probability
of aliasing is also shown on the histogram plots. This probability is computed
by first fitting the distributions of both the inter-chip and noise Hamming
distances with Gamma distributions. Then, a threshold is chosen that represents
the upper bound of 99.7% of the noise distances. Finally, we evaluate the
Cumulative Distribution Function (CDF) of the inter-chip distances at this noise
threshold. This number represents the probability that two PUFs (chips) will
have responses with Hamming distances less than the level of noise apart. Note
that although this metric can be computed with at least two measurements of a
single PUF and at least two known PUF signatures, it should not be used until a
significant number of measurements have been made. We recommend that many PUFs
be measured (30 or more) and that each PUF is measured several times (30 times
or more).

The report function allows the user to capture all the information on the front
panel to a file.

Front Panel
-----------

We define the front panel to include all of the widgets on the main window
excluding the File menu. The PUF signature visualization is meant to be the
central focus of the GUI. In this widget, the PUF response bits are split into
sqrt(N) rows and columns, where N is the PUF response length.

Below the signature visualization is its legend. On the left-hand side, you may
choose the color scheme. The color schemes are described above in the tutorial.

Along the bottom of the front panel are some controls which are available in the
File menu, but are repeated here for convience. You may choose the PUF source,
open the source, enable error correction coding (ECC), advance the measurement
and disconnect.

On the right-hand side are all of the PUF metrics computed on the sample of PUFs
which have been measured. At the top is the similarity scoreboard. This shows
the similarity, in % bits, between the current PUF measurement and the closest
of the signatures in the database. Next is the number of flipped bits between
the current measurement and the previous one. This is reported as both a
fraction and a percentage. Next, the number of unstable bits is reported. A bit
map is maintained of unstable bits using the logical OR of the bit map 
(initially all zeros) with the XOR of the current measurement and the previous
measurement.  Effectively, bits that flip between two consecutive measurements
are forever set in the unstable bit map. Next is the average noise and inter-
chip Hamming distances. The average noise Hamming distance is computed among
all PUFs which have been measured. Each time that a measurement is made, the
number of bits that flipped between the current measurement and the last is
added to the set of noise distances. Also with each measurement, the Hamming
distances between the current signature and the signatures for all other known
PUFs are computed. These are referred to as the inter-chip distances. Finally,
the probability of aliasing is shown. This metric is described above in the
tutorial, and represents the probability that two PUFs like the ones in your
sample will have responses that are within the noise tolerance of one another.
As mentioned above, this metric should be ignored unless a significant number
of PUFs have been measured and a significant number of measurements have been
made on each.


About the Simulator
===================

The simulator produces signatures by emulating an implementation of a ring
oscillator (RO) PUF. When the simulator is first run, it generates a sample of
virtual chips. For each chip, it generates a collection of RO frequencies. These
frequencies are taken from a normal distribution (random.normalvariate). The
default parameters for this distribution are specified in the simulator.py file.
To generate a binary signature for one of the virtual chips, noise is added to 
the RO frequencies which were generated in the previous step. The magnitude of 
noise is also a parameter to the simulator. Then, the noisy RO frequencies are 
compared to generate binary bits with varying stabilities.

About Error Correction
======================

Please note that the facilities for performing ECC are included with the GUI, 
but the binary executables are not included. These two binaries encode and
decode the signatures using a BCH cyclic error-correcting code. When a measure-
ment is made, the encode utility is used to create the syndrome. This syndrome
is stored in the chip database and can be recalled to correct specific number
of errors in subsequent measurements. 

The source code for the BCH encoder/decoder software from Micron Technology,
Inc. <nandsupport@micron.com> was obtained at:
http://www.codeforge.com/article/136423

Files
=====

The GUI writes files to the following locations.

simulator_setup.xml                     Describes a sample of virtual chips
data/[source name]/signatures.xml       Name to signature mapping and statistics
data/[source name]/[chip name].dat      Binary record of each measurement made


Note about Extending
====================

Obviously, the system we have developed won't be a perfect fit for every PUF.
First, there is currently no way to provide a challenge to the PUF. Second, the
user cannot change the PUF size on the GUI. Third, the visualization has only
been tested when the number of PUF bits is a perfect square. In other words, the
number of PUF bits has to be the square of some integer. Provided as a set of
Python modules and scripts, the program was designed to allow the user to look
under the hood and modify the way it works. Hopefully, we will be able to
continue developing the program to suit the needs of most applications. In the
mean time, feel free to modify the program and give us feedback.

Interfacing with Your Hardware
------------------------------

In quartus.py, an interface is provided for programming an FPGA and
communicating with a script (not provided) which reads signatures from the FPGA.
This script is interactive and provides a hexadecimal-encoded PUF response to
standard output each time the user sends a newline character. It will ignore any
initial data output by the script before the first newline character is input.
After the PUF signature and a newline character, the script is expected to
output a time stamp and a temperature code, separated by a space. The format for
the time stamp is Unix epoch. The format for the temperature is a degrees
Celcius fraction string. An example output follows.

[user presses return]
e741cc88ca80b9919561fba122c0ef4150a1ee8ce3619d8c42c1bb9981a0f7b04340ebe586a1d988
4161ab8052e1efa8a5c0ef004b81eca1d3a1b980a661fb8146e0e70189d1ea8453a19d09e761aa80
c6e071a5cdc0e98913b1c2816771a9a0cae1cb0cd3c0ae89a381a9814320daa1c640a58ccce1eb89
99c0db8972a1afa480
1362077874 31.69

The list of sources are configured in 'spat.py' in Application.sourceList and
Application.quartusSources.

