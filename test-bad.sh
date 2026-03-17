#!/bin/bash

for f in ./bad-tests/*.txt; do
    filename=$(basename $f)
    res="result.png"
    cat $f | python3 main.py $res
    echo
    echo
done