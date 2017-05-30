#!/bin/bash -e

if [[ -z $OWNER ]]; then
  OWNER=kalohq
fi

if [[ -z $REPO ]]; then
  echo 'You must set the REPO environment variable'
  exit 1
fi

if [[ ! -d /git/$OWNER/$REPO ]]; then
  # Clone the repo if it's not cloned
  echo "Repo not found, cloning now..."
  git clone -b develop https://github.com/$OWNER/$REPO.git /git/$OWNER/$REPO > /dev/null
fi

cd /git/$OWNER/$REPO

if [[ -n $1 && ! $(echo "$@" | grep help) ]]; then
  # Add credentials to git cache
  echo "Adding your credentials to Git memory cache..."
  git checkout develop
  git pull > /dev/null
fi

# Run dennis command
/usr/local/bin/dennis $@
