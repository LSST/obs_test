"""lsstSim-specific overrides for the processCcd task
"""
root.isr.doDark=False
root.isr.doFringe=False
root.calibrate.doAstrometry=False # no astrometry_net data?
root.calibrate.doPhotoCal=False # forbidden if doAstrometry false