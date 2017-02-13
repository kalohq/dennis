#!/bin/bash -x
#
# Copy SSH to ~/.ssh/id_rsa
#
mkdir -p ~/.ssh
cp /host.ssh/id_rsa ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

# Run dennis command
/usr/local/bin/dennis $@
