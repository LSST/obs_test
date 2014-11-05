#!/usr/bin/env python2
"""Construct a defects file from the mask plane of a test camera bias frame

Example of usage:
setup meas_algorithms
setup ip_isr
./defectsFromBias.py pathToBiasExposure
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
import sys
import time
import itertools

import numpy
import pyfits

import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
from lsst.ip.isr import getDefectListFromMask

defectsPath = "defects_c0.fits"
detectorName = "0"
detectorSerial = "0000011"

def getBBoxList(path, detectorName):
    """Read a defects file and return the defects as a list of bounding boxes
    """
    with pyfits.open(path) as hduList:
        for hdu in hduList[1:]:
            if hdu.header["name"] != detectorName:
                print "skipping header with name=%r" % (hdu.header["name"],)
                continue

            bboxList = []
            for data in hdu.data:
                bbox = afwGeom.Box2I(
                    afwGeom.Point2I(int(data['x0']), int(data['y0'])),
                    afwGeom.Extent2I(int(data['width']), int(data['height'])),
                )
                bboxList.append(bbox)
            return bboxList
        raise RuntimeError("Data not found for detector %r" % (detectorName,))

def writeDefectsFile(bboxList, path, detectorSerial, detectorName):
    head = pyfits.Header()
    head.update('SERIAL', detectorSerial,'Serial of the detector')
    head.update('NAME', detectorName,'Name of detector for this defect map')
    head.update('CDATE',time.asctime(time.gmtime()),'UTC of creation')

    x0 = numpy.array([d.getMinX() for d in bboxList])
    y0 = numpy.array([d.getMinY() for d in bboxList])
    width = numpy.array([d.getWidth() for d in bboxList])
    height = numpy.array([d.getHeight() for d in bboxList])

    col1 = pyfits.Column(name='x0', format='I', array=numpy.array(x0))
    col2 = pyfits.Column(name='y0', format='I', array=numpy.array(y0))
    col3 = pyfits.Column(name='height', format='I', array=numpy.array(height))
    col4 = pyfits.Column(name='width', format='I', array=numpy.array(width))
    cols = pyfits.ColDefs([col1, col2, col3, col4])
    tbhdu = pyfits.new_table(cols, header = head)
    hdu = pyfits.PrimaryHDU()
    thdulist = pyfits.HDUList([hdu, tbhdu])
    thdulist.writeto(defectsPath)

if len(sys.argv) != 2:
    print "To use: defectsFromBias.py pathToBiasExposure"
    sys.exit(1)

biasPath = sys.argv[1]
biasMI = afwImage.MaskedImageF(biasPath)
defectList = getDefectListFromMask(biasMI, "BAD", growFootprints=0)
bboxList = [defect.getBBox() for defect in defectList]
writeDefectsFile(bboxList, defectsPath, detectorSerial, detectorName)
print "wrote defects file %r" % (defectsPath,)

test2BBoxList = getBBoxList(defectsPath, detectorName)
assert len(bboxList) == len(test2BBoxList)
for boxA, boxB in itertools.izip(bboxList, test2BBoxList):
    assert boxA == boxB
print "verified that the file %r round trips correctly" % (defectsPath,)