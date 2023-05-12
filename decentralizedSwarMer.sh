#!/bin/bash

idx=0
num_of_total_servers=4
HOSTNAME="SwarMer-4-72.nova-PG0.clemson.cloudlab.us"
USERNAME="hamedamz"
REMOTE_HOME="/users/${USERNAME}"
server_addr=${USERNAME}@node-$idx.${HOSTNAME}
GITHUB_TOKEN="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"
now=$(date +%d-%b-%H_%M_%S)

for (( i=0; i<num_of_total_servers; i++ )); do
    server_addr=${USERNAME}@node-$i.${HOSTNAME}
#    ssh -oStrictHostKeyChecking=no ${server_addr} "git clone https://${GITHUB_TOKEN}:@github.com/flslab/SwarMer.git"
#    ssh -oStrictHostKeyChecking=no ${server_addr} "cd SwarMer && bash setup.sh"

#    ssh -oStrictHostKeyChecking=no ${server_addr} "pkill python"
#    ssh -oStrictHostKeyChecking=no ${server_addr} "cd SwarMer && git pull"
    ssh -oStrictHostKeyChecking=no -f ${server_addr} "ulimit -n 9999 && cd SwarMer && nohup python server.py ${num_of_total_servers} ${i} ${now} > my.log 2>&1 &"

#    scp -oStrictHostKeyChecking=no ~/.ssh/id_rsa ${server_addr}:${REMOTE_HOME}/.ssh/
#    ssh -oStrictHostKeyChecking=no ${server_addr} "sudo apt-get update"
#    ssh -oStrictHostKeyChecking=no ${server_addr} "wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh"
#    ssh -oStrictHostKeyChecking=no ${server_addr} "bash miniconda.sh --y"
#    ssh -oStrictHostKeyChecking=no ${server_addr} "source $REMOTE_HOME/.bashrc"
#    ssh -oStrictHostKeyChecking=no ${server_addr} "conda init"
done