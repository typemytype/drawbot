import sys
import os
import unittest
import doctest
import importlib
import glob


testRootDir = os.path.dirname(os.path.abspath(__file__))
if testRootDir not in sys.path:
    sys.path.append(testRootDir)

testModules = glob.glob(os.path.join(testRootDir, "test*.py"))
modulesWithDocTests = ["drawBot.misc", "testSupport"]  # TODO: doctest discovery

loader = unittest.TestLoader()
suite = unittest.TestSuite()
for path in testModules:
    moduleName, ext = os.path.splitext(os.path.basename(path))
    suite.addTest(loader.loadTestsFromName(moduleName))

for moduleName in modulesWithDocTests:
    m = importlib.import_module(moduleName)
    suite.addTest(doctest.DocTestSuite(m))

unittest.TextTestRunner(verbosity=1).run(suite)
# TODO: call sys.exit() with result code if we're not in DB
