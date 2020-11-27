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
#![feature(associated_type_bounds)]
#![feature(try_trait)]

pub mod zchannel;
pub use zchannel::ZClientChannel;

pub mod types;
pub use types::*;

pub mod serialize;
pub mod zrpcresult;

use zrpcresult::ZRPCResult;
/// Trait to be implemented by services
pub trait ZServe<Req>: Sized + Clone {
    /// Type of the response
    type Resp;

    fn instance_uuid(&self) -> uuid::Uuid;

    /// Connects to Zenoh, do nothing in this case, state is HALTED
    #[allow(clippy::type_complexity)]
    fn connect(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>;

    /// Authenticates to Zenoh, state changes to INITIALIZING
    #[allow(clippy::type_complexity)]
    fn initialize(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>;

    // Registers, state changes to REGISTERED
    #[allow(clippy::type_complexity)]
    fn register(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>;

    // // Announce, state changes to ANNOUNCED
    // //fn announce(&self);

    /// State changes to SERVING, calls serve on a task::spawn, returns a stop sender and the serve task handle
    #[allow(clippy::type_complexity)]
    fn start(
        &self,
    ) -> ::core::pin::Pin<
        Box<
            dyn std::future::Future<
                    Output = ZRPCResult<(
                        async_std::sync::Sender<()>,
                        async_std::task::JoinHandle<ZRPCResult<()>>,
                    )>,
                > + '_,
        >,
    >;

    /// Starts serving all requests
    #[allow(clippy::type_complexity)]
    fn serve(
        &self,
        stop: async_std::sync::Receiver<()>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>;

    /// State changes to REGISTERED, will stop serve/work
    #[allow(clippy::type_complexity)]
    fn stop(
        &self,
        stop: async_std::sync::Sender<()>,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>;

    // state changes to HALTED
    #[allow(clippy::type_complexity)]
    fn unregister(
        &self,
    ) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>> + '_>>;

    /// removes state from Zenoh
    #[allow(clippy::type_complexity)]
    fn disconnect(self) -> ::core::pin::Pin<Box<dyn std::future::Future<Output = ZRPCResult<()>>>>;
}
