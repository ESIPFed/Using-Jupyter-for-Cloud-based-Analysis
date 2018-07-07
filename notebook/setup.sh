#!/usr/bin/env bash

touch ~/.aws/credentials
cat << EOF >> ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
EOF

touch ~/.aws/config
cat << EOF >> ~/.aws/config
[default]
region=us-west-2
EOF


mkdir -p /tmp/nexuscli
cd /tmp/nexuscli
git init
git remote add -f origin https://github.com/apache/incubator-sdap-nexus
git config core.sparseCheckout true
echo "client" >> .git/info/sparse-checkout
git pull origin master
cd client
python setup.py install


pip install -r requirements.txt
