#!/usr/bin/env bash

export DATA_DIR=/home/ndeploy/ingest/data/podaac-logs/
export MUDROD_CONFIG=/home/ndeploy/Using-Jupyter-for-Cloud-based-Analysis/ec2/sdap-search/config.properties
export SPARK_LOCAL_IP="127.0.0.1"

cd /home/ndeploy/sdap-search
./bin/mudrod-engine -f -dataDir ${DATA_DIR}/2018/01
