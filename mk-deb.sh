#!/bin/sh

if [ -z "$1" ] ; then
	echo "Missing GPG signing key"
	exit 1
fi

DATESTAMP=$(date +%Y%m%d%H%M)
dch -b -M -v ${DATESTAMP}~truenas+1 --force-distribution --distribution bullseye-truenas-unstable "Auto Update from Jenkins CI"

dpkg-buildpackage --sign-key=${1} -S -sa
