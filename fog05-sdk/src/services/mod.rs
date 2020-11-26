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


/// Trait to be implemented by services
pub trait ZServe<Req> : Sized + Clone {
    /// Type of the response
    type Resp;

    ///Starts serving all requests
    fn serve(self, locator: String);
}