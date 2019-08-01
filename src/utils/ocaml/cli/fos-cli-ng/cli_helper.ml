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
open Lwt.Infix
open Fos_im
open Fos_core
open Fos_fim_api
open Fos_faem_api
open Fos_feo_api


let yaksserver =  Apero.Option.get_or_default (Sys.getenv_opt "FOS_YAKS_ENDPOINT") "tcp/127.0.0.1:7887"
let ysystem = Apero.Option.get_or_default (Sys.getenv_opt "FOS_SYS_ID") "0"
let ytenant = Apero.Option.get_or_default (Sys.getenv_opt "FOS_TENANT_ID") "0"

let yapi u = FIMAPI.connect ~locator:yaksserver ~sysid:ysystem ~tenantid:ytenant u
let faemapy u = FAEMAPI.connect ~locator:yaksserver ~sysid:ysystem ~tenantid:ytenant u
let feoapi u = FEOAPI.connect ~locator:yaksserver ~sysid:ysystem ~tenantid:ytenant u


let check_descriptor descriptor parser =
  let res =
    try
      let d = parser descriptor in
      Ok d
    with
    | e -> Error e
  in res

let load_descriptor descriptor parser =
  parser descriptor

let get_all_nodes_uuid yconnector =
  Yaks_connector.Global.Actual.get_all_nodes ysystem ytenant yconnector

let get_all_nodes yconnector =
  get_all_nodes_uuid yconnector >>=
  Lwt_list.map_p (fun e -> Yaks_connector.Global.Actual.get_node_info ysystem ytenant e yconnector)
  >>=
  Lwt_list.map_p (fun (e:FTypes.node_info option) ->
      let e  = Apero.Option.get e in
      Lwt.return (e.uuid, e.name))

let get_node_info nodeid yconnector =
  Yaks_connector.Global.Actual.get_node_info ysystem ytenant nodeid yconnector


let get_all_node_plugin node_uuid yconnector =
  Yaks_connector.Global.Actual.get_all_plugins_ids ysystem ytenant node_uuid yconnector
  >>= Lwt_list.map_p (fun e -> Yaks_connector.Global.Actual.get_plugin_info ysystem ytenant node_uuid e yconnector)

let get_plugins_by_type (all_plugins : FTypes.plugin list) (plugin_type : string) =
  List.filter (fun (e:FTypes.plugin) -> e.plugin_type = plugin_type) all_plugins

let  get_plugins_by_name (all_plugins : FTypes.plugin list) (pl_name : string) =
  List.filter (fun (e: FTypes.plugin) ->
      contains  (String.uppercase_ascii e.name) (String.uppercase_ascii pl_name)
    ) all_plugins

let get_all_node_fdus node_uuid yconnector =
  Yaks_connector.Global.Actual.get_node_fdus ysystem ytenant node_uuid yconnector

let get_all_fdus  yconnector =
  Yaks_connector.Global.Actual.get_catalog_all_fdus ysystem ytenant yconnector

