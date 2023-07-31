#!/bin/bash

bash gen_conf_cluster.sh
sleep 10

for i in {1..1}
do
  for j in {2..9}
  do
     echo "$i" "$j"
     bash start_cluster.sh "$i"
     sleep 10
     pkill python3
  done
done

for i in {2..5}
do
  for j in {0..9}
  do
     echo "$i" "$j"
     bash start_cluster.sh "$i"
     sleep 10
     pkill python3
  done
done
