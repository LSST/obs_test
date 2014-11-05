#!/usr/bin/env python2
"""Make a mask image from a fits table of defects

Example of usage:
setup meas_algorithms
setup obs_lsstSim -j
./convertDefects.py $OBS_LSSTSIM_DIR/description/defects/rev_02272012

If you prefer not to setup obs_lsstSim you can specify the whole path
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

import pyfits

import lsst.afw.image as afwImage
import lsst.meas.algorithms as measAlg
from lsst.ip.isr import maskPixelsFromDefectList

import lsst.afw.geom as afwGeom

def getBBoxList(path, detectorName):
    """Get a list of defects as a list of bounding boxes
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

def writeDefectsFile(bboxList, path):
    maskBBox = afwGeom.Box2I(afwGeom.Point2I(0, 0), afwGeom.Extent2I(1,1))
    for box in bboxList:
        maskBBox.include(box)

    defectsMaskedImage = afwImage.MaskedImageF(maskBBox)
    defectList = measAlg.DefectListT()
    for bbox in bboxList:
        nd = measAlg.Defect(bbox)
        defectList.append(nd)
    maskPixelsFromDefectList(defectsMaskedImage, defectList, maskName='BAD')
    defectsMaskedImage.getMask().writeFits("defectMask.fits")
    print "wrote defectsMask.fits with bbox", maskBBox,

if len(sys.argv) != 3:
    print "To use: convertDefects defects_fits_table detector_name"
    sys.exit(1)

defectsPath = sys.argv[1]
detectorName = sys.argv[2]
bboxList = getBBoxList(defectsPath, detectorName)
print "found %d defects" % (len(bboxList),)
writeDefectsFile(bboxList, detectorName)