(*
let get_all_networks yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/*/network/*/networks/*" aroot  in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get_all s uri
   >>= fun data ->
   Lwt_list.map_p (
   fun (k,_) ->
    let nodeid = List.nth (Fos_core.string_split '/' k) 4 in
    let net_id = List.nth (Fos_core.string_split '/' k) 8 in
    Lwt.return (nodeid, net_id)
   ) data
   >>= fun netnode_map ->
   Lwt_list.map_p (
   fun (k,v) ->
    let net_id = List.nth (Fos_core.string_split '/' k) 8 in
    Lwt.return (net_id, FTypes.network_of_string v)
   ) data
   >>= fun netmap ->
   Lwt_list.map_p (
   fun (nid, descriptor) ->
    let%lwt nodes = Lwt_list.map_p (fun (nodeid,_) -> Lwt.return nodeid) @@ List.find_all  (fun (_, netid) -> ((String.compare netid nid )==0)) netnode_map in
    Lwt.return (nid, nodes, descriptor)
   ) netmap
   >>= fun nets ->
   let comp e1 e2 =
   let n1,_,_ = e1 in
   let n2,_,_ = e2 in
   String.compare n1 n2
   in
   Lwt.return @@ List.sort_uniq comp nets
   >>= fun data ->
   FStore.destroy s >>= fun _ -> Lwt.return data *)

let get_network_info netid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/*/network/*/networks/%s" aroot netid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get_all s uri
   >>= fun data ->
   Lwt_list.map_p (
   fun (k,_) ->
    let nodeid = List.nth (Fos_core.string_split '/' k) 4 in
    let net_id = List.nth (Fos_core.string_split '/' k) 8 in
    Lwt.return (nodeid, net_id)
   ) data
   >>= fun netnode_map ->
   Lwt_list.map_p (
   fun (k,v) ->
    let net_id = List.nth (Fos_core.string_split '/' k) 8 in
    Lwt.return (net_id, FTypes.network_of_string v)
   ) data
   >>= fun netmap ->
   Lwt_list.map_p (
   fun (nid, descriptor) ->
    let%lwt nodes = Lwt_list.map_p (fun (nodeid,_) -> Lwt.return nodeid) @@ List.find_all  (fun (_, netid) -> ((String.compare netid nid )==0)) netnode_map in
    Lwt.return (nid, nodes, descriptor)
   ) netmap
   >>= fun nets ->
   let comp e1 e2 =
   let n1,_,_ = e1 in
   let n2,_,_ = e2 in
   String.compare n1 n2
   in
   Lwt.return @@ List.sort_uniq comp nets
   >>= fun data ->
   FStore.destroy s >>= fun _ -> Lwt.return @@ List.hd data *)



let get_network_node networkid nodeid yserver =
  Lwt.return_unit
(* let uri = Printf.sprintf "%s/%s/network/*/networks/%s" aroot nodeid networkid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get s uri >>= fun (_,v) ->
   Lwt.return @@ Fos_core.FTypes.network_of_string v
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)

let send_add_network_node (descriptor : Fos_core.FTypes.network) node_uuid  yserver =
  Lwt.return_unit
(* let network = { descriptor with status = Some "add"} in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   let%lwt all = get_all_node_plugin node_uuid yserver in
   let plugin = List.hd (get_plugins_by_type all "network") in
   let v =  Types_j.string_of_network network in
   FStore.put s (Printf.sprintf "%s/%s/network/%s/networks/%s" droot node_uuid plugin.uuid network.uuid) v
   >>= fun _ -> FStore.destroy s *)

let send_remove_network_node net_uuid node_uuid yserver =
  Lwt.return_unit
(* let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   let%lwt all = get_all_node_plugin node_uuid yserver in
   let plugin = List.hd (get_plugins_by_type all "network") in
   let%lwt net = get_network_node net_uuid node_uuid yserver in
   let net = {net with status = Some "undefine"} in
   FStore.put s (Printf.sprintf "%s/%s/network/%s/networks/%s" droot node_uuid plugin.uuid net_uuid) (FTypes.string_of_network net)
   >>= fun _ -> FStore.destroy s *)

let send_add_network (descriptor :Fos_core.FTypes.network) yserver =
  Lwt.return_unit
(* let descriptor = {descriptor with status = Some "add"} in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   (match descriptor.nodes with
   | Some ns ->
   Lwt_list.iter_p (fun n ->
       let%lwt all = get_all_node_plugin n yserver in
       let plugin = List.hd (get_plugins_by_type all "network") in
       let uri = Printf.sprintf "%s/%s/network/%s/networks/%s" droot n plugin.uuid descriptor.uuid in
       FStore.put s uri (Fos_core.FTypes.string_of_network descriptor))
     ns
   | None ->
   let uri = Printf.sprintf "%s/*/network/*/networks/%s" dhome descriptor.uuid in
   FStore.put s uri (Fos_core.FTypes.string_of_network descriptor))
   >>= fun _ -> FStore.destroy s *)

let send_remove_network (descriptor :Fos_core.FTypes.network) yserver =
  Lwt.return_unit
