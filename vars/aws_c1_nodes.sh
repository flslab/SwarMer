#!/bin/bash

N=90 # number of total servers
USERNAME="ubuntu"
KEY_PATH="/Users/hamed/Desktop/hamed-vir.pem"
LOCAL_KEY_PATH="~/SwarMer/hamed-vir.pem"

#cluster 1
HOSTNAMES=(
"172.31.94.241"
"172.31.82.240"
"172.31.94.116"
"172.31.95.244"
"172.31.82.119"
"172.31.93.246"
"172.31.90.248"
"172.31.86.247"
"172.31.88.124"
"172.31.88.122"
"172.31.89.127"
"172.31.92.252"
"172.31.85.194"
"172.31.86.64"
"172.31.91.198"
"172.31.81.196"
"172.31.86.72"
"172.31.81.200"
"172.31.82.203"
"172.31.90.201"
"172.31.84.78"
"172.31.87.76"
"172.31.87.79"
"172.31.88.206"
"172.31.92.207"
"172.31.80.207"
"172.31.86.84"
"172.31.93.208"
"172.31.86.216"
"172.31.91.85"
"172.31.80.91"
"172.31.95.217"
"172.31.90.93"
"172.31.85.219"
"172.31.95.35"
"172.31.92.162"
"172.31.83.164"
"172.31.92.36"
"172.31.86.41"
"172.31.84.169"
"172.31.86.169"
"172.31.82.41"
"172.31.81.173"
"172.31.93.44"
"172.31.90.48"
"172.31.95.173"
"172.31.86.50"
"172.31.81.178"
"172.31.94.188"
"172.31.93.56"
"172.31.91.189"
"172.31.82.189"
"172.31.80.191"
"172.31.85.190"
"172.31.93.1"
"172.31.92.63"
"172.31.85.132"
"172.31.85.131"
"172.31.82.6"
"172.31.81.5"
"172.31.86.135"
"172.31.88.7"
"172.31.95.140"
"172.31.90.137"
"172.31.86.224"
"172.31.95.227"
"172.31.82.226"
"172.31.82.230"
"172.31.90.228"
"172.31.94.231"
"172.31.94.103"
"172.31.87.107"
"172.31.90.104"
"172.31.84.110"
"172.31.95.236"
"172.31.81.111"
"172.31.83.110"
"172.31.88.14"
"172.31.80.142"
"172.31.87.145"
"172.31.92.144"
"172.31.94.148"
"172.31.84.19"
"172.31.95.22"
"172.31.90.150"
"172.31.83.154"
"172.31.91.153"
"172.31.82.28"
"172.31.92.28"
"172.31.88.159"
)