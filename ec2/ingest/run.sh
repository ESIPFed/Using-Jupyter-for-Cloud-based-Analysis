#!/usr/bin/env bash

export DATA_DIRECTORY=/home/ndeploy/ingest/data/avhrr
export NINGESTER_CONFIG=/home/ndeploy/Using-Jupyter-for-Cloud-based-Analysis/ec2/ingest
export VERSION=1.0.0-SNAPSHOT
for g in `ls ${DATA_DIRECTORY} | egrep '^2016' | awk "{print $1}"`
do
  docker run -d --rm --name $(echo avhrr_$g | cut -d'-' -f 1) --network docker_nexus -v ${NINGESTER_CONFIG}/connections.yml:/config/connections.yml -v ${NINGESTER_CONFIG}/avhrr.yml:/config/avhrr.yml -v ${DATA_DIRECTORY}/${g}:/data/${g} sdap/ningester:${VERSION} docker,solr,cassandra
  sleep 30
done

export DATA_DIRECTORY=/home/ndeploy/ingest/data/trmm
for g in `ls ${DATA_DIRECTORY} | egrep '1998' | awk "{print $1}"`
do
  docker run -d --rm --name $(echo trmm_$g | cut -d'_' -f 6 | cut -d'.' -f 2) --network docker_nexus -v ${NINGESTER_CONFIG}/connections.yml:/config/connections.yml -v ${NINGESTER_CONFIG}/trmm.yml:/config/trmm.yml -v ${DATA_DIRECTORY}/${g}:/data/${g} sdap/ningester:${VERSION} docker,solr,cassandra
  sleep 15
done

export DATA_DIRECTORY=/home/ndeploy/ingest/data/rapid
for g in `ls ${DATA_DIRECTORY} | awk "{print $1}"`
do
  docker run -d --rm --name $(echo rapid_$g | cut -d'-' -f 1) --network docker_nexus -v ${NINGESTER_CONFIG}/connections.yml:/config/connections.yml -v ${NINGESTER_CONFIG}/rapidwswm.yml:/config/rapidwswm.yml -v ${DATA_DIRECTORY}/${g}:/data/${g} sdap/ningester:${VERSION} docker,solr,cassandra
done
