#!/bin/bash

bash gen_conf_cluster_aws.sh
sleep 10

for i in {0..15}
do
  for j in {0..2}
  do
     echo "$i" "$j"
     bash start_cluster_aws.sh "$i"
     sleep 10
     pkill python3
  done
done

for i in {0..15}
do
  for j in {3..9}
  do
     echo "$i" "$j"
     bash start_cluster_aws.sh "$i"
     sleep 10
     pkill python3
  done
done