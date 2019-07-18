#!/bin/bash

id=$(cat /etc/machine-id)
first=$(echo $id | cut -c -8)
second=$(echo $id | cut -c 9-12)
third=$(echo $id | cut -c 13-16)
fourth=$(echo $id | cut -c 17-20)
fifth=$(echo $id | cut -c 21-)
echo $first-$second-$third-$fourth-$fifth
