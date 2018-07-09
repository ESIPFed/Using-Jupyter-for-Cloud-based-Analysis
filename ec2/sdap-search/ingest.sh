#!/usr/bin/env bash


MUDROD_CONFIG=/usr/local/sdeploy/mudrod-engine.config.xml SPARK_LOCAL_IP="127.0.0.1" mudrod-engine -f -dataDir /usr/local/sdeploy/mudrod-ingest/ftp-mirror/2016/12/ 2>&1 | tee mudrod-ingest-201612.log
