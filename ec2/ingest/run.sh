#!/usr/bin/env bash

export DATA_DIRECTORY=/home/ndeploy/ingest/data/avhrr
export NINGESTER_CONFIG=/home/ndeploy/Using-Jupyter-for-Cloud-based-Analysis/ec2/ingest
export VERSION=1.0.0-SNAPSHOT
for g in `ls ${DATA_DIRECTORY} | grep "2016" | awk "{print $1}"`
do
  docker run -d --rm --name $(echo avhrr_$g | cut -d'-' -f 1) --network docker_nexus -v ${NINGESTER_CONFIG}:/config/ -v ${DATA_DIRECTORY}/${g}:/data/${g} sdap/ningester:${VERSION} docker,solr,cassandra
  sleep 30
done
