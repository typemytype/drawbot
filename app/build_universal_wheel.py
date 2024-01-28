import argparse
import json
import os
import pathlib
import sys

from urllib.request import urlopen
from tempfile import TemporaryDirectory
from delocate.fuse import fuse_wheels


def find_wheels(package, version=None, python_version=None):
    response = urlopen(f"https://pypi.org/pypi/{package}/json")
    data = json.load(response)

    if version is None:
        version = data["info"]["version"]

    if python_version is None:
        python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"

    releases = data["releases"][version]

    releases = [rel for rel in releases if rel["python_version"] == python_version]
    wheels_urls = []
    for rel in releases:
        filename, ext = os.path.splitext(rel["filename"])
        platform = filename.split("-")[-1]
        if platform.startswith("macosx"):
            wheels_urls.append(rel["url"])
    return wheels_urls, version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("--wheels-dir", default="build/universal_wheels")

    args = parser.parse_args()

    wheels_dir = pathlib.Path(args.wheels_dir).resolve()
    wheels_dir.mkdir(exist_ok=True, parents=True)

    package = args.package
    version = None
    if "==" in package:
        package, version = package.split("==")

    wheels_urls, version = find_wheels(package, version)
    assert len(wheels_urls) == 2

    with TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)

        wheel_paths = []
        for url in wheels_urls:
            filename = url.rsplit("/", 1)[-1]
            wheel_path = tmpdir / filename
            response = urlopen(url)
            with open(wheel_path, "wb") as f:
                f.write(response.read())
            wheel_paths.append(wheel_path)

        wheel_names = [url.split("/")[-1].rsplit(".", 1)[0] for url in wheels_urls]
        wheel_names.sort()

        assert any("x86" in name for name in wheel_names)
        assert any("arm64" in name for name in wheel_names)

        wheel_base, platform = wheel_names[-1].rsplit("-", 1)
        platform_base, arch = platform.rsplit("_", 1)

        universal_wheel_path = (
            wheels_dir / f"{wheel_base}-{platform_base}_universal2.whl"
        )
        fuse_wheels(wheel_paths[0], wheel_paths[1], universal_wheel_path)
        print(universal_wheel_path)


if __name__ == "__main__":
    main()
