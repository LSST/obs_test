#!/usr/bin/env python2
from __future__ import absolute_import, division
"""Assemble a set of LSSTSim channel images into one obs_test image
"""
# 
# LSST Data Management System
# Copyright 2014 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
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
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import os.path
import sys
import glob
import re

import numpy
import pyfits

SizeY = 1000 # number of pixels per amplifier in X direction (Y uses all pixels)

KeysToCopy = (
    "XTENSION",
    "CTYPE1",
    "CRPIX1",
    "CRVAL1",
    "CTYPE2",
    "CRPIX2",
    "CRVAL2",
    "CD1_1",
    "CD1_2",
    "CD2_1",
    "CD2_2",
    "RADESYS",
    "EQUINOX",
    "EPOCH",
    "OBSID",
    "TAI",
    "MJD-OBS",
    "EXPTIME",
    "DARKTIME",
    "FILTER",
    "AIRMASS",
)

def openChannelImage(dirPath, x, y):
    """Open an LSSTSim channel image
    """
    globStr =  os.path.join(dirPath, "imsim_*_R22_S00_C%d%d*" % (x, y))
    inImagePathList = glob.glob(globStr)
    if len(inImagePathList) != 1:
        raise RuntimeError("Found %s instead of 1 file" % (inImagePathList,))
    inImagePath = inImagePathList[0]
    inImageFileName = os.path.basename(inImagePath)
    if re.match(r"imsim_\d\d\d\d\d", inImageFileName):
        # raw images are integer images
        print "loading as a unsigned integer data"
        uint = True
    else:
        print "loading as float data"
        uint = False
    return pyfits.open(inImagePath, uint=uint)

def assembleImage(dirPath):
    """Make one image by combining half of amplifiers C00, C01, C10, C11 of lsstSim data
    """
    outHDUList = pyfits.core.HDUList()

    inHDUList = openChannelImage(dirPath, 0, 0)
    xSubSize, ySubSize = None, None
    skipFirstHDU = False
    for x in (0, 1):
        for y in (0, 1):
            inHDUList = openChannelImage(dirPath, x, y)

            if x == 0 and y == 0:
                numHDUs = len(inHDUList)
                if numHDUs in (2, 4):
                    skipFirstHDU = True
                elif numHDUs not in (1, 3):
                    raise RuntimeError("Unknown image type; %s HDUs" % numHDUs)
                print "found %s HDUs" % (numHDUs,)

            for hduIndex, inHDU in enumerate(inHDUList):
                if hduIndex == 0 and skipFirstHDU:
                    outHDUList.append(pyfits.PrimaryHDU())
                    continue

                inImageArr = inHDU.data
                inImageSubArr = inImageArr[-SizeY:,] # view of top SizeY pixels x full width
                if xSubSize is None:
                    xSubSize = inImageSubArr.shape[1]
                    ySubSize = inImageSubArr.shape[0]

                # flip the data, if need be
                if y == 1:
                    inImageSubArr = inImageSubArr[::-1, ::-1]
                
                if x == 0 and y == 0:
                    outArr = numpy.zeros((ySubSize*2, xSubSize*2), dtype=inImageSubArr.dtype)
                    if hduIndex > 0:
                        outHDU = pyfits.ImageHDU(data=outArr)
                    else:
                        outHDU = pyfits.PrimaryHDU(data=outArr)
                    outHDUList.append(outHDU)
                    inHeader = inHDU.header
                    for key in KeysToCopy:
                        if key in inHeader:
                            outHDU.header[key] = (inHeader[key], inHeader.comments[key])

                xStart = x * xSubSize
                yStart = y * ySubSize
                outHDUList[hduIndex].data[yStart:yStart+ySubSize, xStart:xStart+xSubSize] = inImageSubArr

    outHDUList.writeto("image.fits")

if __name__ == "__main__":
    if len(sys.argv) not in (1, 2):
        print """"Usage: assembleLsstChannels.py [dir]

dir is a directory containing LSSTSim channel images (at least for channels 0,0, 0,1, 1,0 and 1,1),
and defaults to the current directory.
Output is written to the current directory as "image.fits" (which must not already exist).
"""
        sys.exit(1)
    if len(sys.argv) == 2:
        dirPath = sys.argv[1]
    else:
        dirPath = "."
    assembleImage(dirPath)
