#!/bin/bash

source cloudlab_vars.sh

now=$(date +%d-%b-%H_%M_%S)

for (( i=1; i<num_of_total_servers; i++ )); do
    server_addr=${USERNAME}@node-$i.${HOSTNAME}
    ssh -oStrictHostKeyChecking=no -f "${server_addr}" "ulimit -n 99999 && cd SwarMer && cp experiments/config$1.py config.py && sleep 10 && nohup python3 secondary.py > my.log 2>&1 &" &
done

ulimit -n 99999 && cp "experiments/config$1.py" config.py && sleep 1 && python3 primary.py "${N}" "${now}"
