from distutils.version import StrictVersion
import platform

# It is safe to compare osVersion to strings, as StrictVersion casts strings
# to StrictVersion instances upon compare.
macOSVersion = StrictVersion(platform.mac_ver("0.0.0")[0])
