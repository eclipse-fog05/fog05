#!/usr/bin/env bash


plog () {
TS=`eval date "+%F-%T"`
   echo "[$TS]: $1"
}


BIN_DIR="../../target/release/examples"

PUT_BIN="put"
GET_BIN="get"
CALL_BIN="zrpc_call"
STATE_BIN="zrpc_state"
ZSTATE_BIN="zrpc_get_zenoh"
EVAL_BIN="eval"
GET_EVAL_BIN="get_eval"


ZENOHD_PATH="/home/ato/Workspace/zenoh/target/release/zenohd"

OUT_DIR="results"

DURATION=120

mkdir -p $OUT_DIR

plog "Starting baseline Zenoh get bench"



plog "Starting zenohd..."
nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
ZENOHD_PID=$!
plog "Zenohd running PID $ZENOHD_PID"

plog "Populating storage"
$BIN_DIR/$PUT_BIN

x=60
plog "Running GET bench with $x size"
$BIN_DIR/$GET_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/get-$x.csv
plog "Done GET bench with $x size, sleeping 5 secs"
sleep 5;

x=128
plog "Running GET bench with $x size"
$BIN_DIR/$GET_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/get-$x.csv
plog "Done GET bench with $x size, sleeping 5 secs"
sleep 5;


x=491
plog "Running GET bench with $x size"
$BIN_DIR/$GET_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/get-$x.csv
plog "Done GET bench with $x size, sleeping 5 secs"
sleep 5;

x=679
plog "Running GET bench with $x size"
$BIN_DIR/$GET_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/get-$x.csv
plog "Done GET bench with $x size, sleeping 5 secs"
sleep 5;



plog "Running GET bench zenoh router admin"
$BIN_DIR/$ZSTATE_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 > $OUT_DIR/zstate.csv
plog "Done GET bench zenoh router admin, sleeping 5 secs"
sleep 5;

plog "Running EVAL bench"
nohup $BIN_DIR/$EVAL_BIN -m client -p tcp/127.0.0.1:7447 -s 60 > /dev/null 2>&1 &
EV_PID=$!
plog "Publiser PID $EV_PID"

$BIN_DIR/$GET_EVAL_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s 60 > $OUT_DIR/eval-$x.csv
plog "Done EVAL bench, killind eval and sleeping 5 secs"
kill -9 $EV_PID


plog "killing zenohd"
kill -9 $ZENOHD_PID


plog "Running ZRPC Call bench"

plog "Starting zenohd..."
nohup $ZENOHD_PATH --mem-storage "/lfos/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
ZENOHD_PID=$!
plog "Zenohd running PID $ZENOHD_PID"

$BIN_DIR/$CALL_BIN -m server -r -r tcp/127.0.0.1:7447 > /dev/null 2>&1 &
SERVER_PID=$!
plog "ZRPC Server running $SERVER_PID"
sleep 5;
$BIN_DIR/$CALL_BIN -d $DURATION -i 1 -m client -r tcp/127.0.0.1:7447 > $OUT_DIR/call.csv
plog "Done ZRPC Call bench, sleeping 5 secs"
kill -9 $SERVER_PID


plog "Running ZRPC State bench"

plog "Starting zenohd..."
nohup $ZENOHD_PATH --mem-storage "/lfos/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
ZENOHD_PID=$!
plog "Zenohd running PID $ZENOHD_PID"
$BIN_DIR/$STATE_BIN -m server -r -r tcp/127.0.0.1:7447 > /dev/null 2>&1 &
SERVER_PID=$!
plog "ZRPC Server running $SERVER_PID"
sleep 5;
$BIN_DIR/$STATE_BIN -d $DURATION -i 1 -m client -r tcp/127.0.0.1:7447 > $OUT_DIR/state.csv
plog "Done ZRPC Call State, sleeping 5 secs"
kill -9 $SERVER_PID


plog "Done Test results stored in $OUT_DIR, killing zenohd"
kill -9 $ZENOHD_PID
plog "Bye!"


