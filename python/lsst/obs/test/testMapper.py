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

import eups
import lsst.afw.image.utils as afwImageUtils
from lsst.daf.butlerUtils import CameraMapper
import lsst.pex.policy as pexPolicy
from lsst.daf.persistence import ButlerLocation
from .testCamera import TestCamera

__all__ = ["TestMapper"]

class TestMapper(CameraMapper):
    def __init__(self, inputPolicy=None, **kwargs):
        policyFile = pexPolicy.DefaultPolicyFile("obs_test", "TestMapper.paf", "policy")
        policy = pexPolicy.Policy(policyFile)

        self.doFootprints = False
        if inputPolicy is not None:
            for kw in inputPolicy.paramNames(True):
                if kw == "doFootprints":
                    self.doFootprints = True
                else:
                    kwargs[kw] = inputPolicy.get(kw)

        CameraMapper.__init__(self, policy, policyFile.getRepositoryPath(), **kwargs)
        self.filterIdMap = {
                'u': 0, 'g': 1, 'r': 2, 'i': 3, 'z': 4, 'y': 5, 'i2': 5}

        # The LSST Filters from L. Jones 04/07/10
        afwImageUtils.defineFilter('u', 364.59)
        afwImageUtils.defineFilter('g', 476.31)
        afwImageUtils.defineFilter('r', 619.42)
        afwImageUtils.defineFilter('i', 752.06)
        afwImageUtils.defineFilter('z', 866.85)
        afwImageUtils.defineFilter('y', 971.68, alias=['y4']) # official y filter

        self.camera = TestCamera()

    def _extractDetectorName(self, dataId):
        return dataId["ccd"]

    def _defectLookup(self, dataId):
        """Find the defects for a given CCD.
        @param dataId (dict) Dataset identifier
        @return (string) path to the defects file or None if not available
        """
        if dataId.get("ccd") != "S0":
            return None

        obsTestDir = eups.packageDir("obs_test")
        if obsTestDir is None:
            raise RuntimeError("obs_test must be setup")

        return os.path.join(obsTestDir, "data", "inputs", "defects", "defects0.fits")

    def map_camera(self, dataId, write=False):
        """Map a camera dataset."""
        return ButlerLocation()

    def std_camera(self, item, dataId):
        """Standardize a camera dataset by converting it to a camera object.

        @param[in] item: camera info (an lsst.afw.cameraGeom.CameraConfig)
        @param[in] dataId: data ID dict
        """
        return self.camera