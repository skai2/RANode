#!/bin/bash

for i in {1..5}
do
    xterm -e "python3 node.py"&
    sleep 1
done
