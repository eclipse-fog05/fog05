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

open Yaks_ocaml
open Lwt.Infix

module MVar = Apero.MVar_lwt

type state = {
  sid : string
; root : string
; home : string
; ylocator : Apero_net.Locator.t
; yapi : Yaks.t
; yworkspace : Yaks.Workspace.t
}

type t = state MVar.t


(* UTILITY FUNCTIONS *)

let update key f (json : Yojson.Basic.json) =
  let rec update_json_obj = function
    | [] ->
      begin match f None with
        | None -> []
        | Some v -> [(key, v)]
      end
    | ((k, v) as m) :: tl ->
      if k = key then
        match f (Some v) with
        | None -> update_json_obj tl
        | Some v' ->
          if v' == v then m :: tl
          else (k, v') :: tl
      else m :: (update_json_obj tl)
  in
  match json with
  | `Assoc obj -> `Assoc (update_json_obj obj)
  | _ -> json


let add k v = update k (fun _ -> Some v) 
(* let remove k = update k (fun _ -> None) *)


let rec merge lst o1 o2 = 
  match lst with
  | [] -> o1
  | h::t ->
    match List.find_opt (fun bk -> bk==h) (Yojson.Basic.Util.keys o1) with
    | None -> 
      merge t (add h (Yojson.Basic.Util.member h o2) o1) o2 
    | Some _ -> 
      match o1 with
      | `Assoc _ -> 
        merge t (update h (fun _ -> Some (merge t (Yojson.Basic.Util.member h o1) (Yojson.Basic.Util.member h o2))) o1) o2
      | _ ->
        merge t (update h (fun _ -> Some o2) o1) o2

let data_merge old_json updated_json = 
  merge (Yojson.Basic.Util.keys updated_json) old_json updated_json

(* ################# *)


let create store_id  store_root  store_home yaks_ip =
  let locator = Apero.Option.get @@ Apero_net.Locator.of_string @@ Printf.sprintf "tcp/%s:7887" yaks_ip in
  let%lwt yapi = Yaks.login locator Apero.Properties.empty in
  let%lwt yworkspace = Yaks.workspace (Yaks_types.Path.of_string store_root) yapi in
  let s = {sid = store_id ; root = store_root; home = store_home; ylocator = locator; yapi; yworkspace} in
  let store = MVar.create s in
  Lwt.return store

let put store key value =
  MVar.read store >>= fun state ->
  let selector = Yaks_types.Path.of_string key in
  let value = (Apero.Result.get (Yaks_types.Value.of_string value Yaks_types.Value.Raw_Encoding)) in
  Yaks.Workspace.put selector value state.yworkspace

let get store key =
  MVar.read store 
  >>= fun state ->
  let selector = Yaks_types.Selector.of_string key in
  Yaks.Workspace.get selector state.yworkspace
  >>= fun data ->
  match List.length data with
  | 0 -> 
    Lwt.return (key, "")
  | _ ->
    let p,v = List.hd data in 
    Lwt.return (Yaks_types.Path.to_string p, Yaks_types.Value.to_string v)

let remove store key =
  MVar.read store >>= fun state ->
  let selector = Yaks_types.Path.of_string key in
  Yaks.Workspace.remove selector state.yworkspace


let get_all store key =
  MVar.read store 
  >>= fun state ->
  let selector = Yaks_types.Selector.of_string key in
  Yaks.Workspace.get selector state.yworkspace 
  >>= Lwt_list.map_p (fun (p,v) -> Lwt.return (Yaks_types.Path.to_string p, Yaks_types.Value.to_string v))

let resolve_all store key =
  get_all store key


let dput store key value =
  get store key 
  >>= fun values ->
  let _,v = values in 
  if v == "" then
    put store key value 
    >>= fun _ -> 
    Lwt.return_unit
  else
    let base = Yojson.Basic.from_string v in
    let updates = Yojson.Basic.from_string value in
    let result = data_merge base updates in
    put store key (Yojson.Basic.to_string result) 
    >>= fun _ -> 
    Lwt.return_unit


let destroy store = 
  MVar.guarded store @@ fun state ->
  (* Yaks. state.yworkspace state.yapi 
     >>= fun _ -> *)
  Yaks.logout state.yapi
  >>= fun _ ->
  MVar.return () state
