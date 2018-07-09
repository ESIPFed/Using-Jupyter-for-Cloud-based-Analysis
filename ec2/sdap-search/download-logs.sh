#!/usr/bin/env bash

mkdir -p /home/ndeploy/ingest/data/podaac-logs
cd /home/ndeploy/ingest/data/podaac-logs
wget -m -np -nH --cut-dirs=4 ftp://podaac.jpl.nasa.gov/misc/outgoing/cjf/mudrod/2018
