#!/bin/bash

bash gen_conf_cluster.sh
sleep 10

for i in 3 7 9 10 11
do
  for j in {0..9}
  do
     echo "$i" "$j"
     bash start_cluster.sh "$i"
     sleep 10
     pkill python3
  done
done
