#!/usr/bin/env bash

export DATA_DIR=/home/ndeploy/ingest/data/podaac-logs/
export MUDROD_CONFIG=/home/ndeploy/Using-Jupyter-for-Cloud-based-Analysis/ec2/sdap-search/mudrod-engine.config.xml
export SPARK_LOCAL_IP="127.0.0.1"

mudrod-engine -f -dataDir /usr/local/sdeploy/mudrod-ingest/ftp-mirror/2016/12/
