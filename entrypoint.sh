#!/bin/bash -e

if [[ -z $OWNER ]]; then
  OWNER=lystable
fi

if [[ -z $REPO ]]; then
  echo 'You must set the REPO environment variable'
  exit 1
fi

if [[ ! -d /git/$REPO ]]; then
  # Clone the repo if it's not cloned
  echo "Repo not found, cloning now..."
  git clone -b develop https://github.com/$OWNER/$REPO.git /git/$REPO > /dev/null
fi

cd /git/$REPO

# Add credentials to git cache
echo "Adding credentials to Git cache..."
git push -u origin develop

# Run dennis command
/usr/local/bin/dennis $@
