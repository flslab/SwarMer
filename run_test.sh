#!/bin/bash
for i in {0..59}
do
   cp "./experiments/test_config$i.py" test_config.py
   sleep 1
   python server.py
done
