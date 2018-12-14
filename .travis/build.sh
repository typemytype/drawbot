#!/bin/bash

set -e
set -x

python3 -m virtualenv .venv-build/

source .venv-build/bin/activate

python3 -m pip install -r ./requirements.txt
python3 -m pip install -r ./test-requirements.txt

# install dev certificate
# https://github.com/danielbuechele/atemOSC/blob/864f95931a7f6ae35a81542b2ca7157124166693/.travis/sign.sh
# https://www.jviotti.com/2016/03/16/how-to-code-sign-os-x-electron-apps-in-travis-ci.html
export CERTIFICATE_P12=Certificate.p12
echo $CERTIFICATE_OSX_P12 | base64 --decode > $CERTIFICATE_P12
export KEYCHAIN=build.keychain
security create-keychain -p mysecretpassword $KEYCHAIN
security default-keychain -s $KEYCHAIN
security unlock-keychain -p mysecretpassword $KEYCHAIN
security import $CERTIFICATE_P12 -k $KEYCHAIN -P $CERTIFICATE_PASSWORD -T $(which codesign)
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k mysecretpassword $KEYCHAIN

# empty dir and build folder
rm -rf ./build
rm -rf ./dist

# build the app
python3 ./setupApp.py py2app --dmg --codesign "Frederik Berlaen"
