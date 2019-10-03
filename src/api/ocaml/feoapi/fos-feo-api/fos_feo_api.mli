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
type feoapi





module Entity : sig

  val onboard : User.Descriptors.Entity.descriptor -> feoapi  -> User.Descriptors.Entity.descriptor Lwt.t
  val instantiate : string -> feoapi -> Infra.Descriptors.Entity.record Lwt.t
  val terminate : string -> feoapi -> Infra.Descriptors.Entity.record Lwt.t
  val offload : string -> feoapi -> User.Descriptors.Entity.descriptor Lwt.t
  val get_entity_descriptor : string -> feoapi -> User.Descriptors.Entity.descriptor Lwt.t
  val get_entity_instance_info : string -> feoapi -> Infra.Descriptors.Entity.record Lwt.t

  val list : feoapi -> string list Lwt.t
  val instance_list : string -> feoapi -> string list Lwt.t

end


module FEOAPI : sig

  val connect : ?locator:string -> ?sysid:string -> ?tenantid:string -> unit -> feoapi Lwt.t
  val close : feoapi -> unit Lwt.t

end