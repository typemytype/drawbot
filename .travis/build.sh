#!/bin/bash

set -e
set -x

source .venv/bin/activate

# install dev certificate
# export CERTIFICATE_P12=Certificate.p12
# echo $CERTIFICATE_OSX_P12 | base64 — decode > $CERTIFICATE_P12
# export KEYCHAIN=build.keychain
# security create-keychain -p mysecretpassword $KEYCHAIN
# security default-keychain -s $KEYCHAIN;
# security unlock-keychain -p mysecretpassword $KEYCHAIN;
# security import $CERTIFICATE_P12 -k $KEYCHAIN -P $CERTIFICATE_PASSWORD -T /usr/bin/codesign;

# make sure drawBot is not installed as module
# py2app gets confused when building the app inside the package
python3 -m pip uninstall --yes drawBot
# build the app
python3 ./setupApp.py py2app --dmg --codesign "Frederik Berlaen"
