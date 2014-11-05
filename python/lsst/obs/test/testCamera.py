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
import numpy
from lsst.afw.geom import Angle, arcseconds, Box2I, Extent2I, Point2I, RadialXYTransform, InvertedXYTransform
from lsst.afw.table import AmpInfoCatalog, AmpInfoTable, LL, LR, UL, UR
from lsst.afw.cameraGeom import Camera, DetectorConfig, FOCAL_PLANE, PUPIL, CameraTransformMap
from lsst.afw.cameraGeom.cameraFactory import makeDetector

class TestCamera(Camera):
    """A simple test Camera

    There is one ccd with name "0"
    It has four amplifiers with names "00", "01", "10", and "11"

    The camera is modeled after a small portion of the LSST sim Summer 2012 camera:
    a single detector with four amplifiers, consisting of
    raft 2,2 sensor 0,0, half of channels 0,0 0,1 1,0 and 1,1 (the half closest to the Y centerline)

    Note that the Summer 2012 camera has one very weird feature: the bias region
    (rawHOverscanBbox) is actually a prescan (appears before the data pixels).

    Standard keys are:
    amp: amplifier number: one of 00, 01, 10, 11
    ccd: ccd number: always 0
    visit: exposure number; test data includes one exposure with visit=1
    """
    def __init__(self):
        """Construct a TestCamera
        """
        plateScale = Angle(20, arcseconds) # plate scale, in angle on sky/mm
        radialDistortion = 0.925 # radial distortion in mm/rad^2
        radialCoeff = numpy.array((0.0, 1.0, 0.0, radialDistortion)) / plateScale.asRadians()
        focalPlaneToPupil = RadialXYTransform(radialCoeff)
        pupilToFocalPlane = InvertedXYTransform(focalPlaneToPupil)
        cameraTransformMap = CameraTransformMap(FOCAL_PLANE, {PUPIL: pupilToFocalPlane})
        detectorList = self._makeDetectorList(pupilToFocalPlane, plateScale)
        Camera.__init__(self, "test", detectorList, cameraTransformMap)

    def _makeDetectorList(self, focalPlaneToPupil, plateScale):
        """Make a list of detectors

        @param[in] focalPlaneToPupil  lsst.afw.geom.XYTransform from FOCAL_PLANE to PUPIL coordinates
        @param[in] plateScale  plate scale, in angle on sky/mm
        @return a list of detectors (lsst.afw.cameraGeom.Detector)
        """
        detectorList = []
        detectorConfigList = self._makeDetectorConfigList()
        for detectorConfig in detectorConfigList:
            ampInfoCatalog = self._makeAmpInfoCatalog()
            detector = makeDetector(detectorConfig, ampInfoCatalog, focalPlaneToPupil, plateScale.asArcseconds())
            detectorList.append(detector)
        return detectorList

    def _makeDetectorConfigList(self):
        """Make a list of detector configs

        @return a list of detector configs (lsst.afw.cameraGeom.DetectorConfig)
        """
        # this camera has one detector that corresponds to a subregion of lsstSim detector R:2,2 S:0,0
        # with lower left corner 0, 1000 and dimensions 1018 x 2000
        # i.e. half of each of the following channels: 0,0, 0,1, 1,0 and 1,1
        detector0Config = DetectorConfig()
        detector0Config.name = '0'
        detector0Config.id = 0
        detector0Config.serial = '0000011'
        detector0Config.detectorType = 0
        detector0Config.bbox_x0 = 0
        detector0Config.bbox_x1 = 1017
        detector0Config.bbox_y0 = 0
        detector0Config.bbox_y1 = 1999
        detector0Config.pixelSize_x = 0.01
        detector0Config.pixelSize_y = 0.01
        detector0Config.transformDict.nativeSys = 'Pixels'
        detector0Config.transformDict.transforms = None
        detector0Config.refpos_x = 2035.5
        detector0Config.refpos_y = 999.5
        detector0Config.offset_x = -42.26073
        detector0Config.offset_y = -42.21914
        detector0Config.transposeDetector = False
        detector0Config.pitchDeg = 0.0
        detector0Config.yawDeg = 90.0
        detector0Config.rollDeg = 0.0
        return [detector0Config]

    def _makeAmpInfoCatalog(self):
        """Construct an amplifier info catalog

        The LSSTSim S12 amplifiers are unusual in that they start with 4 pixels
        of usable bias region (which is used to set rawHOverscanBbox, despite the name),
        followed by the data. There is no other underscan or overscan.
        """
        # dict of amp-specific data x0Assembled, y0Assembled, x0Raw, y0Raw, flipX, flipY
        ampDataDict = {
            "C00": (  0,    0,   0,    0, False, False),
            "C10": (509,    0, 513,    0, False, False),
            "C01": (0,   1000,   0, 1000,  True,  True),
            "C11": (509, 1000, 513, 1000,  True,  True),
        }
        xDataExtent = 509 # trimmed
        yDataExtent = 1000
        xBiasExtent = 4
        xRawExtent = xDataExtent + xBiasExtent
        yRawExtent = yDataExtent
        gain = 1.7 # amplifier gain in e-/ADU
        # bias = 1000 # amplifier bias
        readNoise = 7.0 # amplifier read noise, in e-
        # darkCurrent = 0.02 # amplifier dark current
        linearityType = "PROPORTIONAL"
        linearityThreshold = 0
        linearityMax = 65535
        linearityCoeffs = [linearityThreshold, linearityMax]

        schema = AmpInfoTable.makeMinimalSchema()

        linThreshKey = schema.addField('linearityThreshold', type=float)
        linMaxKey = schema.addField('linearityMaximum', type=float)
        linUnitsKey = schema.addField('linearityUnits', type=str, size=9)
        self.ampInfoDict = {}
        ampCatalog = AmpInfoCatalog(schema)
        for ampName, ampData in ampDataDict.iteritems():
            x0Assembled, y0Assembled, x0Raw, y0Raw, flipX, flipY = ampData
            record = ampCatalog.addNew()
            bbox = Box2I(
                Point2I(x0Assembled, y0Assembled),
                Extent2I(xDataExtent, yDataExtent),
            )

            # for raw bounding boxes, start with them relative to 0,0
            # flip as needed, then offset by x0Raw, y0Raw
            rawBbox = Box2I(
                Point2I(0, 0),
                Extent2I(xRawExtent, yRawExtent),
            )
            rawDataBbox = Box2I(
                Point2I(xBiasExtent, 0),
                Extent2I(xDataExtent, yDataExtent),
            )
            rawHOverscanBbox = Box2I(
                Point2I(0, 0),
                Extent2I(xBiasExtent, yRawExtent),
            )
            rawVOverscanBbox = Box2I()
            rawPrescanBbox = Box2I() # usable horizontal prescan (none)
            if flipX:
                rawBbox.flipLR(xRawExtent)
                rawDataBbox.flipLR(xRawExtent)
                rawHOverscanBbox.flipLR(xRawExtent)
                rawVOverscanBbox.flipLR(xRawExtent)
                rawPrescanBbox.flipLR(xRawExtent)
            if flipY:
                rawBbox.flipTB(yRawExtent)
                rawDataBbox.flipTB(yRawExtent)
                rawHOverscanBbox.flipTB(yRawExtent)
                rawVOverscanBbox.flipTB(yRawExtent)
                rawPrescanBbox.flipTB(yRawExtent)
            readCorner = {
                (False, False): LL,
                (True, False): LR,
                (False, True): UL,
                (True, True): UR,
            }[(bool(flipX), bool(flipY))]
            xy0RawOffset = Extent2I(x0Raw, y0Raw)
            rawBbox.shift(xy0RawOffset)
            rawDataBbox.shift(xy0RawOffset)
            rawHOverscanBbox.shift(xy0RawOffset)
            rawVOverscanBbox.shift(xy0RawOffset)
            rawPrescanBbox.shift(xy0RawOffset)
            x0Raw = 0
            y0Raw = 0

            record.setBBox(bbox)
            record.setRawXYOffset(xy0RawOffset)
            record.setName(ampName)
            record.setReadoutCorner(readCorner)
            record.setGain(gain)
            record.setReadNoise(readNoise)
            record.setSaturation(linearityMax)
            record.setLinearityCoeffs([float(val) for val in linearityCoeffs])
            record.setLinearityType(linearityType)
            record.setHasRawInfo(True)
            record.setRawFlipX(flipX)
            record.setRawFlipY(flipY)
            record.setRawBBox(rawBbox)
            record.setRawDataBBox(rawDataBbox)
            record.setRawHorizontalOverscanBBox(rawHOverscanBbox)
            record.setRawVerticalOverscanBBox(rawVOverscanBbox)
            record.setRawPrescanBBox(rawPrescanBbox)
            record.set(linThreshKey, float(linearityThreshold))
            record.set(linMaxKey, float(linearityMax))
            record.set(linUnitsKey, "DN")
        return ampCatalog
