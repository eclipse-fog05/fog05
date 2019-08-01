(*********************************************************************************
 * Copyright (c) 2018 ADLINK Technology Inc. *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
 * which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 * Contributors: 1
 *   Gabriele Baldoni (gabriele (dot) baldoni (at) adlinktech (dot) com ) - OCaml implementation
 *********************************************************************************)


open Fos_im
type faemapi





module AtomicEntity : sig

  val onboard : User.Descriptors.AtomicEntity.descriptor -> faemapi  -> User.Descriptors.AtomicEntity.descriptor Lwt.t
  val instantiate : string -> faemapi -> Infra.Descriptors.AtomicEntity.record Lwt.t
  val terminate : string -> faemapi -> Infra.Descriptors.AtomicEntity.record Lwt.t
  val offload : string -> faemapi -> User.Descriptors.AtomicEntity.descriptor Lwt.t
  val get_atomic_entity_descriptor : string -> faemapi -> User.Descriptors.AtomicEntity.descriptor Lwt.t
  val get_atomic_entity_instance_info : string -> faemapi -> Infra.Descriptors.AtomicEntity.record Lwt.t

end


module FAEMAPI : sig

  val connect : ?locator:string -> ?sysid:string -> ?tenantid:string -> unit -> faemapi Lwt.t
  val close : faemapi -> unit Lwt.t

end