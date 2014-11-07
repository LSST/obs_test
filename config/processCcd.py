"""lsstSim-specific overrides for the processCcd task
"""
root.isr.doDark=False
root.isr.doFringe=False
root.calibrate.doAstrometry=False # no astrometry_net data?
root.calibrate.doPhotoCal=False # forbidden if doAstrometry false
root.calibrate.repair.doCosmicRay=False # too many CRs with default values; figure out what to tweak to allow CR rejection