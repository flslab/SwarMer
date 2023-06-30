#!/bin/bash

bash gen_conf_cluster.sh
sleep 10

for i in {0..16}
do
  for j in {0..9}
  do
     bash start_cluster.sh "$i"
     pkill python3
     sleep 10
  done
done
