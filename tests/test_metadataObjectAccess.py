# This file is part of obs_test.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import math
import os
import unittest

import lsst.afw.image
from lsst.afw.geom import SkyWcs
import lsst.daf.persistence as dafPersist
import lsst.utils.tests
from lsst.utils import getPackageDir

obsTestDir = getPackageDir('obs_test')


class TestCalexpMetadataObjects(lsst.utils.tests.TestCase):
    """Test getting metadata objects from a calexp."""
    def setUp(self):
        self.input = os.path.join(obsTestDir,
                                  'data',
                                  'calexpMetadataObjectsTest')

    def nanSafeAssertEqual(self, val1, val2):
        try:
            self.assertEqual(val1, val2)
        except AssertionError as err:
            if math.isnan(val1) and math.isnan(val2):
                pass
            else:
                raise err

    def testNanSafeAssertEqual(self):
        val1 = float('nan')
        val2 = float(123.45)
        with self.assertRaises(AssertionError):
            self.nanSafeAssertEqual(val1, val2)
        val1 = float(123.44)
        val2 = float(123.45)
        with self.assertRaises(AssertionError):
            self.nanSafeAssertEqual(val1, val2)
        # should not raise:
        val1 = float('nan')
        val2 = float('nan')
        self.nanSafeAssertEqual(val1, val2)
        val1 = float(123.45)
        val2 = float(123.45)
        self.nanSafeAssertEqual(val1, val2)

    def test(self):
        """Get the wcs, photoCalib, and visitInfo from a calexp dataset."""
        butler = dafPersist.Butler(inputs=self.input)
        wcs = butler.get('calexp_wcs', immediate=True)
        photoCalib = butler.get('calexp_photoCalib', immediate=True)
        visitInfo = butler.get('calexp_visitInfo', immediate=True)
        filt = butler.get('calexp_filter', immediate=True)
        calexp = butler.get('calexp', immediate=True)
        self.assertIsInstance(calexp, lsst.afw.image.ExposureF)

        self.assertIsInstance(wcs, SkyWcs)
        self.assertWcsAlmostEqualOverBBox(wcs, calexp.getWcs(), calexp.getBBox())

        self.assertIsInstance(photoCalib, lsst.afw.image.PhotoCalib)
        self.assertEqual(photoCalib, calexp.getPhotoCalib())

        self.assertIsInstance(visitInfo, lsst.afw.image.VisitInfo)
        self.assertIsInstance(filt, lsst.afw.image.Filter)

        self.assertEqual(visitInfo, calexp.info.getVisitInfo())


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
