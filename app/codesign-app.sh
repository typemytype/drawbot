#!/bin/bash

set -e # abort on errors

DEV_ID=$1
APP_PATH=$2
ENTITLEMENTS=$3

echo "start codesign..."

# Explicitly codesign all embedded *.so and *.dylib files
find "$APP_PATH" -iname '*.so' -or -iname '*.dylib' |
    while read libfile; do
          codesign --sign "$DEV_ID" \
                   --entitlements "$ENTITLEMENTS" \
                   --deep "${libfile}" \
                   --force \
                   --options runtime;
    done;


codesign --sign "$DEV_ID" --entitlements "$ENTITLEMENTS" --deep "${APP_PATH}/Contents/Resources/ffmpeg" --force --options runtime
codesign --sign "$DEV_ID" --entitlements "$ENTITLEMENTS" --deep "${APP_PATH}/Contents/Resources/gifsicle" --force --options runtime
codesign --sign "$DEV_ID" --entitlements "$ENTITLEMENTS" --deep "${APP_PATH}/Contents/Resources/mkbitmap" --force --options runtime
codesign --sign "$DEV_ID" --entitlements "$ENTITLEMENTS" --deep "${APP_PATH}/Contents/Resources/potrace" --force --options runtime


# Codesign the app
codesign --sign "$DEV_ID" \
         --entitlements "$ENTITLEMENTS" \
         --deep "$APP_PATH" \
         --force \
         --options runtime;

echo "verify with codesign"
# verify
codesign --verify --verbose=4 "$APP_PATH"

echo "verify with spctl"
# verify with spctl
 spctl --verbose=4 --raw --assess --type execute "$APP_PATH"

echo "Done codesign"