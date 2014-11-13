#!/usr/bin/env python

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
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

import os
import unittest

import eups
import lsst.utils.tests as utilsTests
from lsst.obs.test import TestMapper
import lsst.afw.image as afwImage

class TestMapperTestCase(unittest.TestCase):
    """A test case for the test mapper."""

    def setUp(self):
        obsTestDir = eups.productDir("obs_test")
        if not obsTestDir:
            raise RuntimeError("obs_test is not setup")
        self.input = os.path.join(obsTestDir, "data", "input")
        self.output = self.input
        self.mapper = TestMapper(root=self.input)

    def tearDown(self):
        del self.mapper

    def testMapConfigData(self):
        dataId = dict(visit=1, ccd="0")
        loc = self.mapper.map_processCcd_config(dataId)
        self.assertEqual(loc.getPythonType(), "lsst.pipe.tasks.processCcd.ProcessCcdConfig")
        self.assertEqual(loc.getCppType(), "Config")
        self.assertEqual(loc.getStorageName(), "ConfigStorage")
        self.assertEqual(loc.getLocations(), [os.path.join(self.output,
            "config", "processCcd.py")])
        for k, v in dataId.iteritems():
            self.assertEqual(loc.getAdditionalData().get(k), v)

    def testMapMetadataData(self):
        dataId = dict(visit=1, ccd="0")
        loc = self.mapper.map_processCcd_metadata(dataId)
        self.assertEqual(loc.getPythonType(), "lsst.daf.base.PropertySet")
        self.assertEqual(loc.getCppType(), "PropertySet")
        self.assertEqual(loc.getStorageName(), "BoostStorage")
        self.assertEqual(loc.getLocations(), [os.path.join(self.output,
            "processCcd_metadata", "v1_fg.boost")])
        for k, v in dataId.iteritems():
            self.assertEqual(loc.getAdditionalData().get(k), v)

    def testKeys(self):
        self.assertEqual(set(self.mapper.keys()),
                set(['filter', 'patch', 'skyTile', 'tract', 'visit']))

    def testGetDatasetTypes(self):
        someKeys = set(['raw', 'processCcd_config', 'processCcd_metadata'])
        self.assertTrue(set(self.mapper.getDatasetTypes()).issuperset(someKeys))

    def testGetKeys(self):
        self.assertEqual(set(self.mapper.getKeys("raw", "skyTile")),
                set(["filter"]))
        self.assertEqual(set(self.mapper.getKeys("raw", "visit")),
                set(["filter", "visit"]))

    def testGetDefaultLevel(self):
        self.assertEqual(self.mapper.getDefaultLevel(), "ccd")

    def testGetDefaultSubLevel(self):
        self.assertEqual(self.mapper.getDefaultSubLevel("skyTile"), "ccd")
        self.assertEqual(self.mapper.getDefaultSubLevel("visit"), "ccd")
        self.assertEqual(self.mapper.getDefaultSubLevel("ccd"), "amp") # is this right, or should it be "ccd"?
        self.assertEqual(self.mapper.getDefaultSubLevel("amp"), None)

    def testMap(self):
        dataId = dict(visit=1, ccd="0")
        for loc in (
            self.mapper.map_raw(dataId),
            self.mapper.map("raw", dataId),
        ):
            self.assertEqual(loc.getPythonType(), "lsst.afw.image.DecoratedImageU")
            self.assertEqual(loc.getCppType(), "DecoratedImageU")
            self.assertEqual(loc.getStorageName(), "FitsStorage")
            locationList = loc.getLocations()
            self.assertEqual(len(locationList), 1)
            fileName = os.path.basename(locationList[0])
            self.assertEqual(fileName, "raw_v1_fg.fits.gz")
            for k, v in dataId.iteritems():
                self.assertEqual(loc.getAdditionalData().get(k), v)

    def testQueryMetadata(self):
        """Test expansion of incomplete information
        """
        tuples = self.mapper.queryMetadata("raw", "visit",
                ["visit", "filter", "ccd"],
                dict(visit=1))
        self.assertTrue((1, 'g', '0') in tuples)

    def testCanStandardize(self):
        self.assertEqual(self.mapper.canStandardize("raw"), True)
        self.assertEqual(self.mapper.canStandardize("camera"), True)
        self.assertEqual(self.mapper.canStandardize("processCcd_config"), False)
        self.assertEqual(self.mapper.canStandardize("processCcd_metadata"), False)

    def testStandardizeRaw(self):
        pathToRaw = os.path.join(self.input, "raw", "raw_v1_fg.fits.gz")
        rawImage = afwImage.DecoratedImageU(pathToRaw)
        dataId = dict(visit=1, ccd="0")
        stdImage = self.mapper.standardize("raw", rawImage, dataId)
        self.assertTrue(isinstance(stdImage, afwImage.ExposureU))

    def testValidate(self):
        for dataId in [
            dict(visit=1),
            dict(visit=25),
        ]:
            self.assertEqual(self.mapper.validate(dataId), dataId)
        for dataId in [
            dict(visit="not-an-int", ccd="0"), # visit must be an integer
        ]:
            self.assertRaises(Exception, self.mapper.validate, dataId)


def suite():
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(TestMapperTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)
    return unittest.TestSuite(suites)

def run(shouldExit=False):
    utilsTests.run(suite(), shouldExit)

if __name__ == '__main__':
    run(True)
