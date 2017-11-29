from __future__ import print_function, division, absolute_import
import sys
import unittest

import testScripts

def dummy(*args, **kwargs):
    pass

e = sys.exit
sys.exit = dummy

tests = [testScripts]

for test in tests:
    print(test.__name__)
    unittest.main(module=test)

sys.exit = e