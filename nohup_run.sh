#!/bin/bash

nohup bash run.sh > my.log 2>&1 &
echo $! > save_pid.txt