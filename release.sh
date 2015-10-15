#!/bin/bash
if [[ -z $1 || -z $2 ]] ; then
  echo "Missing arguments: <last version> <new version>"
  exit 1
fi

LAST_VERSION=$(echo $1 | sed 's/v//g')
NEW_VERSION=$(echo $2 | sed 's/v//g')

VERSION_FILE=./VERSION

# Bump the version
sed -i "s/$LAST_VERSION/$NEW_VERSION/g" $VERSION_FILE

# Check the version was set correctly
grep $NEW_VERSION $VERSION_FILE > /dev/null
