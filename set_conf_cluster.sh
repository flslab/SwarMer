#!/bin/bash

source cloudlab_vars.sh

cp "experiments/config$0.py" config.py

for (( i=1; i<num_of_total_servers; i++ )); do
    server_addr=${USERNAME}@${HOST}${i}
    ssh -oStrictHostKeyChecking=no -f "${server_addr}" "cd SwarMer && cp experiments/config$0.py config.py" &
done
