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
open Fos_errors


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
  | "remove" -> Lwt_io.printf "Not implemented\n"
  (* Missing parameter is pluginid *)
  | _ -> Lwt_io.printf "%s action not recognized!!\n" action

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
     | None -> Lwt_io.print "Missing Node UUID paratemer!\n")
  | "status" ->
    (match nodeid with
     | Some nid ->
       let print_node (n:FTypes.node_status) =
         Lwt_io.printf "Node ID: %s Status: %s\n" n.uuid (FTypes.string_of_node_status n)
       in
       Node.status nid api >>= print_node
     | None -> Lwt_io.print "Missing Node UUID paratemer!\n")
  | "plugins" ->
    (match nodeid with
     | Some nid ->
       let print_plugin (p:FTypes.plugin) =
         Lwt_io.printf "Plugin ID: %s  Name: %s Type: %s Info: %s\n" p.uuid p.name p.plugin_type (FTypes.string_of_plugin p)
       in
       Lwt_io.printf "Node ID: %s" nid >>= fun _ ->
       Node.plugins nid api >>= Lwt_list.iter_p print_plugin
     | None -> Lwt_io.print "Missing Node UUID paratemer!\n")
  | _ -> Lwt_io.printf "Action %s not recognized\n" action


(* Network commands *)

let network_add api descriptor =
  match descriptor with
  | Some path ->
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont FTypes.virtual_network_of_string  in
    (match res with
     | Ok descriptor ->
       Network.add_network descriptor api
       >>= fun _-> Lwt_io.printf "%s\n" descriptor.uuid
     | Error e -> Lwt_io.printf "Desriptor has errors: %s\n" (Printexc.to_string e))
  |None  -> Lwt_io.printf "Desriptor parameter missing!!\n"


let network_remove api netid =
  match netid with
  | Some netid ->
    Network.remove_network netid api
    >>= fun _ -> Lwt_io.printf "%s\n" netid
  | None -> Lwt_io.printf "Network uuid parameter missing!!\n"

let network_list api =
  Network.list_networks api >>= Cli_printing.print_networks


let network_cmd api action descriptor netid =
  match action with
  | "add" -> network_add api descriptor
  | "list" -> network_list api
  | "remove" -> network_remove api netid
  | _ -> Lwt_io.printf "%s action not recognized!!" action


(* Image commands *)

let image_add api descriptor =
  match descriptor with
  | Some path ->
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Fos_im.FDU.image_of_string in
    (match res with
     | Ok descriptor ->
       Image.add descriptor api >>= Lwt_io.printf "%s\n"
     | Error e -> Lwt_io.printf "Desriptor has errors: %s\n" (Printexc.to_string e))
  |None  -> Lwt_io.printf "Desriptor parameter missing!!\n"


let image_remove api imgid =
  match imgid with
  | Some imgid ->
    Image.remove imgid api
    >>= fun _ -> Lwt_io.printf "%s\n" imgid
  | None -> Lwt_io.printf "Image uuid parameter missing!!\n"

let image_list api =
  Image.list api >>= Cli_printing.print_images


let image_cmd api action descriptor imgid =
  match action with
  | "add" -> image_add api descriptor
  | "list" -> image_list api
  | "remove" -> image_remove api imgid
  | _ -> Lwt_io.printf "%s action not recognized!!" action


(* Manifest commands *)

let descriptor_image descriptor =
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Fos_im.FDU.image_of_string  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_flavor descriptor =
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Fos_im.FDU.computational_requirements_of_string  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_fdu descriptor =
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Fos_im.FDU.descriptor_of_string in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_network descriptor =
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont FTypes.network_of_string  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
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
    let fdu = Fos_im.FDU.descriptor_of_string d in
    FDU.onboard fdu api  >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "Manifest parameter missing!!\n"

let remove_fdu_descriptor_from_catalog api fduid =
  match fduid with
  | Some id ->
    FDU.offload id api  >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "Entity uuid parameter missing!!\n"

let fdu_define api fduid nodeid =
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.define fid nid api >>= fun res ->
       Lwt_io.printf "%s\n" res
     | None  -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"

let fdu_undefine api instanceid =
  match instanceid with
  | Some iid ->
    FDU.undefine iid api >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"


let fdu_instantiate api fduid nodeid =
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.instantiate fid nid api >>= fun res ->
       Lwt_io.printf "%s\n" res
     | None  -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"

let fdu_terminate api instanceid =
  match instanceid with
  | Some iid ->
    FDU.terminate iid api >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"


let fdu_instances api fduid nodeid =
  match fduid with
  | Some fduid ->
    (match nodeid with
     | Some nid -> FDU.instance_list fduid ~nodeid:nid api
     | None -> FDU.instance_list fduid api  )
    >>=
    Cli_printing.print_fdu_instances
  | None -> Lwt_io.printf "FDU UUID parameter missing!!\n"

