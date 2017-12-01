from __future__ import print_function, division, absolute_import
import sys
import os
import unittest


testRoot = os.path.dirname(os.path.abspath(__file__))
if testRoot not in sys.path:
    sys.path.append(testRoot)

files = ["testScripts.py"]  # TODO automatic discovery based on naming convention

loader = unittest.TestLoader()
suite = unittest.TestSuite()
for fileName in files:
    moduleName, ext = os.path.splitext(fileName)
    suite.addTest(loader.loadTestsFromName(moduleName))

unittest.TextTestRunner(verbosity=1).run(suite)
