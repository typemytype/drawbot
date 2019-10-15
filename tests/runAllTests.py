import doctest
import glob
import importlib
import os
import sys
import unittest


inDrawBotApp = "drawBot.ui.codeEditor" in sys.modules

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

result = unittest.TextTestRunner(verbosity=1).run(suite)
if not inDrawBotApp and not result.wasSuccessful():
    sys.exit(1)
