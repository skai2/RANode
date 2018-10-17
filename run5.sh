#!/bin/bash

for i in {1..4}
do
    xterm -e "python3 sricart.py"&
    sleep 1
done
