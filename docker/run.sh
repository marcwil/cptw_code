#!/usr/bin/env bash

docker run --name cptw --rm\
#       --user "$(id -u):$(id -g)"\
       -v $PWD/data/input_data:/cptw/input_data\
       -v $PWD/data/output_data:/cptw/output_data\
       -v $PWD/data/plots:/cptw/output.pdf\
       cptw &
