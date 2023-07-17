#!/bin/bash

bash gen_conf_cluster_aws.sh
sleep 10

for i in {0..39}
do
  for j in {0..19}
  do
     echo "$i" "$j"
     bash start_cluster_aws.sh "$i"
     sleep 10
     pkill python3
  done
done
