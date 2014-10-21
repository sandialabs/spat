# Copyright (2014) Sandia Corporation. Under the terms of Contract
# DE-AC04-94AL85000, there is a non-exclusive license for use of this
# work by or on behalf of the U.S. Government. Export of this program
# may require a license from the United States Government.

NOTICES := license.txt README.txt COPYRIGHT.txt

SOURCES := simulator/__init__.py simulator/abstractsimulator.py simulator/ropuf.py bch_code.py bitstring.py bitstringutils.py chipidentify.py spat.py quartus.py randomness.py sigfile.py 

EXTRAS := spat.bat Makefile

clean:
	find . -name "*.py[oc]" -exec rm {} \;
	rm *~ *.bak *.swp
.PHONY: clean

linecount:
	wc -l ${SOURCES}

DIST_NAME := spat-dist

tgz: ${DIST_NAME}.tar.gz
tar.gz: ${DIST_NAME}.tar.gz
${DIST_NAME}.tar.gz: ${SOURCES} ${NOTICES} ${EXTRAS}
	tar -cvzf ${DIST_NAME}.tar.gz ${SOURCES} ${NOTICES} ${EXTRAS}

zip: ${DIST_NAME}.zip
${DIST_NAME}.zip: ${SOURCES} ${NOTICES} ${EXTRAS}
	zip ${DIST_NAME}.zip ${SOURCES} ${NOTICES} ${EXTRAS}

7z: ${DIST_NAME}.7z
${DIST_NAME}.7z: ${SOURCES} ${NOTICES} ${EXTRAS}
	7z a ${DIST_NAME}.7z ${SOURCES} ${NOTICES} ${EXTRAS}

