import sys
import os
import unittest

from testSupport import StdOutCollector, TempFolder, TempFile
from drawBot.drawBotPackage import DrawBotPackage


class PackageTest(unittest.TestCase):

    def test_buildPackage(self):
        package = DrawBotPackage()
        package.info.name = "demo"
        package.info.developer = "drawbot"
        package.info.developerURL = "http://www.drawbot.com"
        package.info.requiresVersion = "3.0"
        package.info.mainScript = "main.py"

        succes, _ = package.buildPackage("does/not/exists", "does/not/exists")
        self.assertFalse(succes)

        with TempFolder(suffix=".drawbot") as tempPath:
            succes, _ = package.buildPackage(tempPath.path, "does/not/exists")
            self.assertFalse(succes)

            with TempFolder() as tempScriptRoot:
                succes, _ = package.buildPackage(tempPath.path, tempScriptRoot.path)
                self.assertFalse(succes)

                with TempFile(suffix=".py", dir=tempScriptRoot.path) as tmp:
                    with open(tmp.path, "w") as f:
                        f.write("print('hello world'")
                    package.info.mainScript = os.path.basename(tmp.path)
                    succes, _ = package.buildPackage(tempPath.path, tempScriptRoot.path)
                    self.assertTrue(succes)

    def test_readPackage(self):
        path = os.path.join(os.path.dirname(__file__), "package/empty.drawbot")

        package = DrawBotPackage(path)
        self.assertEqual(package.info.asDict(), {})
        self.assertEqual(package.info.version, "0.0")
        self.assertEqual(package.info.developer, "")
        self.assertEqual(package.info.developerURL, "")
        self.assertEqual(package.info.requiresVersion, "0.0")
        self.assertEqual(package.info.mainScript, "main.py")

        path = os.path.join(os.path.dirname(__file__), "package/simple.drawbot")

        package = DrawBotPackage(path)
        self.assertEqual(package.info.version, "1.0")
        self.assertEqual(package.info.developer, "drawbot")
        self.assertEqual(package.info.developerURL, "http://www.drawbot.com")
        self.assertEqual(package.info.requiresVersion, "3.0")
        self.assertEqual(package.info.mainScript, "main.py")

    def test_runPackages(self):
        path = os.path.join(os.path.dirname(__file__), "package/empty.drawbot")

        package = DrawBotPackage(path)
        with StdOutCollector() as output:
            succes, _ = package.run()

        self.assertEqual(output.lines(), ['hello world'])

    def test_missingMainScript(self):
        path = os.path.join(os.path.dirname(__file__), "package/missingMainScript.drawbot")
        package = DrawBotPackage(path)
        succes, message = package.run()
        self.assertEqual(succes, False)
        self.assertTrue(message.startswith("Cannot find"))


if __name__ == '__main__':
    sys.exit(unittest.main())
