#!/bin/bash

nohup bash run_test.sh > my.log 2>&1 &
echo $! > save_pid.txt