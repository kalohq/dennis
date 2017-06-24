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

if [[ -n $1 && ! $(echo "$@" | grep help) && ! $(echo "$@" | grep '\-h') ]]; then
  # Add credentials to git cache if they were given on command line
  args=("$@")
  for i in "${!args[@]}"
  do
      if [ "${args[i]}" = "--user" ]; then
          user=${args[i+1]}
      elif [ "${args[i]}" = "--token" ]; then
          token=${args[i+1]}
      fi
  done

  git checkout develop
  if [[ -n $user && -n $token ]]; then
      # Pull with credentials in url to add them to credential cache
      repo_url=$(git config --get remote.origin.url)
      repo_url="https://${user}:${token}@${repo_url#https://}"
      git pull $repo_url > /dev/null

  else
      # Resort to prompting user for credentials
      git pull > /dev/null
  fi
fi

# Run dennis command
/usr/local/bin/dennis $@
