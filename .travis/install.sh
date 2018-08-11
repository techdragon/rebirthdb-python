#!/bin/sh

set -e
set -u

export DISTRIB_CODENAME=$(lsb_release -sc)

#The debian package gpg key setup doesnt appear to be fully set up yet. So this set of commands is just commented out for now until we can switch over.
#echo "deb https://dl.bintray.com/rebirthdb/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rebirthdb.list
#wget -qO- https://dl.bintray.com/rebirthdb/keys/pubkey.gpg | sudo apt-key add -

echo "deb https://dl.bintray.com/floydkots/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rebirthdb.list
wget -qO- https://dl.bintray.com/floydkots/keys/pubkey.gpg | sudo apt-key add -

# Normal apt-get update seems fragile on travis-ci so we try to ensure it completes.
sudo apt-get update --option Acquire::Retries=100 --option Acquire::http::Timeout="300"
#sudo apt-get update -o Dir::Etc::sourcelist="sources.list.d/rebirthdb.list" -o Dir::Etc::sourceparts="-" -o APT::Get::List-Cleanup="0"

sudo apt-get --allow-unauthenticated install rebirthdb --option Acquire::Retries=100 --option Acquire::http::Timeout="300"

pip install tox
pip install tox-travis
pip install tox-pyenv
