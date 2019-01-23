#!/usr/bin/env bash
PID=$1
if [ -n "$(ps -p $PID -o pid=)" ]; then
        echo 1
else
        echo 0
fi
