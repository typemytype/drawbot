import sys
import unittest
from pathlib import Path

sys.path.append(str((Path(__file__).parent.parent / "scripting").resolve()))

from generateDrawbotInit import INIT_PATH, generateInitCode
from imageObjectCodeExtractor import IMAGE_OBJECT_PATH, generateImageObjectCode


class AutomaticallyGeneratedCodeTester(unittest.TestCase):
    def test_init(self):
        initCode = generateInitCode()
        self.assertEqual(INIT_PATH.read_text(), initCode)

    def test_imageObject(self):
        imageObjectCode, _ = generateImageObjectCode()
        self.assertEqual(IMAGE_OBJECT_PATH.read_text(), imageObjectCode)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    sys.exit(unittest.main())
