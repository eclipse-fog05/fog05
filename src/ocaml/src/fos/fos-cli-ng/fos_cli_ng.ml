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
open Fos_im
open Fos_fim_api

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
let node_cmd api action nodeid =
  match action with
  | "list" ->
    let print_node (n:FTypes.node_info) =
      Lwt_io.printf "Node ID: %s Hostname: %s\n" n.uuid n.name
    in
    Node.list api >>= Lwt_list.iter_p print_node
  | "info" ->
    (match nodeid with
     | Some nid ->
       let print_node (n:FTypes.node_info) =
         Lwt_io.printf "Node ID: %s Info: %s\n" n.uuid (FTypes.string_of_node_info n)
       in
       Node.info nid api >>= print_node
     | None -> Lwt_io.print "Missing Node UUID paratemer!")
  | "plugins" ->
    (match nodeid with
     | Some nid ->
       let print_plugin (p:FTypes.plugin) =
         Lwt_io.printf "Plugin ID: %s  Name: %s Type: %s Info: %s\n" p.uuid p.name p.plugin_type (FTypes.string_of_plugin p)
       in
       Lwt_io.printf "Node ID: %s" nid >>= fun _ ->
       Node.plugins nid api >>= Lwt_list.iter_p print_plugin
     | None -> Lwt_io.print "Missing Node UUID paratemer!")
  | _ -> Lwt_io.printf "Action %s not recognized" action


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

let add_fdu_descriptor_to_catalog api (descriptor:string option) =
  match descriptor with
  | Some dp ->
    let d = read_file dp in
    let fdu = FTypes.fdu_of_string d in
    FDU.onboard fdu api >>= fun res ->
    (match res with
     | true -> Lwt_io.printf "Descriptor Onboarder!\n"
     | false -> Lwt_io.printf "Error while onboarding the descriptor\n")
  (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.onboard path *)
  | None -> Lwt_io.printf "Manifest parameter missing!!\n"

let remove_fdu_descriptor_from_catalog api fduid =
  match fduid with
  | Some id ->
    FDU.offload id api >>=  fun res ->
    (match res with
     | true -> Lwt_io.printf "Descriptor Removed!\n"
     | false -> Lwt_io.printf "Error while removing the descriptor\n")
  (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.offload id *)
  | None -> Lwt_io.printf "Entity uuid parameter missing!!\n"

let fdu_define api fduid nodeid =
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.define fid nid api >>= fun res ->
       (match res with
        | true -> Lwt_io.printf "FDU Defined!\n"
        | false -> Lwt_io.printf "Error while defining FDU\n")
     | None  -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"

let fdu_undefine api fduid nodeid =
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.undeifne fid nid api >>= fun res ->
       (match res with
        | true -> Lwt_io.printf "FDU Undefined!\n"
        | false -> Lwt_io.printf "Error while undefining FDU\n")
     | None -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"

(* let fdu_clean api fduid nodeid instanceid =
   match nodeid with
   | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.clean fid nid api >>= fun res ->
       (match res with
        | true -> Lwt_io.printf "FDU Cleaned!"
        | false -> Lwt_io.printf "Error while clean FDU")
     | None -> Lwt_io.printf "Atomic Entity uuid parameter missing!!\n")
   | None ->  Lwt_io.printf "Node uuid parameter missing!!\n" *)

