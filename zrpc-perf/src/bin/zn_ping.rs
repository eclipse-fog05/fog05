//
// Copyright (c) 2017, 2020 ADLINK Technology Inc.
//
// This program and the accompanying materials are made available under the
// terms of the Eclipse Public License 2.0 which is available at
// http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
// which is available at https://www.apache.org/licenses/LICENSE-2.0.
//
// SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
//
// Contributors:
//   ADLINK zenoh team, <zenoh@adlink-labs.tech>
//
use async_std::stream::StreamExt;
use async_std::sync::{Arc, Barrier, Mutex};
use async_std::channel::{unbounded, Sender, Receiver};
use async_std::task;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use zenoh::net::ResKey::*;
use zenoh::net::*;
use zenoh::Properties;
use structopt::StructOpt;


static DEFAULT_MODE: &str = "peer";
static DEFAULT_SIZE: &str = "8";
static DEFAULT_INT: &str = "1";
static DEFAULT_DURATION: &str = "60";
#[derive(StructOpt, Debug)]
struct PingArgs {
    /// Zenoh mode, client or peer
    #[structopt(short, long, default_value = DEFAULT_MODE)]
    mode: String,
    #[structopt(short, long)]
    peer: Option<String>,
    #[structopt(short, long, default_value = DEFAULT_SIZE)]
    size: u64,
    #[structopt(short, long, default_value = DEFAULT_INT)]
    interveal: f64,
    #[structopt(short, long, default_value = DEFAULT_DURATION)]
    duration: u64,
}

type PingInfo = (u64,usize,u128);

#[async_std::main]
async fn main() {
    // initiate logging
    env_logger::init();

    let args = PingArgs::from_args();

    let scenario = if args.mode == "peer" {
        "PP-PING"
    } else {
        "CRC-PING"
    };

    let properties = match args.peer {
        Some(peer) => format!("mode={};peer={}", args.mode, peer),
        None => format!("mode={}", args.mode),
    };
    let zproperties = Properties::from(properties);

    let session = open(zproperties.into()).await.unwrap();
    let session = Arc::new(session);


    let (s,r) = unbounded::<PingInfo>();

    // The hashmap with the pings
    let pending = Arc::new(Mutex::new(HashMap::<u64, Instant>::new()));
    let barrier = Arc::new(Barrier::new(2));

    let c_pending = pending.clone();
    let c_barrier = barrier.clone();
    let c_session = session.clone();
    task::spawn(async move {
        // The resource to wait the response back
        let reskey_pong = RId(c_session
            .declare_resource(&RName("/test/pong".to_string()))
            .await
            .unwrap());

        let sub_info = SubInfo {
            reliability: Reliability::Reliable,
            mode: SubMode::Push,
            period: None,
        };
        let mut sub = c_session
            .declare_subscriber(&reskey_pong, &sub_info)
            .await
            .unwrap();

        // Wait for the both publishers and subscribers to be declared
        c_barrier.wait().await;
        println!("SQ_NUMBER,SIZE,RTT_US,SCENARIO");
        while let Some(mut sample) = sub.stream().next().await {
            let mut count_bytes = [0u8; 8];
            sample.payload.read_bytes(&mut count_bytes);
            let count = u64::from_le_bytes(count_bytes);
            let instant = c_pending.lock().await.remove(&count).unwrap();
            s.send((count,sample.payload.len(),instant.elapsed().as_micros())).await;
            //print!("{},{},{},{}\n", count,sample.payload.len(),instant.elapsed().as_micros(),scenario);
        }
    });


    task::spawn(async move {
        loop {
            while let Ok(pi) = r.recv().await {
                let (c,s,rtt) = pi;
                print!("{},{},{},{}\n", c,s,rtt,scenario);
            }
        }
    });

    let d = args.duration;
    task::spawn(async move {
         task::sleep(Duration::from_secs(d)).await;
         std::process::exit(0);
    });

    // The resource to publish data on
    let reskey_ping = RId(session
        .declare_resource(&RName("/test/ping".to_string()))
        .await
        .unwrap());
    let _publ = session.declare_publisher(&reskey_ping).await.unwrap();

    // Wait for the both publishers and subscribers to be declared
    barrier.wait().await;

    let payload = vec![0u8; args.size as usize - 8];
    let mut count: u64 = 0;
    let i = args.interveal;
    loop {
        let mut data: WBuf = WBuf::new(args.size as usize, true);
        let count_bytes: [u8; 8] = count.to_le_bytes();
        data.write_bytes(&count_bytes);
        data.write_bytes(&payload);

        let data: RBuf = data.into();

        pending.lock().await.insert(count, Instant::now());
        session
            .write_ext(
                &reskey_ping,
                data,
                encoding::DEFAULT,
                data_kind::DEFAULT,
                CongestionControl::Block, // Make sure to not drop messages because of congestion control
            )
            .await
            .unwrap();

        task::sleep(Duration::from_secs_f64(i)).await;
        count += 1;
    }
}