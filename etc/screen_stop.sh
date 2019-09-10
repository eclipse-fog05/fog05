#!/usr/bin/env bash

screen -S lxdp -X quit
sleep 1
screen -S netp -X quit
sleep 1
screen -S linuxp -X quit
sleep 1
screen -S agent -X quit
sleep 1
screen -S rest -X quit
sleep 1
screen -S yaks -X quit