let fdu_state_change api fduid nodeid state  =
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       (
         let api_func =
           match state with
           | `CONDIFURE -> FDU.configure
           | `CLEAN -> FDU.clean
           | `RUN -> FDU.run
           | `STOP -> FDU.stop
           | `PAUSE -> FDU.pause
           | _ -> fun _ _ ?(wait=true) _ -> ignore wait; Lwt.return_false
         in
         api_func fid nid api >>= fun res ->
         (match res with
          | true -> Lwt_io.printf "FDU State Update!\n"
          | false -> Lwt_io.printf "Error while updating FDU state\n")
       )
     | None -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"


let fdu_migrate fduid nodeid destinationid  =
  match nodeid with
  | Some _ ->
    (match fduid with
     | Some _ ->
       (match destinationid with
        |Some _ ->
          Lwt.return_unit
        (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_migrate_atomic_entity_instance node_uuid entity_uuid instance_uuid destination_node *)
        |None -> Lwt_io.printf "Destination Node UUID parameter missing!!\n")
     | None -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"



let fdu_list api nodeid =
  match nodeid with
  | Some nid ->
    let print_fdu (f:FTypesRecord.fdu) =
      Lwt_io.printf "FDU ID: %s Descriptor %s\n" f.fdu_uuid (FTypesRecord.string_of_fdu f)
    in
    FDU.list_node nid api >>=
    Lwt_list.iter_p print_fdu
  | None ->
    let print_fdu (f:FTypes.fdu) =
      Lwt_io.printf "FDU ID: %s Descriptor %s\n" f.uuid (FTypes.string_of_fdu f)
    in
    FDU.list api >>=
    Lwt_list.iter_p print_fdu
    >>= fun _ -> Lwt.return_unit

let fdu_cmd api action nodeid fduid destid descriptor =
  match action with
  | "list" ->
    fdu_list api nodeid
  |  "onboard" ->
    add_fdu_descriptor_to_catalog api descriptor
  | "offload" ->
    remove_fdu_descriptor_from_catalog api fduid
  | "define" ->
    fdu_define api fduid nodeid
  | "configure" ->
    fdu_state_change api fduid nodeid `CONFIGURE
  | "run" ->
    fdu_state_change api fduid nodeid `RUN
  | "stop" ->
    fdu_state_change api fduid nodeid `STOP
  | "pause" ->
    fdu_state_change api fduid nodeid `PAUSE
  | "resume" ->
    fdu_state_change api fduid nodeid `RUN
  | "clean" ->
    fdu_state_change  api fduid nodeid `CLEAN
  | "undefine" ->
    fdu_undefine api fduid nodeid
  | "migrate" ->
    fdu_migrate nodeid fduid destid
  | _ ->
    let _ = Lwt_io.printf "%s action not recognized!!\n" action in
    let _ = Lwt_io.printf "action: %s parameters  %s %s %s %s %s\n"
        action   (Apero.Option.get_or_default nodeid "") (Apero.Option.get_or_default fduid "") (Apero.Option.get_or_default destid "") (Apero.Option.get_or_default descriptor "")
    in Lwt.return_unit



let parser component cmd action netid nodeid fduid destid descriptor =
  let%lwt fimapi = Cli_helper.yapi () in
  match String.lowercase_ascii component with
  | "fim" ->
    (match cmd with
     | "fdu" ->
       fdu_cmd fimapi action nodeid fduid destid descriptor
     | "network" ->
       network_cmd action descriptor netid nodeid
     | "plugin" ->
       plugin_cmd action nodeid None descriptor
     | "descriptor" ->
       descriptor_cmd action descriptor
     | "node" ->
       node_cmd fimapi action nodeid
     | _ -> Lwt_io.printf "%s Is not a command\n" cmd)
  | _ -> Lwt_io.printf "%s not implemented\n" component


let p1 component cmd action netid nodeid fduid destid descriptor =
  Lwt_main.run @@ parser component cmd action netid nodeid fduid destid descriptor

let usage = "usage: " ^ Sys.argv.(0) ^ " [node|network|descriptor|entity] "

let node_uuid_par = Arg.(value & opt (some string) None & info ["nu"] ~docv:"node uuid")
let fdu_uuid_par = Arg.(value & opt (some string) None & info ["fu"] ~docv:"entity uuid")
let dest_node_uuid_par = Arg.(value & opt (some string) None & info ["du"] ~docv:"destination uuid")
let net_uuid_par = Arg.(value & opt (some string) None & info ["net"] ~docv:"network uuid")
let descriptor_par = Arg.(value & opt (some string) None & info ["d";"descriptor"] ~docv:"descriptor file")

let act_t = Arg.(required & pos 2 (some string) None & info [] ~docv:"action")
let cmd_t = Arg.(required & pos 1 (some string) None & info [] ~docv:"type")
let component_t = Arg.(required & pos 0 (some string) None & info [] ~docv:"component [fim|faem|feo]")

let fos_t =
  Term.(
    const p1 $ component_t $ cmd_t $ act_t $ net_uuid_par
    $ node_uuid_par $ fdu_uuid_par  $ dest_node_uuid_par $ descriptor_par)


let () =
  Printexc.record_backtrace true;
  Term.exit @@ Term.eval (fos_t, Term.info "fos-ng")