let fdu_state_change api instanceid state  =
  match instanceid with
  | Some iid ->
    (
      let api_func =
        match state with
        | `CONFIGURE -> FDU.configure
        | `CLEAN -> FDU.clean
        | `RUN -> FDU.start
        | `STOP -> FDU.stop
        | `PAUSE -> FDU.pause
        | _ -> raise @@ FException (`InternalError (`Msg ("Action not legal")))
      in
      api_func iid api >>= fun res ->
      Lwt_io.printf "%s\n" res
    )
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"

let fdu_migrate instanceid destinationid  =
  match instanceid with
  | Some _ ->
    (match destinationid with
     |Some _ ->
       Lwt.return_unit
     (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_migrate_atomic_entity_instance node_uuid entity_uuid instance_uuid destination_node *)
     |None -> Lwt_io.printf "Destination Node UUID parameter missing!!\n")
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"



let fdu_list api =
  let print_fdu (f:Fos_im.FDU.descriptor) =
    Lwt_io.printf "FDU ID: %s Descriptor %s\n" (Apero.Option.get f.uuid) (Fos_im.FDU.string_of_descriptor f)
  in
  FDU.list api >>=
  Lwt_list.iter_p print_fdu
  >>= fun _ -> Lwt.return_unit

let fdu_cmd api action nodeid fduid instanceid destid descriptor =
  match action with
  | "list" ->
    fdu_list api
  |  "onboard" ->
    add_fdu_descriptor_to_catalog api descriptor
  | "offload" ->
    remove_fdu_descriptor_from_catalog api fduid
  | "define" ->
    fdu_define api fduid nodeid
  | "configure" ->
    fdu_state_change api instanceid `CONFIGURE
  | "start" ->
    fdu_state_change api instanceid `RUN
  | "stop" ->
    fdu_state_change api instanceid `STOP
  | "pause" ->
    fdu_state_change api instanceid `PAUSE
  | "resume" ->
    fdu_state_change api instanceid `RUN
  | "clean" ->
    fdu_state_change  api instanceid `CLEAN
  | "undefine" ->
    fdu_undefine api instanceid
  | "migrate" ->
    fdu_migrate instanceid destid
  | "instantiate" ->
    fdu_instantiate api fduid nodeid
  | "terminate" ->
    fdu_terminate api instanceid
  | "instances" ->
    fdu_instances api fduid nodeid
  | _ ->
    let%lwt _ = Lwt_io.printf "%s action not recognized!!\n" action in
    let%lwt _ = Lwt_io.printf "action: %s parameters  Node %s FDU %s dest %s descr %s instance %s\n"
        action  (Apero.Option.get_or_default nodeid "") (Apero.Option.get_or_default fduid "") (Apero.Option.get_or_default destid "") (Apero.Option.get_or_default descriptor "") (Apero.Option.get_or_default instanceid "")
    in Lwt.return_unit



let parser component cmd action netid imgid nodeid fduid instanceid destid descriptor =
  let%lwt fimapi = Cli_helper.yapi () in
  match String.lowercase_ascii component with
  | "fim" ->
    (match cmd with
     | "fdu" ->
       fdu_cmd fimapi action nodeid fduid instanceid destid descriptor
     | "network" ->
       network_cmd fimapi action descriptor netid
     | "plugin" ->
       plugin_cmd action nodeid None descriptor
     | "image" ->
       image_cmd fimapi action descriptor imgid
     | "flavor" ->
       Lwt.return_unit
     | "descriptor" ->
       descriptor_cmd action descriptor
     | "node" ->
       node_cmd fimapi action nodeid
     | _ -> Lwt_io.printf "%s Is not a command\n" cmd)
  | _ -> Lwt_io.printf "%s not implemented\n" component


let p1 component cmd action netid imgid nodeid fduid instanceid destid descriptor =
  Lwt_main.run @@ parser component cmd action netid imgid nodeid fduid instanceid destid descriptor

let usage = "usage: " ^ Sys.argv.(0) ^ " [fim|faem|feo] "

let node_uuid_par = Arg.(value & opt (some string) None & info ["n"] ~docv:"node uuid")
let fdu_uuid_par = Arg.(value & opt (some string) None & info ["f"] ~docv:"fdu uuid")
let instance_uuid_par = Arg.(value & opt (some string) None & info ["i"] ~docv:"instance uuid")
let dest_node_uuid_par = Arg.(value & opt (some string) None & info ["du"] ~docv:"destination uuid")
let net_uuid_par = Arg.(value & opt (some string) None & info ["net"] ~docv:"network uuid")
let img_uuid_par = Arg.(value & opt (some string) None & info ["img"] ~docv:"image uuid")
let descriptor_par = Arg.(value & opt (some string) None & info ["d";"descriptor"] ~docv:"descriptor file")

let act_t = Arg.(required & pos 2 (some string) None & info [] ~docv:"action")
let cmd_t = Arg.(required & pos 1 (some string) None & info [] ~docv:"type")
let component_t = Arg.(required & pos 0 (some string) None & info [] ~docv:"component [fim|faem|feo]")

let fos_t =
  Term.(
    const p1 $ component_t $ cmd_t $ act_t $ net_uuid_par $ img_uuid_par
    $ node_uuid_par $ fdu_uuid_par $ instance_uuid_par $ dest_node_uuid_par $ descriptor_par)


let () =
  Printexc.record_backtrace true;
  Term.exit @@ Term.eval (fos_t, Term.info "fos-ng")