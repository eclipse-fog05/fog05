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
(* open Fos_im *)


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

let plugin_add nodeid descriptor _ =
  match nodeid with
  | Some _ ->
    (match descriptor with
     | Some path ->
       let _ = read_file path in
       Lwt.return_unit
     (* let res = Cli_helper.check_descriptor cont FTypesValidator.plugin_of_string FTypes.validate_plugin  in
        (match res with
        | Ok _ -> Lwt.return_unit
        (* let plugin = {(Cli_helper.load_descriptor cont FTypes.plugin_of_string) with status = Some "add"} in
         let%lwt s = FStore.create (Printf.sprintf "d%s" Cli_helper.home) Cli_helper.droot Cli_helper.dhome yserver in
         let v = (FTypes.string_of_plugins_info_type {plugins = [plugin]}) in
         Store.dput s (Printf.sprintf "%s/%s/plugins" Cli_helper.droot node_uuid) v >>= fun _ ->
         Lwt_io.printf "Plugin added\n" *)
        | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
     |None  -> Lwt_io.printf "Manifest parameter missing!!\n")
  | None ->  Lwt_io.printf "Node uuid parameter missing!!\n"


let plugin_cmd action nodeid _ descriptor =
  match action with
  | "list" -> (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= plugin_list nodeid
  | "add" -> (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= plugin_add nodeid descriptor
  | "remove" -> Lwt_io.printf "Not implemented"
  (* Missing parameter is pluginid *)
  | _ -> Lwt_io.printf "%s action not recognized!!" action

(* Node commands *)

let node_list () =
  let _ = Lwt_io.printf "Node list\n" in
  let _ = Lwt_io.printf "+---------------------------------------------+\n" in
  (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.get_all_nodes >>=
  Lwt_list.iter_p (
    fun (nid,name) ->
      Lwt_io.printf "UUID: %s \t Name: %s\n" nid name
  ) >>= fun _ ->
  Lwt_io.printf "+---------------------------------------------+\n"

let node_info nodeid =
  match nodeid with
  | Some nid ->
    let _ = Lwt_io.printf "Node info\n" in
    (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>=
    Cli_helper.get_node_info nid
    >>=
    Cli_printing.print_node_info
  | None -> Lwt_io.printf "Node uuid parameter missing!!\n"

let node_cmd action nodeid =
  match action with
  | "list" -> node_list ()
  | "info" -> node_info nodeid
  | _ -> Lwt_io.printf "%s action not recognized!!" action


(* Network commands *)

let network_add nodeid descriptor =
  match nodeid with
  | Some _ ->
    (match descriptor with
     | Some path ->
       let _ = read_file path in
       (* let res = Cli_helper.check_descriptor cont FTypes.network_of_string Types_v.validate_network  in
          (match res with
          | Ok _ -> *)
       Lwt.return_unit
     (* let descriptor = Cli_helper.load_descriptor cont FTypes.network_of_string in
        (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_add_network_node descriptor id  >>= fun _ ->
        Lwt_io.printf "Atomic Entity Defined\n"; *)
     (* | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
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

let network_cmd action descriptor netid nodeid =
  match action with
  | "add" -> network_add nodeid descriptor
  | "list" -> network_list ()
  | "remove" -> network_remove nodeid netid
  | _ -> Lwt_io.printf "%s action not recognized!!" action

(* Manifest commands *)

let descriptor_image descriptor =
  match descriptor with
  | Some path ->
    let _ = Lwt_io.printf "Check descriptor %s\n" path in
    let _ = read_file path in
    (* let res = Cli_helper.check_descriptor cont FTypes.image_of_string Types_v.validate_image  in
       (match res with
       | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
       | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
    Lwt.return_unit
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_flavor descriptor =
  match descriptor with
  | Some path ->
    let _ = Lwt_io.printf "Check descriptor %s\n" path in
    (* let cont = read_file path in
       let res = Cli_helper.check_descriptor cont FTypes.flavor_of_string Types_v.validate_flavor  in
       (match res with
       | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
       | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
    Lwt.return_unit
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_plugin descriptor =
  match descriptor with
  | Some path ->
    let _ = Lwt_io.printf "Check descriptor %s\n" path in
    (* let cont = read_file path in
       let res = Cli_helper.check_descriptor cont FTypes.plugin_of_string Types_v.validate_plugin  in
       (match res with
       | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
       | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
    Lwt.return_unit
  | None -> Lwt_io.printf"Manifest parameter is missing!!\n"

let descriptor_fdu descriptor =
  match descriptor with
  | Some path ->
    let _ = Lwt_io.printf "Check descriptor %s\n" path in
    (* let cont = read_file path in
       let res = Cli_helper.check_descriptor cont Fos_im.FTypes.fdu_of_string Fos_im.FTypesValidator.validate_fdu  in
       (match res with
       | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
       | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
    Lwt.return_unit
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_network descriptor =
  match descriptor with
  | Some _ ->
    (* let _ = Lwt_io.printf "Check descriptor %s\n" path in
       let cont = read_file path in
       let res = Cli_helper.check_descriptor cont FTypes.network_of_string Types_v.validate_network  in
       (match res with
       | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
       | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
    Lwt.return_unit
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_cmd action descriptor =
  match action with
  | "fdu" -> descriptor_fdu descriptor
  | "network" -> descriptor_network descriptor
  | "flavor" -> descriptor_flavor descriptor
  | "image" -> descriptor_image descriptor
  | _ -> Lwt_io.printf "%s is not a valid type of descriptor\n" action

(* FDU COMMANDS *)

let add_entity descriptor =
  match descriptor with
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

let atomic_entity_define nodeid descriptor =
  match nodeid with
  | Some _ ->
    (match descriptor with
     | Some _ ->
       (* let cont = read_file path in
          let res = Cli_helper.check_descriptor cont FTypes.atomic_entity_of_string Types_v.validate_atomic_entity  in
          (match res with
          | Ok _ ->
          Lwt.return_unit
          (* let descriptor = Cli_helper.load_descriptor cont FTypes.atomic_entity_of_string in
           Cli_helper.send_atomic_entity_define descriptor id (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= fun _ ->
           Lwt_io.printf "Atomic Entity Defined\n"; *)
          | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e)) *)
       Lwt.return_unit
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



let fdu_list nodeid =
  (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver)  >>=
  fun connector ->
  (match nodeid with
   | Some nid ->
     Cli_helper.get_all_node_fdus nid connector
   | None ->
     Cli_helper.get_all_node_fdus "*" connector)
  >>= fun _ -> Lwt.return_unit

let fdu_cmd action nodeid entityid instanceid destid descriptor =
  match action with
  | "list" ->
    fdu_list nodeid
  | "add" | "onboard" ->
    add_entity descriptor
  | "remove" | "offload" ->
    remove_entity entityid
  | "define" ->
    atomic_entity_define nodeid descriptor
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
        (Apero.Option.get_or_default instanceid "") (Apero.Option.get_or_default destid "") (Apero.Option.get_or_default descriptor "")
    in Lwt.return_unit



let parser component cmd action netid nodeid entityid instanceid destid descriptor =
  match String.lowercase_ascii component with
  | "fim" ->
    (match cmd with
     | "fdu" ->
       Lwt_main.run @@ fdu_cmd action nodeid entityid instanceid destid descriptor
     | "network" ->
       Lwt_main.run @@ network_cmd action descriptor netid nodeid
     | "plugin" ->
       Lwt_main.run @@ plugin_cmd action nodeid None descriptor
     | "descriptor" ->
       Lwt_main.run @@ descriptor_cmd action descriptor
     | "node" ->
       Lwt_main.run @@ node_cmd action nodeid
     | _ -> Printf.printf "%s Is not a command\n" cmd)
  | _ -> Printf.printf "%s not implemented" component


let usage = "usage: " ^ Sys.argv.(0) ^ " [node|network|descriptor|entity] "

let node_uuid_par = Arg.(value & opt (some string) None & info ["nu"] ~docv:"node uuid")
let entity_uuid_par = Arg.(value & opt (some string) None & info ["eu"] ~docv:"entity uuid")
let instance_uuid_par = Arg.(value & opt (some string) None & info ["iu"] ~docv:"instance uuid")
let dest_node_uuid_par = Arg.(value & opt (some string) None & info ["du"] ~docv:"destination uuid")
let net_uuid_par = Arg.(value & opt (some string) None & info ["net"] ~docv:"network uuid")
let descriptor_par = Arg.(value & opt (some string) None & info ["d";"descriptor"] ~docv:"descriptor file")

let act_t = Arg.(required & pos 2 (some string) None & info [] ~docv:"action")
let cmd_t = Arg.(required & pos 1 (some string) None & info [] ~docv:"type")
let component_t = Arg.(required & pos 0 (some string) None & info [] ~docv:"component [fim|faem|feo]")

let fos_t =
  Term.(
    const parser $ component_t $ cmd_t $ act_t $ net_uuid_par
    $ node_uuid_par $ entity_uuid_par $ instance_uuid_par $ dest_node_uuid_par $ descriptor_par)


let () =
  Printexc.record_backtrace true;
  Term.exit @@ Term.eval (fos_t, Term.info "fos-ng")