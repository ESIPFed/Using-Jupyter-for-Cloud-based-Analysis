#!/usr/bin/env bash

cd /home/ndeploy/Using-Jupyter-for-Cloud-based-Analysis/docker
docker-compose up -d cassandra1

sleep 15

docker exec -it cassandra1 cqlsh -e CREATE KEYSPACE IF NOT EXISTS nexustiles WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };
docker exec -it cassandra1 cqlsh -e CREATE TABLE IF NOT EXISTS nexustiles.sea_surface_temp (tile_id uuid PRIMARY KEY, tile_blob blob);


docker-compose up -d

sleep 30

docker exec -it solr1 curl -g 'http://localhost:8983/solr/nexustiles/select?q=dataset_s:AVHRR_OI_L4_GHRSST_NCEI&rows=5000' > /dev/null
