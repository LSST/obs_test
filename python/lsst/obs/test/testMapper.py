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
__all__ = ["TestMapper", "MapperForTestCalexpMetadataObjects"]

import os
import warnings

import lsst.utils
import lsst.afw.image.utils as afwImageUtils
import lsst.daf.persistence as dafPersist
from lsst.obs.base import CameraMapper
from .testCamera import TestCamera
from .makeTestRawVisitInfo import MakeTestRawVisitInfo


class TestMapper(CameraMapper):
    """Camera mapper for the Test camera.
    """
    packageName = 'obs_test'

    MakeRawVisitInfoClass = MakeTestRawVisitInfo

    def __init__(self, inputPolicy=None, **kwargs):
        policyFilePath = dafPersist.Policy.defaultPolicyFile(self.packageName, "testMapper.yaml", "policy")
        policy = dafPersist.Policy(policyFilePath)

        self.doFootprints = False
        if inputPolicy is not None:
            for kw in inputPolicy.paramNames(True):
                if kw == "doFootprints":
                    self.doFootprints = True
                else:
                    kwargs[kw] = inputPolicy.get(kw)

        CameraMapper.__init__(self, policy, policyFilePath, **kwargs)
        self.filterIdMap = {
            'u': 0, 'g': 1, 'r': 2, 'i': 3, 'z': 4, 'y': 5, 'i2': 5}

        with warnings.catch_warnings():
            # surpress Filter warnings; we already know this is deprecated
            warnings.simplefilter('ignore', category=FutureWarning)

            # The LSST Filters from L. Jones 04/07/10
            afwImageUtils.defineFilter('u', 364.59)
            afwImageUtils.defineFilter('g', 476.31)
            afwImageUtils.defineFilter('r', 619.42)
            afwImageUtils.defineFilter('i', 752.06)
            afwImageUtils.defineFilter('z', 866.85)
            afwImageUtils.defineFilter('y', 971.68, alias=['y4'])  # official y filter

    def _extractDetectorName(self, dataId):
        return "0"

    def _defectLookup(self, dataId):
        """Find the defects for a given CCD.

        Parameters
        ----------
        dataId : `dict`
            Dataset identifier

        Returns
        -------
        result : `str`
            Path to the defects file.

        Raises
        ------
        RuntimeError
            If ``obs_test`` is not setup.
        """
        obsTestDir = lsst.utils.getPackageDir('obs_test')

        return os.path.join(obsTestDir, "data", "input", "defects", "defects.fits")

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        Parameters
        ----------
        dataId : `dict`
            Data identifier with visit
        """
        visit = dataId['visit']
        return int(visit)

    def bypass_ccdExposureId(self, datasetType, pythonType, location, dataId):
        return self._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        return 41

    def validate(self, dataId):
        visit = dataId.get("visit")
        if visit is not None and not isinstance(visit, int):
            dataId["visit"] = int(visit)
        return dataId

    def _setCcdExposureId(self, propertyList, dataId):
        propertyList.set("Computed_ccdExposureId", self._computeCcdExposureId(dataId))
        return propertyList

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera describing the camera geometry.

        Returns
        -------
        testCamera : `TestCamera`
            Test camera.
        """
        return TestCamera()


class MapperForTestCalexpMetadataObjects(lsst.obs.base.CameraMapper):
    """Minimal mapper for testing calexp composite access, e.g. calexp_wcs.

    Used by test_metadataObjectAccess.py.
    """
    packageName = "obs_test"

    def __init__(self, root, parentRegistry=None, repositoryCfg=None):
        policyFilePath = dafPersist.Policy.defaultPolicyFile(
            self.packageName, "testCalexpMetadataObjects.yaml", "policy")
        policy = dafPersist.Policy(policyFilePath)
        super(MapperForTestCalexpMetadataObjects, self).__init__(
            policy, repositoryDir=root, root=root, parentRegistry=None, repositoryCfg=None)
        self.filterIdMap = {
            'u': 0, 'g': 1, 'r': 2, 'i': 3, 'z': 4, 'y': 5, 'i2': 5}

        with warnings.catch_warnings():
            # surpress Filter warnings; we already know this is deprecated
            warnings.simplefilter('ignore', category=FutureWarning)

            # The LSST Filters from L. Jones 04/07/10
            afwImageUtils.defineFilter('u', 364.59)
            afwImageUtils.defineFilter('g', 476.31)
            afwImageUtils.defineFilter('r', 619.42)
            afwImageUtils.defineFilter('i', 752.06)
            afwImageUtils.defineFilter('z', 866.85)
            afwImageUtils.defineFilter('y', 971.68, alias=['y4'])  # official y filter

    def _makeCamera(self, policy, repositoryDir):
        """Normally this makes a camera. For composite testing, we don't need a camera.
        """
        return TestCamera()

    def _extractDetectorName(self, dataId):
        """Normally this extracts the detector (CCD) name from the dataset
        identifier. The name in question is the detector name used by
        lsst.afw.cameraGeom.

        We don't need anything meaninful here, so just override so as not to
        throw (in the base class impl)
        """
        return "0"
