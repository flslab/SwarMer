#!/bin/bash

bash gen_conf_cluster.sh
sleep 10

for i in {0..15}
do
  for j in {0..14}
  do
     bash start_cluster.sh "$i"
#     echo "$i" "$j"
     sleep 10
     pkill python3
  done
done
