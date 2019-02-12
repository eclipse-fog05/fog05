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
  val plugins : string  -> api -> (FTypes.plugin list) Lwt.t

end


module Network : sig

  val add : FTypes.network -> api -> bool Lwt.t
  val remove : string -> api -> bool Lwt.t
  val list : api -> (FTypes.network list) Lwt.t

end

module FDU : sig

  val define : FTypes.fdu -> string -> ?wait:bool -> api -> bool Lwt.t
  val undeifne : string -> string -> ?wait:bool -> api -> bool Lwt.t
  val configure : string -> string -> ?wait:bool -> api -> bool Lwt.t
  val clean : string -> string -> ?wait:bool -> api -> bool Lwt.t
  val run : string -> string -> ?wait:bool -> api -> bool Lwt.t
  val stop : string -> string -> ?wait:bool -> api -> bool Lwt.t
  val pause : string -> string -> ?wait:bool -> api -> bool Lwt.t
  val migrate : string -> string -> string -> ?wait:bool -> api -> bool Lwt.t
  val info : string -> string -> api -> FTypes.fdu  Lwt.t
  val list : ?nodeid:string -> api -> (FTypes.fdu list) Lwt.t

end

(* module Image : sig

   val add : FTypes.image_type -> api -> bool Lwt.t
   val remove : string -> api -> bool Lwt.t
   val list : api -> (FTypes.image_type list) Lwt.t

   end


   module Flavor : sig
   val add : FTypes.computational_requirements_type -> api -> bool Lwt.t
   val remove : string -> api -> bool Lwt.t
   val list : api -> (FTypes.computational_requirements_type list) Lwt.t

   end *)

module FIMAPI : sig

  val connect : ?locator:Apero_net.Locator.t -> ?sysid:string -> ?tenantid:string -> unit -> api Lwt.t
  val close : api -> unit Lwt.t

end