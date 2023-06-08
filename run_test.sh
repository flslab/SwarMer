#!/bin/bash

python3 gen_conf.py -t
sleep 1

for i in {0..47}
do
   cp "./experiments/test_config$i.py" test_config.py
   sleep 1
   python3 server.py
done