(* let descriptor = {descriptor with status = Some "undefine"} in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   (match descriptor.nodes with
   | Some ns ->
   Lwt_list.iter_p (fun n ->
       let%lwt all = get_all_node_plugin n yserver in
       let plugin = List.hd (get_plugins_by_type all "network") in
       let uri = Printf.sprintf "%s/%s/network/%s/networks/%s" droot n plugin.uuid descriptor.uuid in
       FStore.put s uri (Fos_core.FTypes.string_of_network descriptor))
     ns
   | None ->
   let uri = Printf.sprintf "%s/*/network/*/networks/%s" dhome descriptor.uuid in
   FStore.put s uri (Fos_core.FTypes.string_of_network descriptor))
   >>= fun _ -> FStore.destroy s *)

let get_entity entity_uuid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/*/onboard/%s" aroot entity_uuid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get s uri >>= fun (_,v) ->
   Lwt.return @@ Fos_core.FTypes.entity_of_string v
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)

let get_atomic_entity node_uuid handler entity_uuid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s" aroot node_uuid handler entity_uuid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get s uri >>= fun (_,v) ->
   Lwt.return @@ Fos_core.FTypes.atomic_entity_of_string v
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)

let get_atomic_entity_instances node_uuid handler entity_uuid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/*" aroot node_uuid handler entity_uuid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get_all s uri >>= fun instances ->
   Lwt.return @@ Lwt_list.map_p  (fun (k,v) -> Lwt.return (k,(Fos_core.FTypes.atomic_entity_of_string v))) instances
   >>= fun data -> let _ = FStore.destroy s in data *)


let get_flavors node_uuid yserver =
  Lwt.return []
(* let uri = match node_uuid with
   | None -> Printf.sprintf "%s/*/runtime/*/flavor/*/" aroot
   | Some s -> Printf.sprintf "%s/%s/runtime/*/flavor/*/" aroot s
   in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.resolve_all s uri >>=
   Lwt_list.map_p (fun (_,v) -> Lwt.return @@ Fos_core.FTypes.flavor_of_string v)
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)

let get_flavor_node imageid nodeid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/%s/runtime/*/flavor/%s" aroot nodeid imageid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get s uri >>= fun (_,v) ->
   Lwt.return @@ Fos_core.FTypes.flavor_of_string v
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)

let send_add_flavor_node (descriptor : Fos_core.FTypes.flavor) node_uuid yserver =
  Lwt.return_unit
(* let flavor = { descriptor with status = Some "add"} in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   let%lwt all = get_all_node_plugin node_uuid yserver in
   let plugins =get_plugins_by_name (get_plugins_by_type all "runtime ") flavor.flv_type in
   let v =  Fos_core.FTypes.string_of_flavor flavor in
   Lwt_list.iter_p (fun (e:FTypes.plugin) -> FStore.put s (Printf.sprintf "%s/%s/runtime/%s/flavor/%s" droot node_uuid e.uuid flavor.uuid) v ) plugins
   >>= fun _ -> FStore.destroy s *)

let send_remove_flavor_node flavor_uuid node_uuid yserver =
  Lwt.return_unit
(* let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   let%lwt flv = get_flavor_node flavor_uuid node_uuid yserver in
   let flv = {flv with status = Some "undefine"} in
   let%lwt all = get_all_node_plugin node_uuid yserver in
   let plugins = get_plugins_by_name (get_plugins_by_type all "runtime ") flv.flv_type in
   let v = FTypes.string_of_flavor flv in
   Lwt_list.iter_p (fun (e:FTypes.plugin) -> FStore.put s (Printf.sprintf "%s/%s/runtime/%s/flavor/%s" droot node_uuid e.uuid flavor_uuid) v ) plugins
   >>= fun _ -> FStore.destroy s *)

let get_images node_uuid yserver =
  Lwt.return []
(* let uri = match node_uuid with
   | None -> Printf.sprintf "%s/*/runtime/*/image/*/" aroot
   | Some s -> Printf.sprintf "%s/%s/runtime/*/image/*/" aroot s
   in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.resolve_all s uri
   >>= Lwt_list.map_p (fun (_ , v) -> Lwt.return @@ Fos_core.FTypes.image_of_string v)
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)


