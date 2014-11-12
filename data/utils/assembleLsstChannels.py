#!/usr/bin/env python2
from __future__ import absolute_import, division
"""Assemble a set of LSSTSim channel images into one obs_test image

Example of usage:
./assembleLsstChannels.py <path-to-LSSTSim-repo>/raw/v890104911g_R22_S00/
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

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage

SizeY = 1000 # number of pixels per amplifier in X direction (Y uses all pixels)

KeysToCopy = (
    "EPOCH",
    "OBSID",
    "TAI",
    "MJD-OBS",
    "EXPTIME",
    "DARKTIME",
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
        print "loading %s as raw unsigned integer data" % (inImageFileName,)
        exposureClass = afwImage.ExposureU
    else:
        print "loading %s as float data" % (inImageFileName,)
        exposureClass = afwImage.ExposureF
    return exposureClass(inImagePath)

def assembleImage(dirPath):
    """Make one image by combining half of amplifiers C00, C01, C10, C11 of lsstSim data
    """
    inExposure = openChannelImage(dirPath, 0, 0)
    fullInDim = inExposure.getDimensions()
    yStart = fullInDim[1] - 1000
    if yStart < 0:
        raise RuntimeError("channel image unexpectedly small")
    subDim = afwGeom.Extent2I(fullInDim[0], 1000) # dimensions of the portion of a channel that we use
    inSubBBox = afwGeom.Box2I(afwGeom.Point2I(0, yStart), subDim)
    outBBox = afwGeom.Box2I(afwGeom.Point2I(0, 0), subDim * 2)
    outExposure = inExposure.Factory(outBBox)

    # copy WCS, filter and other metadata
    if inExposure.hasWcs():
        outExposure.setWcs(inExposure.getWcs())
    outExposure.setFilter(inExposure.getFilter())
    inMetadata = inExposure.getMetadata()
    outMetadata = outExposure.getMetadata()
    for key in KeysToCopy:
        if inMetadata.exists(key):
            outMetadata.set(key, inMetadata.get(key))
    outExposure.setMetadata(outMetadata)

    for x in (0, 1):
        for y in (0, 1):
            inExposure = openChannelImage(dirPath, x, y)
            inView = inExposure.Factory(inExposure, inSubBBox)
            inMIView = inView.getMaskedImage()

            # rotate the data by 180 degreees for the y = 1 channels
            if y == 1:
                inArrList = inMIView.getArrays()
                for arr in inArrList:
                    if numpy.any(arr != 0):
                        arr[:, :] = numpy.array(arr[::-1, ::-1])

            xStart = x * subDim[0]
            yStart = y * subDim[1]
            outSubBBox = afwGeom.Box2I(afwGeom.Point2I(xStart, yStart), subDim)
            outView = outExposure.Factory(outExposure, outSubBBox)
            outMIView = outView.getMaskedImage()
            outMIView <<= inMIView

    outExposure.writeFits("image.fits")
    print "wrote assembled data as 'image.fits'"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print """"Usage: assembleLsstChannels.py [dir]

dir is a directory containing LSSTSim channel images (at least for channels 0,0, 0,1, 1,0 and 1,1),
and defaults to the current directory.
Output is written to the current directory as "image.fits" (which is overwritten if it exists)
"""
        sys.exit(1)
    if len(sys.argv) == 2:
        dirPath = sys.argv[1]
    else:
        dirPath = "."
    assembleImage(dirPath)
