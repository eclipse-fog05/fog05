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

use std::collections::hash_set::HashSet;
use std::collections::HashMap;
use std::env;
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

use signal_hook_async_std::Signals;

use uuid::Uuid;

use structopt::StructOpt;

use git_version::git_version;

#[cfg(feature = "isolation")]
use nix::{
    fcntl::OFlag,
    sched::CloneFlags,
    sys::{signal::kill, signal::Signal, stat::Mode, wait::waitpid},
    unistd::{execvp, fork, ForkResult},
};

#[cfg(feature = "isolation")]
use caps::{CapSet, Capability};

const NETNS_PATH: &str = "/run/netns/";
pub const NONE_FS: &str = "none";
pub const SYS_FS: &str = "sysfs";

const GIT_VERSION: &str = git_version!(prefix = "v", cargo_prefix = "v");

fn main() {
    // Init logging
    env_logger::init_from_env(
        env_logger::Env::default().filter_or(env_logger::DEFAULT_FILTER_ENV, "info"),
    );
    let mut args: Vec<String> = env::args().collect();
    log::trace!("Args: {:?}", args);

    let bin_name = args.remove(0);
    if args.len() < 2 {
        eprintln!("Usage {} namespace binary [args...]", bin_name);
        std::process::exit(-1);
    }

    let netns = args.remove(0);

    log::debug!("Eclipse fog05 Native Hypervisor Isolation {}", GIT_VERSION);

    #[cfg(feature = "isolation")]
    {
        log::trace!(
            "Ambient Capabilities: {:?}",
            caps::read(None, CapSet::Ambient)
        );
        log::trace!(
            "Bounding Capabilities: {:?}",
            caps::read(None, CapSet::Bounding)
        );
        log::trace!(
            "Effective Capabilities: {:?}",
            caps::read(None, CapSet::Effective)
        );
        log::trace!(
            "Inheritable Capabilities: {:?}",
            caps::read(None, CapSet::Inheritable)
        );
        log::trace!(
            "Permitted Capabilities: {:?}",
            caps::read(None, CapSet::Permitted)
        );

        let res = match caps::has_cap(None, CapSet::Permitted, Capability::CAP_SYS_ADMIN) {
            Ok(res) => res,
            Err(e) => {
                log::error!("Capabilities check error {}", e);
                process::exit(-1);
            }
        };

        if !res {
            log::error!("Missing CAP_SYS_ADMIN capability the program cannot proceed");
            process::exit(-1);
        }

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
        netns_path.push_str(&netns);

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
        if let Err(e) = nix::sched::setns(fd, setns_flags) {
            let _ = nix::unistd::close(fd);
            log::error!("setns error {}", e);
            process::exit(-1);
        }
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

        if let Err(e) = nix::mount::umount2(Path::new("/sys"), nix::mount::MntFlags::MNT_DETACH) {
            log::error!("umount2 error {}", e);
            process::exit(-1);
        }

        let sys_fs = Path::new(&SYS_FS);
        mount_flags = nix::mount::MsFlags::empty();
        if let Err(e) = nix::mount::mount(
            Some(Path::new(&netns)),
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
                async fn __main(netns: String, child: nix::unistd::Pid) {
                    log::info!("Running on namespace {} child is {}", netns, child);
                    let my_pid = process::id();

                    let signals = Signals::new(&[
                        signal_hook::SIGTERM,
                        signal_hook::SIGINT,
                        signal_hook::SIGQUIT,
                    ])
                    .unwrap();

                    let sig_handle = signals.handle();

                    let mut signals = signals.fuse();
                    if let Some(signal) = signals.next().await {
                        match signal {
                            signal_hook::SIGTERM | signal_hook::SIGINT | signal_hook::SIGQUIT => {
                                log::trace!("Received stop signal closing...");
                            }
                            _ => unreachable!(),
                        }
                    }

                    match kill(child, Some(Signal::SIGINT)) {
                        Ok(_) => log::trace!("Sending signal success"),
                        Err(e) => log::error!("Sending signal error {}", e),
                    }

                    match waitpid(child, None) {
                        Ok(_) => {
                            log::info!("Child is gone!");
                        }
                        Err(e) => {
                            log::error!("Error when waiting! {}", e);
                        }
                    }

                    if let Err(e) =
                        nix::mount::umount2(Path::new("/sys"), nix::mount::MntFlags::MNT_DETACH)
                    {
                        log::error!("umount2 error {}", e);
                        process::exit(-1);
                    }

                    if let Err(e) =
                        nix::mount::umount2(Path::new(NETNS_PATH), nix::mount::MntFlags::MNT_DETACH)
                    {
                        log::error!("umount2 error {}", e);
                        process::exit(-1);
                    }
                }
                async_std::task::block_on(async move { __main(netns, child).await })
            }
            Ok(ForkResult::Child) => {
                if let Err(e) = caps::clear(None, CapSet::Effective) {
                    log::error!("Error when clearing Effective Capabilities {}", e);
                    process::exit(-1);
                }

                if let Err(e) = caps::clear(None, CapSet::Permitted) {
                    log::error!("Error when clearing Permitted Capabilities {}", e);
                    process::exit(-1);
                }

                let cmd = args[0].clone();
                log::trace!("Child will start: {:?} with args {:?}", cmd, args);

                let cmd_cstring = CString::new(cmd.as_bytes()).unwrap();
                log::trace!("Child will start: {:p}", cmd_cstring.as_ptr());

                let mut c_args: Vec<CString> = args
                    .into_iter()
                    .map(|x| CString::new(x.as_bytes()).unwrap())
                    .collect();

                // Starting process
                execvp(&cmd_cstring, c_args.as_slice());
            }
            Err(_) => log::error!("Fork failed"),
        }
    }
}
