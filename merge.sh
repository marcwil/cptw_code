#!/usr/bin/env bash
#

if [ $# -ge 3 ]; then
    echo "usage: merge.sh basename [output]"
    exit 1
fi

basename=$1
output=$basename.csv
if [ $# -eq 2 ]; then
    output=$2
fi

first=true
for var in $basename*; do
    if [ $first == true ]; then
        cat $var > $output
        first=false
    else
        tail -n +2 $var >> $output
    fi
done