let get_image_node imageid nodeid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/%s/runtime/*/image/%s" aroot nodeid imageid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get s uri >>= fun (_,v) ->
   Lwt.return @@ Fos_core.FTypes.image_of_string v
   >>= fun data -> let _ = FStore.destroy s in Lwt.return data *)


let send_add_image_node (descriptor : Fos_core.FTypes.image) node_uuid yserver =
  Lwt.return_unit
(* let image = { descriptor with status = Some "add"} in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   let%lwt all = get_all_node_plugin node_uuid yserver in
   let plugins = (get_plugins_by_name (get_plugins_by_type all "runtime ") image.img_type) in
   let v =  Fos_core.FTypes.string_of_image image in
   Lwt_list.iter_p (fun (e:FTypes.plugin) -> FStore.put s (Printf.sprintf "%s/%s/runtime/%s/image/%s" droot node_uuid e.uuid image.uuid) v) plugins
   >>= fun _ -> FStore.destroy s *)

let send_remove_image_node image_uuid node_uuid yserver =
  Lwt.return_unit
(* let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   let%lwt img = get_image_node image_uuid node_uuid yserver in
   let img = {img with status = Some "undefine"} in
   let%lwt all = get_all_node_plugin node_uuid yserver in
   let plugins = get_plugins_by_name (get_plugins_by_type all "runtime ") img.img_type in
   let v  = FTypes.string_of_image img in
   Lwt_list.iter_p (fun (e:FTypes.plugin) -> FStore.put s (Printf.sprintf "%s/%s/runtime/%s/image/%s" droot node_uuid e.uuid image_uuid) v ) plugins
   >>= fun _ -> FStore.destroy s *)

let get_all_atomic_entities yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/*/runtime/*/entity/*" aroot  in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get_all s uri
   >>= fun data ->
   Lwt_list.map_p (
   fun (k,v) ->
    let nodeid = List.nth (Fos_core.string_split '/' k) 4 in
    let aeid = List.nth (Fos_core.string_split '/' k) 8 in
    let m = FTypes.atomic_entity_of_string v in
    Lwt.return (aeid,nodeid,m)
   ) data
   >>= fun atomic_entities_ids ->
   Lwt_list.map_p (
   fun (aeid, nid, m) ->
    let uri = Printf.sprintf "%s/*/runtime/*/entity/%s/instance/*" aroot aeid in
    let%lwt aeiids =  FStore.get_all s uri >>= Lwt_list.map_p (
        fun (k,v) ->
          let instance_id = List.nth (Fos_core.string_split '/' k) 10 in
          let m = FTypes.atomic_entity_of_string v in
          Lwt.return (instance_id,m)
      ) in
    Lwt.return (aeid,nid,m,aeiids)
   ) atomic_entities_ids
   >>= fun data ->
   FStore.destroy s >>= fun _ -> Lwt.return data *)

let get_all_atomic_entity_info atomic_entity_uuid yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/*/runtime/*/entity/%s" aroot atomic_entity_uuid  in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get s uri
   >>= fun (k,v) ->
   let nodeid = List.nth (Fos_core.string_split '/' k) 4 in
   let aeid = List.nth (Fos_core.string_split '/' k) 8 in
   let m = FTypes.atomic_entity_of_string v in
   Lwt.return (aeid,nodeid,m)
   >>=
   fun (aeid, nid, m) ->
   let uri = Printf.sprintf "%s/*/runtime/*/entity/%s/instance/*" aroot aeid in
   let%lwt aeiids =  FStore.get_all s uri >>= Lwt_list.map_p (
    fun (k,v) ->
      let instance_id = List.nth (Fos_core.string_split '/' k) 10 in
      let m = FTypes.atomic_entity_of_string v in
      Lwt.return (instance_id,m)
   ) in
   Lwt.return (aeid,nid,m,aeiids)
   >>= fun data ->
   FStore.destroy s >>= fun _ -> Lwt.return data *)

let get_all_entities yserver =
  Lwt.return []
(* let uri = Printf.sprintf "%s/%s/onboard/*" aroot "*"  in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.get_all s uri
   >>= fun data ->
   Lwt_list.map_p (
   fun (k,v) ->
    let eid = List.nth (Fos_core.string_split '/' k) 6 in
    let m = FTypes.entity_of_string v in
    Lwt.return (eid,m)
   ) data
   >>= fun entities_data ->
   Lwt_list.map_p (
   fun (eid,(m:FTypes.entity)) ->
    let%lwt nets = Lwt_list.map_p
        (fun (n:FTypes.network) ->
           get_network_info n.uuid yserver
        ) (Apero.Option.get_or_default m.networks [])
    in
    let%lwt atomics = Lwt_list.map_p
        (fun (c:FTypes.component_type) ->
           get_all_atomic_entity_info c.descriptor.uuid yserver
        ) m.components
    in
    Lwt.return (eid,m,nets, atomics)
   ) entities_data
   >>= fun data ->
   let comp e1 e2 =
   let n1,_,_,_ = e1 in
   let n2,_,_,_ = e2 in
   String.compare n1 n2
   in
   Lwt.return @@ List.sort_uniq comp data
   >>= fun data ->
   FStore.destroy s >>= fun _ -> Lwt.return data *)


let get_entity_handler_by_uuid node_uuid entity_uuid yserver =
  Lwt.return_unit
(* let uri = Printf.sprintf "%s/%s/runtime/*/entity/%s" aroot node_uuid entity_uuid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   FStore.resolve_all s uri >>=
   fun d ->
   let _ = FStore.destroy s in Lwt.return @@ List.hd (List.map (fun e -> let (k,_) = e in List.nth (Fos_core.string_split '/' k) 6) d) *)

