/*********************************************************************************
* Copyright (c) 2018,2020 ADLINK Technology Inc.
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
* which is available at https://www.apache.org/licenses/LICENSE-2.0.
*
* SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
* Contributors:
*   ADLINK fog05 team, <fog05@adlink-labs.tech>
*********************************************************************************/
#![allow(unused)]

use std::collections::HashMap;
use std::ffi::CStr;
use std::ffi::CString;
use std::path::Path;
use std::process;
use std::str;
use std::time::Duration;

use async_std::fs;
use async_std::path::Path as AsyncPath;
use async_std::prelude::*;
use async_std::sync::{Arc, RwLock};
use async_std::task;

use futures::stream::TryStreamExt;

use zenoh::*;

use fog05_sdk::fresult::{FError, FResult};
use fog05_sdk::types::IPAddress;
use fog05_sdk::zconnector::ZConnector;

use zrpc::ZServe;
use zrpc_macros::zserver;

//use async_ctrlc::CtrlC;
use uuid::Uuid;

use structopt::StructOpt;

use git_version::git_version;

#[cfg(feature = "isolation")]
use nix::{
    fcntl::OFlag,
    sched::CloneFlags,
    sys::{signal::kill, stat::Mode, wait::waitpid},
    unistd::{execvp, fork, ForkResult},
};

const NETNS_PATH: &str = "/run/netns/";
pub const NONE_FS: &str = "none";
pub const SYS_FS: &str = "sysfs";

const GIT_VERSION: &str = git_version!(prefix = "v", cargo_prefix = "v");

#[derive(StructOpt, Debug)]
struct IsolateArgs {
    /// Config file
    #[structopt(short, long)]
    netns: String,
    #[structopt(short, long)]
    cmd: String,
}

fn main() {
    // Init logging
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );
    let args = IsolateArgs::from_args();

    log::debug!("Eclipse fog05 Native Hypervisor Isolation {}", GIT_VERSION);
    log::trace!("Args: {:?}", args);

    #[cfg(feature = "isolation")]
    {
        log::trace!("Changing namespace");
        // https://github.com/shemminger/iproute2/blob/f33a871b8094ae0f6e6293804e1cc6edbba0e108/lib/namespace.c#L49
        let mut unshare_flags = CloneFlags::empty();
        let mut setns_flags = CloneFlags::empty();
        let mut open_flags = OFlag::empty();
        let mut mount_flags = nix::mount::MsFlags::empty();
        let none_p4: Option<&Path> = None;

        unshare_flags.insert(CloneFlags::CLONE_NEWNS);

        let mut netns_path = String::new();
        netns_path.push_str(NETNS_PATH);
        netns_path.push_str(&args.netns);

        open_flags.insert(OFlag::O_RDONLY);
        open_flags.insert(OFlag::O_CLOEXEC);

        let fd = match nix::fcntl::open(Path::new(&netns_path), open_flags, Mode::empty()) {
            Ok(raw_fd) => raw_fd,
            Err(e) => {
                log::error!("open error {}", e);
                process::exit(-1);
            }
        };

        setns_flags.insert(CloneFlags::CLONE_NEWNET);
        match nix::sched::setns(fd, setns_flags) {
            Err(e) => {
                let _ = nix::unistd::close(fd);
                log::error!("setns error {}", e);
                process::exit(-1);
            }
            Ok(_) => {
                let _ = nix::unistd::close(fd);

                if let Err(e) = nix::sched::unshare(unshare_flags) {
                    log::error!("Unshare error {}", e);
                    process::exit(-1);
                }

                let none_fs = Path::new(&NONE_FS);
                mount_flags.insert(nix::mount::MsFlags::MS_REC);
                mount_flags.insert(nix::mount::MsFlags::MS_SLAVE);
                if let Err(e) = nix::mount::mount(
                    Some(Path::new("")),
                    Path::new("/"),
                    Some(none_fs),
                    mount_flags,
                    none_p4,
                ) {
                    log::error!("mount error {}", e);
                    process::exit(-1);
                }

                if let Err(e) =
                    nix::mount::umount2(Path::new("/sys"), nix::mount::MntFlags::MNT_DETACH)
                {
                    log::error!("umount2 error {}", e);
                    process::exit(-1);
                }

                let sys_fs = Path::new(&SYS_FS);
                mount_flags = nix::mount::MsFlags::empty();
                if let Err(e) = nix::mount::mount(
                    Some(Path::new(&args.netns)),
                    Path::new("/sys"),
                    Some(sys_fs),
                    mount_flags,
                    none_p4,
                ) {
                    log::error!("mount sysfs error {}", e);
                    process::exit(-1);
                }

                match unsafe { fork() } {
                    Ok(ForkResult::Parent { child, .. }) => {
                        async fn __main(args: IsolateArgs, child: nix::unistd::Pid) {
                            log::info!("Running on namespace {} child is {}", args.netns, child);
                            let my_pid = process::id();

                            // let ctrlc = CtrlC::new().expect("Unable to create Ctrl-C handler");
                            // let mut stream = ctrlc.enumerate().take(1);
                            // stream.next().await;
                            // log::trace!("Received Ctrl-C start teardown");

                            // kill(child, 2);

                            match waitpid(child, None) {
                                Ok(_) => {
                                    log::info!("Child is gone!");
                                }
                                Err(e) => {
                                    log::error!("Error when waiting! {}", e);
                                }
                            }
                        }
                        async_std::task::block_on(async move { __main(args, child).await })
                    }
                    Ok(ForkResult::Child) => {
                        let mut cmd_arg: Vec<&str> = args.cmd.split(' ').collect();
                        let cmd = cmd_arg.remove(0);
                        log::trace!("Child will start: {:?} with args {:?}", cmd, cmd_arg);

                        let cmd_cstring = CString::new(cmd.as_bytes()).unwrap();
                        log::trace!("Child will start: {:p}", cmd_cstring.as_ptr());

                        let mut c_args: Vec<CString> = cmd_arg
                            .into_iter()
                            .map(|x| CString::new(x.as_bytes()).unwrap())
                            .rev()
                            .collect();

                        // Starting process
                        execvp(&cmd_cstring, c_args.as_slice());
                    }
                    Err(_) => log::error!("Fork failed"),
                }
            }
        }
    }
}
