#!/bin/bash

bash gen_conf_cluster_aws.sh
sleep 10

for i in {0..19}
do
  for j in {0..14}
  do
     bash start_cluster_aws.sh "$i"
#     echo "$i" "$j"
     sleep 10
     pkill python3
  done
done
