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

open Cmdliner
open Lwt.Infix
open Fos_core
(* open Types_t *)

(*   ignore @@ initialize (); *)
(* >outfile 2> errfile & echo $! > pid file *)
(* "-p"; "9876"; *)

let check s =
  let n = String.length s in
  if n > 0 && s.[n-1] = '\n' then
    String.sub s 0 (n-1)
  else
    s

(* Plugin command *)

let plugin_list nodeid yconnector =
  match nodeid with
  | Some node_uuid ->
    Cli_helper.get_all_node_plugin node_uuid yconnector >>=
    fun d -> Cli_printing.print_node_plugin d
  | None -> Lwt_io.printf "Node uuid parameter missing!!\n"

let plugin_add nodeid manifest _ =
  match nodeid with
  | Some _ ->
    (match manifest with
     | Some path ->
       let cont = read_file path in
       let res = Cli_helper.check_manifest cont Types_j.plugin_of_string Types_v.validate_plugin  in
       (match res with
        | Ok _ -> Lwt.return_unit
        (* let plugin = {(Cli_helper.load_manifest cont Types_j.plugin_of_string) with status = Some "add"} in
           let%lwt s = FStore.create (Printf.sprintf "d%s" Cli_helper.home) Cli_helper.droot Cli_helper.dhome yserver in
           let v = (Types_j.string_of_plugins_info_type {plugins = [plugin]}) in
           Store.dput s (Printf.sprintf "%s/%s/plugins" Cli_helper.droot node_uuid) v >>= fun _ ->
           Lwt_io.printf "Plugin added\n" *)
        | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
     |None  -> Lwt_io.printf "Manifest parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"


let plugin_cmd action nodeid _ manifest =
  match action with
  | "list" -> (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= plugin_list nodeid
  | "add" -> (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= plugin_add nodeid manifest
  | "remove" -> Lwt_io.printf "Not implemented"
  (* Missing parameter is pluginid *)
  | _ -> Lwt_io.printf "%s action not recognized!!" action

(* Node commands *)

let node_list () =
  let _ = Lwt_io.printf "Node list\n" in
  let _ = Lwt_io.printf "+---------------------------------------------+\n" in
  (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.get_all_nodes >>=
  Lwt_list.iter_p (
    fun (_,n) ->
      let node_info = FTypesJson.node_info_of_string n in
      Lwt_io.printf "UUID: %s \t Name: %s\n" node_info.uuid node_info.name
  ) >>= fun _ ->
  Lwt_io.printf "+---------------------------------------------+\n"

let node_info nodeid =
  match nodeid with
  | Some _ ->
    Lwt.return_unit
  (* let _ = Lwt_io.printf "Node info\n" in
     let%lwt s = Store.create (Printf.sprintf "a%s" Cli_helper.home) Cli_helper.aroot Cli_helper.ahome (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) in
     Store.get s (Printf.sprintf "%s/%s" Cli_helper.aroot node_uuid) >>= fun res ->
     (match res with
     | _,v -> let node_info = Types_j.node_info_of_string v in
     Cli_printing.print_node_info node_info
     ) *)
  | None -> Lwt_io.printf "Node uuid parameter missing!!\n"

let node_cmd action nodeid =
  match action with
  | "list" -> node_list ()
  | "info" -> node_info nodeid
  | _ -> Lwt_io.printf "%s action not recognized!!" action


(* Network commands *)

let network_add nodeid manifest =
  match nodeid with
  | Some _ ->
    (match manifest with
     | Some path ->
       let cont = read_file path in
       let res = Cli_helper.check_manifest cont Types_j.network_of_string Types_v.validate_network  in
       (match res with
        | Ok _ ->
          Lwt.return_unit
        (* let manifest = Cli_helper.load_manifest cont Types_j.network_of_string in
           (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_add_network_node manifest id  >>= fun _ ->
           Lwt_io.printf "Atomic Entity Defined\n"; *)
        | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
     |None  -> Lwt_io.printf "Manifest parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"


let network_remove nodeid netid =
  match nodeid with
  | Some _ ->
    (match netid with
     | Some _ ->
       Lwt.return_unit
     (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_remove_network_node net_uuid node_uuid >>= fun _ ->
        Lwt_io.printf "Removed network %s from node  %s\n" net_uuid node_uuid *)
     | None -> Lwt_io.printf "Atomic Entity uuid parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"

let network_list () =
  Lwt.return_unit
(*
  (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.get_all_networks  >>= Cli_printing.print_networks *)

let network_cmd action manifest netid nodeid =
  match action with
  | "add" -> network_add nodeid manifest
  | "list" -> network_list ()
  | "remove" -> network_remove nodeid netid
  | _ -> Lwt_io.printf "%s action not recognized!!" action

(* Manifest commands *)

let manifest_image manifest =
  match manifest with
  | Some path ->
    let _ = Lwt_io.printf "Check manifest %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_manifest cont Types_j.image_of_string Types_v.validate_image  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let manifest_flavor manifest =
  match manifest with
  | Some path ->
    let _ = Lwt_io.printf "Check manifest %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_manifest cont Types_j.flavor_of_string Types_v.validate_flavor  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let manifest_plugin manifest =
  match manifest with
  | Some path ->
    let _ = Lwt_io.printf "Check manifest %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_manifest cont Types_j.plugin_of_string Types_v.validate_plugin  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf"Manifest parameter is missing!!\n"

let manifest_entity manifest =
  match manifest with
  | Some path ->
    let _ = Lwt_io.printf "Check manifest %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_manifest cont Types_j.entity_of_string Types_v.validate_entity  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let manifest_atomic_entity manifest =
  match manifest with
  | Some path ->
    let _ = Lwt_io.printf "Check manifest %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_manifest cont Types_j.atomic_entity_of_string Types_v.validate_atomic_entity  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let manifest_network manifest =
  match manifest with
  | Some path ->
    let _ = Lwt_io.printf "Check manifest %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_manifest cont Types_j.network_of_string Types_v.validate_network  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let manifest_cmd action manifest =
  match action with
  | "network" -> manifest_network manifest
  | "aentity" -> manifest_atomic_entity manifest
  | "entity" -> manifest_entity manifest
  | "plugin" -> manifest_plugin manifest
  | "flavor" -> manifest_flavor manifest
  | "image" -> manifest_image manifest
  | _ -> Lwt_io.printf "%s is not a valid type of manifest\n" action

(* ENTITY COMMANDS *)

let add_entity manifest =
  match manifest with
  | Some _ ->
    Lwt.return_unit
  (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.onboard path *)
  | None -> Lwt_io.printf "Manifest parameter missing!!\n"

let remove_entity entityid =
  match entityid with
  | Some _ ->
    Lwt.return_unit
  (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.offload id *)
  | None -> Lwt_io.printf "Entity uuid parameter missing!!\n"

let atomic_entity_define nodeid manifest =
  match nodeid with
  | Some _ ->
    (match manifest with
     | Some path ->
       let cont = read_file path in
       let res = Cli_helper.check_manifest cont Types_j.atomic_entity_of_string Types_v.validate_atomic_entity  in
       (match res with
        | Ok _ ->
          Lwt.return_unit
        (* let manifest = Cli_helper.load_manifest cont Types_j.atomic_entity_of_string in
           Cli_helper.send_atomic_entity_define manifest id (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= fun _ ->
           Lwt_io.printf "Atomic Entity Defined\n"; *)
        | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
     |None  -> Lwt_io.printf "Manifest parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"

let atomic_entity_undefine nodeid entityid =
  match nodeid with
  | Some _ ->
    (match entityid with
     | Some _ ->
       Lwt.return_unit
     (* let _ = Lwt_io.printf "Undefine entity %s from node %s" entity_uuid node_uuid in
        let%lwt _ = Cli_helper.send_atomic_entity_remove node_uuid entity_uuid (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) in
        Lwt_io.printf "Atomic Entity Removed\n"; *)
     | None -> Lwt_io.printf "Atomic Entity uuid parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"

let atomic_entity_clean nodeid entityid instanceid =
  match nodeid with
  | Some _ ->
    (match entityid with
     | Some _ ->
       (match instanceid with
        | Some _ ->
          Lwt.return_unit
        (* let _ = Lwt_io.printf "Clean instance %s entity %s from node %s\n" instance_uuid entity_uuid node_uuid in
           let%lwt _ = Cli_helper.send_atomic_entity_instance_remove node_uuid entity_uuid instance_uuid (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) in
           Lwt_io.printf "Atomic Entity Cleaned\n"; *)
        | None -> Lwt_io.printf "Instance uuid parameter missing!!\n")
     | None -> Lwt_io.printf "Atomic Entity uuid parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"

let atomic_entity_change_state nodeid entityid instanceid _ _  =
  match nodeid with
  | Some _ ->
    (match entityid with
     | Some _ ->
       (match instanceid with
        | Some _ ->
          Lwt.return_unit
        (* let _ = Lwt_io.printf "Configure entity %s with instance %s to node %s\n" entity_uuid instance_uuid node_uuid in
           let%lwt _ = Cli_helper.send_atomic_entity_instance_action node_uuid entity_uuid instance_uuid action newstate (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) in
           Lwt_io.printf "Atomic Entity Configured\n"; *)
        | None -> Lwt_io.printf "Instance uuid parameter missing!!\n")
     | None -> Lwt_io.printf "Atomic Entity uuid parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"


let atomic_entity_migrate nodeid entityid instanceid destinationid  =
  match nodeid with
  | Some _ ->
    (match entityid with
     | Some _ ->
       (match instanceid with
        | Some _ ->
          (match destinationid with
           |Some _ ->
             Lwt.return_unit
           (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_migrate_atomic_entity_instance node_uuid entity_uuid instance_uuid destination_node *)
           |None -> Lwt_io.printf "Destination Node uuid parameter missing!!\n")
        | None -> Lwt_io.printf "Instance uuid parameter missing!!\n")
     | None -> Lwt_io.printf "Atomic Entity uuid parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"

let atomic_entity_list () =
  Lwt.return_unit
(* Cli_helper.get_all_atomic_entities (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_printing.print_atomic_entities *)

let entity_list () =
  Lwt.return_unit
(* Cli_helper.get_all_entities (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_printing.print_entities *)

let entity_cmd action nodeid entityid instanceid destid manifest =
  match action with
  | "list" ->
    entity_list ()
  | "atomic-list" ->
    atomic_entity_list ()
  | "add" | "onboard" ->
    add_entity manifest
  | "remove" | "offload" ->
    remove_entity entityid
  | "define" ->
    atomic_entity_define nodeid manifest
  | "configure" ->
    atomic_entity_change_state nodeid entityid instanceid action "configured"
  | "run" ->
    atomic_entity_change_state nodeid entityid instanceid action "run"
  | "stop" ->
    atomic_entity_change_state nodeid entityid instanceid action "stop"
  | "pause" ->
    atomic_entity_change_state nodeid entityid instanceid action "pause"
  | "resume" ->
    atomic_entity_change_state nodeid entityid instanceid action "run"
  | "clean" ->
    atomic_entity_clean nodeid entityid instanceid
  | "undefine" ->
    atomic_entity_undefine nodeid entityid
  | "migrate" ->
    atomic_entity_migrate nodeid entityid instanceid destid
  | _ ->
    let _ = Lwt_io.printf "%s action not recognized!!" action in
    let _ = Lwt_io.printf "action: %s parameters  %s %s %s %s %s %s\n"
        action   (Apero.Option.get_or_default nodeid "") (Apero.Option.get_or_default entityid "")
        (Apero.Option.get_or_default instanceid "") (Apero.Option.get_or_default destid "") (Apero.Option.get_or_default manifest "")
    in Lwt.return_unit



let parser cmd action netid nodeid entityid instanceid destid manifest =
  match cmd with
  | "fdu" ->
    Lwt_main.run @@ entity_cmd action nodeid entityid instanceid destid manifest
  | "network" ->
    Lwt_main.run @@ network_cmd action manifest netid nodeid
  | "plugin" ->
    Lwt_main.run @@ plugin_cmd action nodeid None manifest
  | "manifest" ->
    Lwt_main.run @@ manifest_cmd action manifest
  | "node" ->
    Lwt_main.run @@ node_cmd action nodeid
  | _ -> Printf.printf "%s Is not a command\n" cmd


let usage = "usage: " ^ Sys.argv.(0) ^ " [node|network|manifest|entity] "

let node_uuid_par = Arg.(value & opt (some string) None & info ["nu"] ~docv:"node uuid")
let entity_uuid_par = Arg.(value & opt (some string) None & info ["eu"] ~docv:"entity uuid")
let instance_uuid_par = Arg.(value & opt (some string) None & info ["iu"] ~docv:"instance uuid")
let dest_node_uuid_par = Arg.(value & opt (some string) None & info ["du"] ~docv:"destination uuid")
let net_uuid_par = Arg.(value & opt (some string) None & info ["net"] ~docv:"network uuid")
let manifest_par = Arg.(value & opt (some string) None & info ["m";"manifest"] ~docv:"manifest file")

let act_t = Arg.(required & pos 1 (some string) None & info [] ~docv:"action")
let cmd_t = Arg.(required & pos 0 (some string) None & info [] ~docv:"type")

let fos_t =
  Term.(
    const parser $ cmd_t $ act_t $ net_uuid_par
    $ node_uuid_par $ entity_uuid_par $ instance_uuid_par $ dest_node_uuid_par $ manifest_par)


let () =
  Printexc.record_backtrace true;
  Term.exit @@ Term.eval (fos_t, Term.info "fos-ng")