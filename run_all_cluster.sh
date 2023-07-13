#!/bin/bash

bash gen_conf_cluster.sh
sleep 10

for i in {0..3}
do
#   bash set_conf_cluster.sh "$i"
   sleep 10
   bash start_cluster.sh "$i"
done
