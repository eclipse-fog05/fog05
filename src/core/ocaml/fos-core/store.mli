(*********************************************************************************
 * Copyright (c) 2018 ADLINK Technology Inc. 
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
 * which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 * Contributors: 1
 *   Gabriele Baldoni (gabriele (dot) baldoni (at) adlinktech (dot) com ) - OCaml implementation
 *********************************************************************************)

type state

type t

(* type store_value *)

val create : string -> string -> string  -> string -> t Lwt.t

val put : t -> string -> string -> unit Lwt.t

val dput : t -> string -> string -> unit Lwt.t

val get : t -> string -> (string * string) Lwt.t

val get_all : t -> string -> ((string * string) list) Lwt.t

val resolve_all : t -> string -> ((string * string) list) Lwt.t

val remove : t -> string -> unit Lwt.t

val destroy : t -> unit Lwt.t