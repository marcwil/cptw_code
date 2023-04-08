#!/usr/bin/env bash

echo "Building Dockerfile.."
docker build -t cptw .
echo "Saving docker image to tar.."
docker save -o cptw.tar cptw

echo "Creating data directories.."
mkdir -p ./data/input_data/
mkdir ./data/output_data/
mkdir ./data/plots/

echo "Copying stuff.."
mkdir cptw
cp cptw.tar cptw/
cp enter.sh cptw/
cp kill.sh cptw/
cp load.sh cptw/
cp run.sh cptw/
#cp setup_data.sh cptw/

echo "Creating new zip.."
rm cptw.zip
zip -r cptw.zip cptw/
echo "Deleting temporary files.."
rm -rf cptw/
rm cptw.tar
echo "Done."
