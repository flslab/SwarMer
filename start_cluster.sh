#!/bin/bash

source cloudlab_vars.sh

now=$(date +%d-%b-%H_%M_%S)

for (( i=1; i<num_of_total_servers; i++ )); do
    server_addr=${USERNAME}@node-$i.${HOSTNAME}
    ssh -oStrictHostKeyChecking=no -f "${server_addr}" "sleep 20 && ulimit -n 9999 && cd SwarMer && nohup python3 server.py ${num_of_total_servers} ${i} ${now} > my.log 2>&1 &" &
done

ulimit -n 9999 && cd SwarMer && python3 server.py "${num_of_total_servers}" 0 "${now}"