let get_entity_handler_by_type node_uuid t yserver =
  Lwt.return_unit
(* let%lwt all = get_all_node_plugin node_uuid yserver in
   Lwt.return @@ List.hd (get_plugins_by_name all t) *)

let wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state yserver =
  Lwt.return_unit
(* let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s" aroot node_uuid handler_uuid atomic_uuid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   Unix.sleep 1;
   FStore.get s uri >>= fun (_,v) ->
   if v = "" then
   wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state yserver
   else
   match (Fos_core.FTypes.atomic_entity_of_string v).status with
   | Some data ->
    if data = state then let _ = FStore.destroy s in Lwt.return @@ Ok true else wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state yserver
   | _ -> wait_atomic_entity_state_change node_uuid handler_uuid atomic_uuid state yserver *)

let wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state yserver =
  Lwt.return_unit
(* let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" aroot node_uuid handler_uuid atomic_uuid instance_uuid in
   let%lwt s = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   Unix.sleep 1;
   FStore.get s uri >>= fun (_,v) ->
   if v = "" then wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state yserver
   else
   match (Fos_core.FTypes.atomic_entity_of_string v).status with
   | Some data -> if data = state then let _ = FStore.destroy s in Lwt.return @@ Ok true else wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state yserver
   | _ -> wait_atomic_entity_instance_state_change node_uuid handler_uuid atomic_uuid instance_uuid state yserver *)

let send_atomic_entity_define (descriptor :Fos_core.FTypes.atomic_entity) node_uuid yserver =
  Lwt.return_unit
(* let descriptor = {descriptor with status = Some "define"} in
   let%lwt handler = get_entity_handler_by_type node_uuid descriptor.atomic_type yserver in
   let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s" droot node_uuid handler.uuid descriptor.uuid in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   FStore.put s uri (Fos_core.FTypes.string_of_atomic_entity descriptor)
   >>= fun _ ->
   wait_atomic_entity_state_change node_uuid handler.uuid descriptor.uuid "defined" yserver
   >>= fun r -> FStore.destroy s >>= fun _ -> Lwt.return r *)

let send_atomic_entity_remove node_uuid entity_uuid yserver =
  Lwt.return_unit
