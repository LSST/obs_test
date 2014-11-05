#!/usr/bin/env python2
"""Convert the appropriate defects file from LSSTSim to test format

Example of usage:
setup afw
setup obs_lsstSim -j
./convertDefects.py $OBS_LSSTSIM_DIR/description/defects/rev_02272012

If you prefer not to setup obs_lsstSim you can specify the whole path
"""
import os.path
import sys
import time
import itertools

import numpy
import pyfits

import lsst.afw.geom as afwGeom

lsstDetectorName = "R:2,2 S:0,0"
lsstDefectsFileName = "defects2200.fits"
testDefectsPath = "defects1.fits"
testDetectorName = "S1"
testDetectorSerial = "0000011"

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

def convertLsstBBoxesToTestBBoxes(lsstBBoxList):
    """Read the obs_lsstSim defect list for R:2,2 S:0,0 and convert to a defect list for obs_test
    """
    testLL = afwGeom.Point2I(0, 1000)
    testOffset = afwGeom.Extent2I(0, -1000)
    testExtent = afwGeom.Extent2I(1018, 2000)
    testSubregion = afwGeom.Box2I(testLL, testExtent)
    testBBoxList = []
    for bbox in lsstBBoxList:
        bbox.clip(testSubregion)
        if bbox.isEmpty():
            continue
        bbox.shift(testOffset)
        testBBoxList.append(bbox)
#        bboxList.append(afwImage.DefectBase(bbox))
    return testBBoxList

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
    thdulist.writeto(testDefectsPath)

if len(sys.argv) != 2:
    print "To use: convertDefects path-to-lsstSims-defects"
    sys.exit(1)

lsstDefectsDir = sys.argv[1]
lsstDefectsPath = os.path.join(lsstDefectsDir, lsstDefectsFileName)
lsstBBoxList = getBBoxList(lsstDefectsPath, lsstDetectorName)
print "found %d LSST defects" % (len(lsstBBoxList),)
testBBoxList = convertLsstBBoxesToTestBBoxes(lsstBBoxList)
print "found %d test defects" % (len(testBBoxList),)
writeDefectsFile(testBBoxList, testDefectsPath, testDetectorSerial, testDetectorName)
print "wrote defects file %r" % (testDefectsPath,)

test2BBoxList = getBBoxList(testDefectsPath, testDetectorName)
assert len(testBBoxList) == len(test2BBoxList)
for boxA, boxB in itertools.izip(testBBoxList, test2BBoxList):
    assert boxA == boxB
print "verified that the file %r round trips correctly" % (testDefectsPath,)