#!/usr/bin/env bash


plog () {
TS=`eval date "+%F-%T"`
   echo "[$TS]: $1"
}

TS=$(date "+%F-%T")

INITIAL_SIZE=8
END_SIZE=65536

BIN_DIR="./target/release"

WD=$(pwd)

SERVER_BIN="gserver"
CLIENT_BIN="gclient"

GET_BIN="get"
QUERY_BIN="query"

CALL_BIN="zrpc_call"

NCALL_BIN="znrpc_call"

EVAL_BIN="eval"
GET_EVAL_BIN="get_eval"

NET_EVAL_BIN="queryable"
NET_GET_EVAL_BIN="query_eval"

STATE_BIN="zrpc_state"
ZSTATE_BIN="zrpc_get_zenoh"

SER_BIN="serialization"
DE_BIN="deserialization"

ZENOH_REPO="https://github.com/eclipse-zenoh/zenoh"
ZENOH_BRANCH="master"
ZENOH_DIR="$WD/zenoh"

OUT_DIR="results"

DURATION=20
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

plog "Running baseline gRPC bench"

x=8
while [ $x -le $END_SIZE ]
do
   nohup $BIN_DIR/$SERVER_BIN -a 127.0.0.1:50001 -s $x > /dev/null 2>&1 &
   SERVER_PID=$!
   plog "Server PID $SERVER_PID"
   plog "Running gRPC bench with $x size"
   $BIN_DIR/$CLIENT_BIN -d $DURATION -i 1 -a 127.0.0.1:50001 -s $x > $OUT_DIR/grpc-$x-$TS.csv
   plog "Done gRPC bench with $x size"
   kill -9 $SERVER_PID
   x=$(( $x * 2 ))
done

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
   plog "Running QUERY bench with $x size"
   $BIN_DIR/$QUERY_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/query-$x-$TS.csv
   plog "Done QUERY bench with $x size"
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Running baseline net queryable bench"

x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   nohup $BIN_DIR/$NET_EVAL_BIN -m client -p tcp/127.0.0.1:7447 -s $x > /dev/null 2>&1 &
   EV_PID=$!
   plog "Queryable PID $EV_PID"
   plog "Running Queryable bench with $x size"
   $BIN_DIR/$NET_GET_EVAL_BIN -d $DURATION -i 1 -m client -p tcp/127.0.0.1:7447 -s $x > $OUT_DIR/queryable-$x-$TS.csv
   plog "Done Queryable bench with $x size"
   kill -9 $ZENOHD_PID
   kill -9 $EV_PID
   x=$(( $x * 2 ))
done


plog "Running baseline net p2p queryable bench"

x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $BIN_DIR/$NET_EVAL_BIN  -s $x > /dev/null 2>&1 &
   EV_PID=$!
   plog "Queryable PID $EV_PID"
   plog "Running Queryable P2P bench with $x size"
   $BIN_DIR/$NET_GET_EVAL_BIN -d $DURATION -i 1 -s $x > $OUT_DIR/p2p-queryable-$x-$TS.csv
   plog "Done Queryable P2P bench with $x size"
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
   sleep 2
   nohup $BIN_DIR/$CALL_BIN -m server -r tcp/127.0.0.1:7447 -s $x > /tmp/server.out 2>&1 &
   SERVER_PID=$!
   plog "ZRPC Server running $SERVER_PID"
   sleep 6
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
   sleep 2
   nohup $BIN_DIR/$CALL_BIN -m server -r tcp/127.0.0.1:7447 -s $x > /tmp/server.out 2>&1 &
   SERVER_PID=$!
   plog "ZRPC Server running $SERVER_PID"
   sleep 6
   plog "Running zrpc call w/o chk bench with $x size"
   $BIN_DIR/$CALL_BIN -d $DURATION -i 1 -m client -r tcp/127.0.0.1:7447 -s $x -n > $OUT_DIR/nochk-call-$x-$TS.csv
   plog "Done ZRPC Call bench, killing server and zenoh"
   kill -9 $SERVER_PID
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Running ZNRPC Call bench"
x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   plog "Starting zenohd..."
   nohup $ZENOHD_PATH --mem-storage "/test/**" -l tcp/127.0.0.1:7447 > /dev/null 2>&1 &
   ZENOHD_PID=$!
   plog "Zenohd running PID $ZENOHD_PID"
   sleep 2
   nohup $BIN_DIR/$NCALL_BIN -z client -m server -r tcp/127.0.0.1:7447 -s $x > /tmp/server.out 2>&1 &
   SERVER_PID=$!
   plog "ZNRPC Server running $SERVER_PID"
   sleep 6
   plog "Running ZNRPC call bench with $x size"
   $BIN_DIR/$NCALL_BIN -d $DURATION -z client -i 1 -m client -r tcp/127.0.0.1:7447 -s $x > $OUT_DIR/zcall-$x-$TS.csv
   plog "Done ZNRPC Call bench, killing server and zenoh"
   kill -9 $SERVER_PID
   kill -9 $ZENOHD_PID
   x=$(( $x * 2 ))
done


plog "Running P2P ZNRPC Call bench"
x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   nohup $BIN_DIR/$NCALL_BIN -z peer -m server -s $x > /tmp/server.out 2>&1 &
   SERVER_PID=$!
   plog "P2P ZNRPC Server running $SERVER_PID"
   sleep 5
   plog "Running P2P ZNRPC call bench with $x size"
   $BIN_DIR/$NCALL_BIN -d $DURATION -z peer -i 1 -m client -s $x > $OUT_DIR/p2p-zcall-$x-$TS.csv
   plog "Done P2P ZNRPC Call bench, killing server and zenoh"
   kill -9 $SERVER_PID
   x=$(( $x * 2 ))
done


plog "Running ZNRPC Response Serialization bench"
x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   plog "Running ZNRPC Response Serialization bench with $x size"
   $BIN_DIR/$SER_BIN -d $DURATION -i 1 -s $x > $OUT_DIR/serialize-$x-$TS.csv
   plog "Done ZNRPC Response Serialization"
   x=$(( $x * 2 ))
done

plog "Running ZNRPC Response Deserialization bench"
x=$INITIAL_SIZE
while [ $x -le $END_SIZE ]
do
   plog "Running ZNRPC Response Deserialization bench with $x size"
   $BIN_DIR/$DE_BIN -d $DURATION -i 1 -s $x > $OUT_DIR/deserialize-$x-$TS.csv
   plog "Done ZNRPC Response Deserialization"
   x=$(( $x * 2 ))
done



plog "Done Test results stored in $OUT_DIR, killing zenohd"
plog "Bye!"