(* let%lwt handler = get_entity_handler_by_uuid node_uuid entity_uuid yserver in
   let%lwt entityinfo = get_atomic_entity node_uuid handler entity_uuid yserver in
   let v  = FTypes.string_of_atomic_entity {entityinfo with status = Some "undefine"} in
   let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s" droot node_uuid handler entity_uuid in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   FStore.dput s uri v >>= fun _ -> FStore.destroy s *)

let send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid action state yserver =
  Lwt.return_unit
(* let%lwt handler = get_entity_handler_by_uuid node_uuid entity_uuid yserver in
   let%lwt entityinfo = get_atomic_entity node_uuid handler entity_uuid yserver in
   let v  = FTypes.string_of_atomic_entity {entityinfo with status = Some action} in
   let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" droot node_uuid handler entity_uuid instance_uuid in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   FStore.dput s uri v >>= fun _ ->
   wait_atomic_entity_instance_state_change node_uuid handler entity_uuid instance_uuid state yserver
   >>= fun r -> FStore.destroy s >>= fun _ -> Lwt.return r *)

let send_atomic_entity_instance_remove node_uuid entity_uuid instance_uuid yserver =
  Lwt.return_unit
(* let%lwt handler = get_entity_handler_by_uuid node_uuid entity_uuid yserver in
   let%lwt entityinfo = get_atomic_entity node_uuid handler entity_uuid yserver in
   let v  = FTypes.string_of_atomic_entity {entityinfo with status = Some "clean"} in
   let uri = Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" droot node_uuid handler entity_uuid instance_uuid in
   let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   FStore.dput s uri v >>= fun _ -> FStore.destroy s *)

let send_migrate_atomic_entity_instance node_uuid entity_uuid instance_uuid destination_uuid yserver =
  Lwt.return_unit
(* let%lwt sd = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
   let%lwt sa = FStore.create (Printf.sprintf "a%s" home) aroot ahome yserver in
   let%lwt  handler = get_entity_handler_by_uuid node_uuid entity_uuid yserver in
   let%lwt _,ei =  FStore.get sa (Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" aroot node_uuid handler entity_uuid instance_uuid) in
   let entity_info_src = {(FTypes.atomic_entity_of_string ei) with status=Some "taking_off"; dst=Some(destination_uuid)} in
   let entity_info_dst = {(FTypes.atomic_entity_of_string ei) with status=Some "landing"; dst=Some(destination_uuid) } in
   let%lwt destination_handler = get_entity_handler_by_type destination_uuid entity_info_dst.atomic_type yserver in
   FStore.put sd (Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" droot destination_uuid destination_handler.uuid entity_uuid instance_uuid) (Types_j.string_of_atomic_entity entity_info_dst)
   >>= fun _ ->
   FStore.put sd (Printf.sprintf "%s/%s/runtime/%s/entity/%s/instance/%s" droot node_uuid handler entity_uuid instance_uuid) (Types_j.string_of_atomic_entity entity_info_src)
   >>= fun _ ->
   wait_atomic_entity_instance_state_change destination_uuid destination_handler.uuid entity_uuid instance_uuid "run" yserver
   >>= fun _ -> FStore.destroy sa >>= fun _ -> FStore.destroy sd
   >>= fun _ -> Lwt_io.printf "Instance %s of Entity %s migrated from %s to %s\n" instance_uuid entity_uuid node_uuid destination_uuid *)

let get_node (component : FTypes.component_type) =
  match component.node with
  | Some s -> s
  | _ -> ""  (* TODO Find the correct node!! *)

let rec dedup xs =
  match xs with
  | hd::tl -> hd :: (dedup @@ List.filter (fun x -> x <> hd) tl)
  | [] -> []

let dep_graph (n: FTypes.component_type) (g: FTypes.component_type list) =
  let ds = n.need in
  List.filter (fun (x:FTypes.component_type) -> List.exists (fun a -> a = x.name) ds) g

let rec dep_order_wd (dg: FTypes.component_type list) (g: FTypes.component_type list) =
  match dg with
  | hd::tl -> (dep_order_wd (dep_graph hd g) g) @ dep_order_wd tl g @ [hd.name]
  | [] -> []

let dep_order (dg: FTypes.component_type list) = dedup @@ dep_order_wd dg dg

(* TODO check this *)
(* [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}] *)
let resolve_entity_dependencies (components : FTypes.component_type list) =
  dep_order components


let onboard path yserver =
  let m = read_file path in
  let res = check_descriptor m FTypes.entity_of_string FTypesValidator.validate_entity in
  (match res with
   | Ok _ ->
     let entity = load_descriptor m FTypes.entity_of_string in
     let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
     get_all_nodes_uuid yserver >>=
     Lwt_list.iter_p (fun e ->
         let uri = Printf.sprintf "%s/%s/onboard/%s" droot e entity.uuid in
         FStore.dput s uri m
       )
     >>= fun _ ->
     let deps = resolve_entity_dependencies entity.components in
     let%lwt _ = get_all_nodes_uuid yserver in
     let nws = match entity.networks with
       | Some l -> l
       | None -> []
     in
     Lwt_list.iter_p (fun e -> send_add_network e yserver) nws
     >>= fun _ -> Lwt_list.map_s (
       fun e ->
         let m = List.find (fun (c:FTypes.component_type) -> c.name=e) entity.components in
         let instance_uuid = Apero.Uuid.to_string @@ Apero.Uuid.make () in
         let node = get_node m in
         send_atomic_entity_define m.descriptor node yserver >>= fun _ ->
         send_atomic_entity_instance_action node m.descriptor.uuid instance_uuid "configure" "configured" yserver >>= fun _ ->
         send_atomic_entity_instance_action node m.descriptor.uuid instance_uuid "run" "run" yserver >>= fun _ ->
         Lwt.return (m.descriptor.uuid ,instance_uuid)
     ) deps
     >>= fun uuids ->
     let _ = Lwt_io.printf "\nOnboarded:\n" in
     Lwt_list.iter_p (fun (e:FTypes.network) -> Lwt_io.printf "Network %s\n" e.uuid) nws
     >>= fun _ ->
     Lwt_list.iter_p (fun (e,i) -> Lwt_io.printf "Atomic Entity %s - Instance %s\n" e i) uuids
     >>= fun _ -> FStore.destroy s
   | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))

let offload entity_id yserver =
  let%lwt s = FStore.create (Printf.sprintf "d%s" home) droot dhome yserver in
  let%lwt entity = get_entity entity_id yserver in
  Lwt_list.map_p (fun (c:FTypes.component_type) ->
      let nid = get_node c in
      let%lwt handler = get_entity_handler_by_uuid nid c.descriptor.uuid yserver in
      let%lwt insts = get_atomic_entity_instances nid handler c.descriptor.uuid yserver in
      Lwt_list.map_p (fun (k,_) ->
          Lwt.return @@ List.nth (Fos_core.string_split '/' k) 10) insts
      >>= fun ids ->
      Lwt.return (c.descriptor.uuid, nid, ids)
    ) entity.components
  >>=
  Lwt_list.iter_s (
    fun (eid,nid ,iids) ->
      Lwt_list.iter_p (fun iid ->
          send_atomic_entity_instance_action nid eid iid "stop" "stop" yserver >>= fun _ ->
          send_atomic_entity_instance_remove nid eid iid yserver >>= fun _ ->
          send_atomic_entity_remove nid eid yserver
        ) iids
  )
  >>= fun _ ->
  let nws = match entity.networks with
    | Some l -> l
    | None -> []
  in
  Lwt_list.iter_p (fun e -> send_remove_network e yserver) nws
  >>= fun _ ->
  let entity = {entity with status = Some "undefine"} in
  get_all_nodes_uuid yserver >>=
  Lwt_list.iter_p (fun e ->
      let uri = Printf.sprintf "%s/%s/onboard/%s" droot e entity.uuid in
      FStore.dput s uri (FTypes.string_of_entity entity)
    )
  >>= fun _ -> Lwt_io.printf "Entity %s offloaded\n" entity_id
  >>= fun _ -> FStore.destroy s *)