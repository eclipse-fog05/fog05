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

pub mod zchannel;
pub use zchannel::ZClientChannel;

pub mod types;
pub use types::*;



/// Trait to be implemented by services
pub trait ZServe<Req> : Sized + Clone {
    /// Type of the response
    type Resp;

    /// Connects to Zenoh, do nothing in this case...
    fn connect(&self);

    /// Authenticates to Zenoh, state changes to BUILDING
    fn authenticate(&self);

    // Registers, state changes to REGISTERED
    fn register(&self);

    // Announce, state changes to ANNOUNCED
    fn announce(&self);

    /// State changes to WORKING, will call or replace serve?
    fn work(&self) -> (async_std::sync::Sender<()>, async_std::task::JoinHandle<()>); //, ws: async_std::sync::Arc<zenoh::Workspace>);

    /// Starts serving all requests
    fn serve(&self, stop : async_std::sync::Receiver<()>);//, ws: async_std::sync::Arc<zenoh::Workspace>);

    /// State changes to UNWORKING, will stop serve/work
    fn unwork(&self, stop: async_std::sync::Sender<()>);

    // state changes to UNANNOUNCED
    fn unannounce(&self);

    ///  state changes to UNREGISTERED
    fn unregister(&self);

    /// state changes to DISCONNECTED
    fn disconnect(&self);

    /// removes the advertisement
    fn stop(self);
}