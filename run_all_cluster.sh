#!/bin/bash

bash gen_conf_cluster.sh
sleep 10

for i in {0..15}
do
  for j in {0..9}
  do
     bash start_cluster.sh "$i" "$j"
     sleep 10
     echo "$i" "$j"
     pkill python3
  done
done
