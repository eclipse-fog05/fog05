#!/usr/bin/env bash


plog () {
TS=`eval date "+%F-%T"`
   echo "[$TS]: $1"
}

TS=`eval date "+%F-%T"`

INITIAL_SIZE=8
END_SIZE=65536

BIN_DIR="../target/release"

WD=$(pwd)

GET_BIN="get"
QUERY_BIN="query"

CALL_BIN="zrpc_call"

EVAL_BIN="eval"
GET_EVAL_BIN="get_eval"

NET_EVAL_BIN="net_eval"
NET_GET_EVAL_BIN="query_eval"

STATE_BIN="zrpc_state"
ZSTATE_BIN="zrpc_get_zenoh"

ZENOH_REPO="https://github.com/eclipse-zenoh/zenoh"
ZENOH_BRANCH="master"
ZENOH_DIR="$WD/zenoh"

OUT_DIR="results"

DURATION=120
ZENOHD_PATH="$ZENOH_DIR/target/release/zenohd"

if [[ ! -d $ZENOH_DIR ]];
then
   plog "Cloning and building zenoh from $ZENOH_REPO branch $ZENOH_BRANCH"
   git clone $ZENOH_REPO -b $ZENOH_BRANCH $ZENOH_DIR
   cd $ZENOH_DIR
   cargo build --release
   cd $WD
else
   cd $ZENOH_DIR
   git pull
   cargo build --release
   cd $WD
fi


mkdir -p $OUT_DIR


plog "Running baseline get bench"

x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   plog "Running GET bench with $x size"
   $BIN_DIR/$GET_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/get-$x-$TS.csv
   plog "Done GET bench with $x size"
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Running baseline query bench"

x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   plog "Running GET bench with $x size"
   $BIN_DIR/$QUERY_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/query-$x-$TS.csv
   plog "Done GET bench with $x size"
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Running baseline net queriable bench"

x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   nohup $BIN_DIR/$NET_EVAL_BIN -m client -p tcp/127.0.0.1:7447 -s $x > /dev/null 2>&1 &
   EV_PID=$!
   plog "Eval PID $EV_PID"
   plog "Running EVAL bench with $x size"
   $BIN_DIR/$NET_GET_EVAL_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/net-eval-$x-$TS.csv
   plog "Done EVAL bench with $x size"
   kill -9 $ZENOHD_PID
   kill -9 $EV_PID
   x=$(( $x * 2 ))
done

plog "Running baseline eval bench"

x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   nohup $BIN_DIR/$EVAL_BIN -m client -p tcp/127.0.0.1:7447 -s $x > /dev/null 2>&1 &
   EV_PID=$!
   plog "Eval PID $EV_PID"
   plog "Running EVAL bench with $x size"
   $BIN_DIR/$GET_EVAL_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/eval-$x-$TS.csv
   plog "Done EVAL bench with $x size"
   kill -9 $ZENOHD_PID
   kill -9 $EV_PID
   x=$(( $x * 2 ))
done

plog "Running ZRPC Call bench"


x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   plog "Starting zenohd..."
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   sleep 1
   nohup $BIN_DIR/$CALL_BIN -m server -r tcp/127.0.0.1:7447 -s $x > /tmp/server.out 2>&1 &
   SERVER_PID=$!
   plog "ZRPC Server running $SERVER_PID"
   sleep 5
   plog "Running zrpc call bench with $x size"
   $BIN_DIR/$CALL_BIN -d $DURATION -i 1 -m client -r tcp/127.0.0.1:7447 -s $x  > $OUT_DIR/call-$x-$TS.csv
   plog "Done ZRPC Call bench, killing server and zenoh"
   kill -9 $SERVER_PID
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Running ZRPC Call w/o check bench"


x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   plog "Starting zenohd..."
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   sleep 1
   nohup $BIN_DIR/$CALL_BIN -m server -r tcp/127.0.0.1:7447 -s $x > /tmp/server.out 2>&1 &
   SERVER_PID=$!
   plog "ZRPC Server running $SERVER_PID"
   sleep 5
   plog "Running zrpc call w/o chk bench with $x size"
   $BIN_DIR/$CALL_BIN -d $DURATION -i 1 -m client -r tcp/127.0.0.1:7447 -s $x -n > $OUT_DIR/nochk-call-$x-$TS.csv
   plog "Done ZRPC Call bench, killing server and zenoh"
   kill -9 $SERVER_PID
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Done Test results stored in $OUT_DIR, killing zenohd"
plog "Bye!"


