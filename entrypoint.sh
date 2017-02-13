#!/bin/bash -x

if [[ -z $OWNER ]]; then
  OWNER=lystable
fi

if [[ -z $REPO ]]; then
  echo 'You must set the REPO environment variable'
  exit 1
fi

# Clone the repo if it's not cloned
git clone https://github.com/$OWNER/$REPO.git /git/$REPO

# Run dennis command
cd /git/$REPO
/usr/local/bin/dennis $@
