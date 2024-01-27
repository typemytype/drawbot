from packaging.version import Version
import platform

macOSVersion = Version(platform.mac_ver("0.0.0")[0])
