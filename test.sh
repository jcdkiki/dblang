#!/bin/bash
set -e

rm -rf result
mkdir -p result

for f in ./tests/*.txt; do
    filename=$(basename $f)
    res="result/${filename%.*}.png"
    cat $f | python3 main.py $res
done

rm result.dot