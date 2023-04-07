#!/usr/bin/env bash

docker build -t cptw .
docker save -o docker/cptw.tar cptw

mkdir -p ./data/input_data/
mkdir ./data/output_data/
mkdir ./data/plots/

cp cptw.tar cptw/
cp enter.sh cptw/
cp kill.sh cptw/
cp load.sh cptw/
cp run.sh cptw/
#cp setup_data.sh cptw/

rm cptw.zip
zip -r cptw.zip cptw/
rm -rf cptw/
