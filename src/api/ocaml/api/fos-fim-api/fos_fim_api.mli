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
type api



module Manifest : sig

  val check : string -> bool


end


module Node : sig

  val list : api -> (FTypes.node_info list) Lwt.t
  val info : string -> api -> FTypes.node_info Lwt.t
  val status : string -> api -> FTypes.node_status Lwt.t
  val plugins : string  -> api -> (FTypes.plugin list) Lwt.t

end


module Network : sig

  val add_network : FTypes.virtual_network -> api -> bool Lwt.t
  val remove_network : string -> api -> bool Lwt.t
  val add_connection_point : User.Descriptors.FDU.connection_point_descriptor -> api -> bool Lwt.t
  val remove_connection_point : string -> api -> bool Lwt.t
  val list_networks : api -> (FTypes.virtual_network list) Lwt.t
  val list_connection_points : api -> (User.Descriptors.FDU.connection_point_descriptor list) Lwt.t

end

module AtomicEntity : sig

  val onboard : User.Descriptors.AtomicEntity.descriptor -> api  -> User.Descriptors.AtomicEntity.descriptor Lwt.t
  val instantiate : string -> api -> Infra.Descriptors.AtomicEntity.record Lwt.t

end

module FDU : sig

  (* FDU descriptor *)
  val onboard : User.Descriptors.FDU.descriptor -> ?wait:bool -> api -> User.Descriptors.FDU.descriptor Lwt.t
  val offload : string -> ?wait:bool -> api -> string Lwt.t

  (* FDU instances *)
  val define : string-> string -> ?wait:bool -> api -> Infra.Descriptors.FDU.record Lwt.t
  val undefine : string -> ?wait:bool -> api -> string Lwt.t
  val configure : string -> ?wait:bool -> api -> string Lwt.t
  val clean : string -> ?wait:bool -> api -> string Lwt.t
  val start : string -> ?wait:bool -> api -> string Lwt.t
  val stop : string -> ?wait:bool -> api -> string Lwt.t
  val pause : string -> ?wait:bool -> api -> string Lwt.t
  val resume : string -> ?wait:bool -> api -> string Lwt.t
  val migrate : string -> string -> ?wait:bool -> api -> string Lwt.t
  (*  All-in-one functions  *)
  val instantiate : string -> string -> ?wait:bool -> api -> Infra.Descriptors.FDU.record  Lwt.t
  val terminate : string -> ?wait:bool -> api -> string Lwt.t

  (* Enumeration functions *)
  (* val info_node : string -> string -> api -> FDU.record  Lwt.t *)
  (* val list_node : string -> api -> (FDU.record list) Lwt.t *)
  val get_nodes : string -> api -> (string list) Lwt.t
  val instance_list : string -> ?nodeid:string -> api -> (string * (string list)) list Lwt.t
  val info : string -> api -> User.Descriptors.FDU.descriptor Lwt.t
  val instance_info : string -> api -> Infra.Descriptors.FDU.record Lwt.t
  val list : api -> (User.Descriptors.FDU.descriptor list) Lwt.t

end

module Image : sig

  val add : Base.Descriptors.FDU.image -> api -> string Lwt.t
  val remove : string -> api -> bool Lwt.t
  val list : api -> (Base.Descriptors.FDU.image list) Lwt.t

end


module Flavor : sig
  val add : Base.Descriptors.FDU.computational_requirements -> api -> string Lwt.t
  val remove : string -> api -> string Lwt.t
  val list : api -> (Base.Descriptors.FDU.computational_requirements list) Lwt.t

end

module FIMAPI : sig

  val connect : ?locator:Apero_net.Locator.t -> ?sysid:string -> ?tenantid:string -> unit -> api Lwt.t
  val close : api -> unit Lwt.t

end