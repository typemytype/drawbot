#!/bin/bash

set -e
set -x

python3 -m virtualenv .venv-build/

source .venv-build/bin/activate

python3 -m pip install -r ./requirements.txt
python3 -m pip install -r ./test-requirements.txt

# install dev certificate
export CERTIFICATE_P12=Certificate.p12
echo $CERTIFICATE_OSX_P12 | base64 --decode > $CERTIFICATE_P12
export KEYCHAIN=build.keychain
security create-keychain -p mysecretpassword $KEYCHAIN
security default-keychain -s $KEYCHAIN
security unlock-keychain -p mysecretpassword $KEYCHAIN
security import $CERTIFICATE_P12 -k $KEYCHAIN -P $CERTIFICATE_PASSWORD -T /usr/bin/codesign
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k mysecretpassword $KEYCHAIN

# build the app
python3 ./setupApp.py py2app --dmg --codesign "Frederik Berlaen"
