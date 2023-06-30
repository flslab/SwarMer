#!/bin/bash

source cloudlab_vars.sh

cp "experiments/config$1.py" config.py

for (( i=1; i<num_of_total_servers; i++ )); do
    server_addr=${USERNAME}@node-$i.${HOSTNAME}
    ssh -oStrictHostKeyChecking=no -f "${server_addr}" "cd SwarMer && cp experiments/config$1.py config.py" &
done
