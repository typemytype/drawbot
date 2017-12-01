from __future__ import print_function, division, absolute_import
import sys
import os
import unittest
import doctest
import importlib


testRoot = os.path.dirname(os.path.abspath(__file__))
if testRoot not in sys.path:
    sys.path.append(testRoot)

files = ["testScripts.py"]  # TODO automatic discovery based on naming convention
modulesWithDocTests = ["drawBot.misc"]  # TODO: doctest discovery

loader = unittest.TestLoader()
suite = unittest.TestSuite()
for fileName in files:
    moduleName, ext = os.path.splitext(fileName)
    suite.addTest(loader.loadTestsFromName(moduleName))

for moduleName in modulesWithDocTests:
    m = importlib.import_module(moduleName)
    suite.addTest(doctest.DocTestSuite(m))

import drawBot.misc as m
unittest.TextTestRunner(verbosity=1).run(suite)
# TODO: call sys.exit() with result code if we're not in DB
