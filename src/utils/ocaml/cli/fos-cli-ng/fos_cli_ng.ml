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
open Fos_im
open Fos_core
open Errors
open Fos_fim_api
open Fos_faem_api
open Fos_feo_api


let check s =
  let n = String.length s in
  if n > 0 && s.[n-1] = '\n' then
    String.sub s 0 (n-1)
  else
    s


(* Entity Commands *)

let add_entity_descriptor_to_catalog api (descriptor:string option) =
(** [add_entity_descriptor_to_catalog a d] registers the descriptor [d] in the system catalog.
    Returns Lwt.unit
  *)
  match descriptor with
  | Some dp ->
    let d = read_file dp in
    let e = User.Descriptors.Entity.descriptor_of_string d in
    Entity.onboard e api  >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.Entity.string_of_descriptor res)
  | None -> Lwt_io.printf "Manifest parameter missing!!\n"

let remove_entity_descriptor_from_catalog api eid =
(** [remove_entity_descriptor_from_catalog a id] removed the descriptor intified by [id] from the system catalog.
    Returns Lwt.unit
  *)
  match eid with
  | Some id ->
    Entity.offload id api  >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.Entity.string_of_descriptor res)
  | None -> Lwt_io.printf "Entity uuid parameter missing!!\n"


let entity_instantiate api eid =
(** [entity_instantiate a id] instatiate the Entity identified by [id] in the system.
    Returns Lwt.unit
  *)
  (match eid with
   | Some eid ->
     Entity.instantiate eid api >>= fun res ->
     Lwt_io.printf "%s\n" (Infra.Descriptors.Entity.string_of_record res)
   | None  -> Lwt_io.printf "Entity UUID parameter missing!!\n")

let entity_terminate api instanceid =
(** [entity_terminate a id] termiates the Entity instace identified by [id].
    Returns Lwt.unit
  *)
  match instanceid with
  | Some iid ->
    Entity.terminate iid api >>= fun res ->
    Lwt_io.printf "%s\n" (Infra.Descriptors.Entity.string_of_record res)
  | None -> Lwt_io.printf "Entity Instance UUID parameter missing!!\n"

let entity_info api aeid =
(** [entity_info a id] gets informatio about the entity identified by [id].
    Returns Lwt.unit
  *)
  match aeid with
  | Some iid ->
    Entity.get_entity_descriptor iid api >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.Entity.string_of_descriptor res)
  | None -> Lwt_io.printf "Entity UUID parameter missing!!\n"


let entity_record api instanceid =
(** [entity_record a id] gets informatio about the entity instance identified by [id].
    Returns Lwt.unit
  *)
  match instanceid with
  | Some iid ->
    Entity.get_entity_instance_info iid api >>= fun res ->
    Lwt_io.printf "%s\n" (Infra.Descriptors.Entity.string_of_record res)
  | None -> Lwt_io.printf "Entity Instance UUID parameter missing!!\n"

let entity_list api =
(** [entity_record a id] gets all the entities registered in the system catalog.
    Returns Lwt.unit
  *)
  let%lwt elist = Entity.list api in
  Lwt_list.iter_p (fun e -> Lwt_io.printf "%s\n" e) elist

let entity_instance_list api eid =
(** [entity_record a id] gets all the entities instaces running the system catalog.
    Returns Lwt.unit
  *)
  match eid with
  | Some eid ->
    let%lwt elist = Entity.instance_list eid api in
    let%lwt _ = Lwt_io.printf "Entity: %s instances\n" eid in
    Lwt_list.iter_p (fun e -> Lwt_io.printf "%s\n" e) elist
  | None -> Lwt_io.printf "Entity UUID parameter missing!!\n"

(* Atomic Entity Commands *)
(* let add_ae_descriptor_to_catalog api (descriptor:string option) =
  match descriptor with
  | Some dp ->
    let d = read_file dp in
    let fdu = User.Descriptors.AtomicEntity.descriptor_of_string d in
    AtomicEntity.onboard fdu api  >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.AtomicEntity.string_of_descriptor res)
  | None -> Lwt_io.printf "Manifest parameter missing!!\n"

let remove_ae_descriptor_from_catalog api aeid =
  match aeid with
  | Some id ->
    AtomicEntity.offload id api  >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.AtomicEntity.string_of_descriptor res)
  | None -> Lwt_io.printf "Atomic Entity UUID parameter missing!!\n"


let ae_instantiate api ae_id =
  (match ae_id with
   | Some ae_id ->
     AtomicEntity.instantiate ae_id api >>= fun res ->
     Lwt_io.printf "%s\n" (Infra.Descriptors.AtomicEntity.string_of_record res)
   | None  -> Lwt_io.printf "Atomic Entity UUID parameter missing!!\n")

let ae_terminate api instanceid =
  match instanceid with
  | Some iid ->
    AtomicEntity.terminate iid api >>= fun res ->
    Lwt_io.printf "%s\n" (Infra.Descriptors.AtomicEntity.string_of_record res)
  | None -> Lwt_io.printf "Atomic Entity Instance UUID parameter missing!!\n"

let ae_info api aeid =
  match aeid with
  | Some iid ->
    AtomicEntity.get_atomic_entity_descriptor iid api >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.AtomicEntity.string_of_descriptor res)
  | None -> Lwt_io.printf "Atomic Entity Instance UUID parameter missing!!\n"


let ae_record api instanceid =
  match instanceid with
  | Some iid ->
    AtomicEntity.get_atomic_entity_instance_info iid api >>= fun res ->
    Lwt_io.printf "%s\n" (Infra.Descriptors.AtomicEntity.string_of_record res)
  | None -> Lwt_io.printf "Atomic Entity Instance UUID parameter missing!!\n"


let atomic_entity_list api =
  let%lwt elist = AtomicEntity.list api in
  Lwt_list.iter_p (fun e -> Lwt_io.printf "%s\n" e) elist

let atomic_entity_instance_list api aeid =
  match aeid with
  | Some aeid ->
    let%lwt elist = AtomicEntity.instance_list aeid api in
    let%lwt _ = Lwt_io.printf "Atomic Entity: %s instances\n" aeid in
    Lwt_list.iter_p (fun e -> Lwt_io.printf "%s\n" e) elist
  | None  -> Lwt_io.printf "Atomic Entity UUID parameter missing!!\n" *)
(* Plugin command *)

let plugin_list nodeid yconnector =
(** [plugin_list nodeid connector] gets all plugins of [nodeid] need a yaks connector [connector].
    Returns Lwt.unit
  *)
  match nodeid with
  | Some node_uuid ->
    Cli_helper.get_all_node_plugin node_uuid yconnector >>=
    fun d -> Cli_printing.print_node_plugin d
  | None -> Lwt_io.printf "Node uuid parameter missing!!\n"

let plugin_add nodeid descriptor _ =
(** [plugin_add nodeid descriptor] add the plguin describer by [descriptor] in [nodeid].
    Returns Lwt.unit
  *)
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
(** [plugin_cmd action nodeid () descriptor] plugin command function for the CLI.
    Returns Lwt.unit
  *)
  match action with
  | "list" -> (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= plugin_list nodeid
  | "add" -> (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= plugin_add nodeid descriptor
  | "remove" -> Lwt_io.printf "Not implemented\n"
  (* Missing parameter is pluginid *)
  | _ -> Lwt_io.printf "%s action not recognized!!\n" action

(* Node commands *)
let node_cmd api action nodeid =
(** [node_cmd api action nodeid] node command function for the CLI.
    Returns Lwt.unit
  *)
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
(** [network_add api descriptor] adds the network represented by [descriptor] in the system catalog.
    Returns Lwt.unit
  *)
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
(** [network_remove api netid] removes the network idenfified by [netid] in from system catalog.
    Returns Lwt.unit
  *)
  match netid with
  | Some netid ->
    Network.remove_network netid api
    >>= fun _ -> Lwt_io.printf "%s\n" netid
  | None -> Lwt_io.printf "Network uuid parameter missing!!\n"

let network_list api =
(** [network_list api] gets all the network registered in the system catalog.
    Returns Lwt.unit
  *)
  Network.list_networks api >>= Cli_printing.print_networks


let network_cmd api action descriptor netid =
(** [network_cmd api action descriptor netid] network command function for the CLI.
    Returns Lwt.unit
  *)
  match action with
  | "add" -> network_add api descriptor
  | "list" -> network_list api
  | "remove" -> network_remove api netid
  | _ -> Lwt_io.printf "%s action not recognized!!" action


(* Image commands *)

let image_add api descriptor =
(** [image_add api descriptor] adds the image represented by [descriptor] in the system catalog.
    Returns Lwt.unit
  *)
  match descriptor with
  | Some path ->
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Base.Descriptors.FDU.image_of_string in
    (match res with
     | Ok descriptor ->
       Image.add descriptor api >>= Lwt_io.printf "%s\n"
     | Error e -> Lwt_io.printf "Desriptor has errors: %s\n" (Printexc.to_string e))
  |None  -> Lwt_io.printf "Desriptor parameter missing!!\n"


let image_remove api imgid =
(** [image_remove api imgid] removes the image idenfitied by [imgid] from the system catalog.
    Returns Lwt.unit
  *)
  match imgid with
  | Some imgid ->
    Image.remove imgid api
    >>= fun _ -> Lwt_io.printf "%s\n" imgid
  | None -> Lwt_io.printf "Image uuid parameter missing!!\n"

let image_list api =
(** [image_list api] gets all the images registered in the system catalog.
    Returns Lwt.unit
  *)
  Image.list api >>= Cli_printing.print_images


let image_cmd api action descriptor imgid =
(** [image_cmd api action descriptor imgid] image command function for the CLI.
    Returns Lwt.unit
  *)
  match action with
  | "add" -> image_add api descriptor
  | "list" -> image_list api
  | "remove" -> image_remove api imgid
  | _ -> Lwt_io.printf "%s action not recognized!!" action


(* Manifest commands *)

let descriptor_image descriptor =
(** [descriptor_image descriptor] Checks the image [descriptor].
    Returns Lwt.unit
  *)
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Base.Descriptors.FDU.image_of_string  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_flavor descriptor =
(** [descriptor_flavor descriptor] Checks the flavor [descriptor].
    Returns Lwt.unit
  *)
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont Base.Descriptors.FDU.computational_requirements_of_string  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_fdu descriptor =
(** [descriptor_fdu descriptor] Checks the FDU [descriptor].
    Returns Lwt.unit
  *)
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont User.Descriptors.FDU.descriptor_of_string in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_network descriptor =
(** [descriptor_network descriptor] Checks the network [descriptor].
    Returns Lwt.unit
  *)
  match descriptor with
  | Some path ->
    let%lwt _ = Lwt_io.printf "Check descriptor %s\n" path in
    let cont = read_file path in
    let res = Cli_helper.check_descriptor cont FTypes.network_of_string  in
    (match res with
     | Ok _ -> Lwt_io.printf "Manifest is Ok\n"
     | Error e -> Lwt_io.printf "Manifest has errors: %s\n" (Printexc.to_string e))
  | None -> Lwt_io.printf "Manifest parameter is missing!!\n"

let descriptor_cmd kind descriptor =
(** [descriptor_cmd kind descriptor] descriptor command function for the CLI.
    Returns Lwt.unit
  *)
  match kind with
  | "fdu" -> descriptor_fdu descriptor
  | "network" -> descriptor_network descriptor
  | "flavor" -> descriptor_flavor descriptor
  | "image" -> descriptor_image descriptor
  | _ -> Lwt_io.printf "%s is not a valid type of descriptor\n" kind

(* FDU COMMANDS *)

let add_fdu_descriptor_to_catalog api (descriptor:string option) =
(** [add_fdu_descriptor_to_catalog api descriptor] Adds the fdu represented by [descriptor] in the system catalog
    Returns Lwt.unit
  *)
  match descriptor with
  | Some dp ->
    let d = read_file dp in
    let fdu = User.Descriptors.FDU.descriptor_of_string d in
    FDU.onboard fdu api  >>= fun res ->
    Lwt_io.printf "%s\n" (User.Descriptors.FDU.string_of_descriptor res)
  | None -> Lwt_io.printf "Manifest parameter missing!!\n"

let remove_fdu_descriptor_from_catalog api fduid =
(** [remove_fdu_descriptor_from_catalog api fduid] Removes the fdu identified by [fduid] from the system catalog
    Returns Lwt.unit
  *)
  match fduid with
  | Some id ->
    FDU.offload id api  >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "Entity uuid parameter missing!!\n"

let fdu_define api fduid nodeid =
(** [fdu_define api fduid nodeid] Defines an fdu instance for the fdu [fduid] in the node [nodeid].
    Returns Lwt.unit
  *)
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.define fid nid api >>= fun res ->
       Lwt_io.printf "%s\n" (Infra.Descriptors.FDU.string_of_record res)
     | None  -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"

let fdu_undefine api instanceid =
(** [fdu_define api instanceid] Undefines the fdu instance idenfitied by [instanceid].
    Returns Lwt.unit
  *)
  match instanceid with
  | Some iid ->
    FDU.undefine iid api >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"


let fdu_instantiate api fduid nodeid =
(** [fdu_instantiate api fduid nodeid] Instantiates an fdu instance for the fdu [fduid] in the node [nodeid].
    Returns Lwt.unit
  *)
  match nodeid with
  | Some nid ->
    (match fduid with
     | Some fid ->
       FDU.instantiate fid nid api >>= fun res ->
       Lwt_io.printf "%s\n" (Infra.Descriptors.FDU.string_of_record res)
     | None  -> Lwt_io.printf "FDU UUID parameter missing!!\n")
  | None ->  Lwt_io.printf "Node UUID parameter missing!!\n"

let fdu_terminate api instanceid =
(** [fdu_terminate api instanceid] Terminates the fdu instance idenfitied by [instanceid].
    Returns Lwt.unit
  *)
  match instanceid with
  | Some iid ->
    FDU.terminate iid api >>= fun res ->
    Lwt_io.printf "%s\n" res
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"


let fdu_instances api fduid nodeid =
(** [fdu_instances api fduid nodeid] Gets all the instances of [fduid] running in [nodeid].
    Returns Lwt.unit
  *)
  match fduid with
  | Some fduid ->
    (match nodeid with
     | Some nid -> FDU.instance_list fduid ~nodeid:nid api
     | None -> FDU.instance_list fduid api  )
    >>=
    Cli_printing.print_fdu_instances
  | None -> Lwt_io.printf "FDU UUID parameter missing!!\n"

let fdu_state_change api instanceid state =
(** [fdu_state_change api instanceid state] Updates the state for the instance identified by [instanceid] to [state].
    Returns Lwt.unit
  *)
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
(** [fdu_migrate api instanceid destinationid] Migrates the instance identified by [instanceid] to [destinationid].
    Returns Lwt.unit
  *)
  match instanceid with
  | Some _ ->
    (match destinationid with
     |Some _ ->
       Lwt.return_unit
     (* (Yaks_connector.get_connector_of_locator Cli_helper.yaksserver) >>= Cli_helper.send_migrate_atomic_entity_instance node_uuid entity_uuid instance_uuid destination_node *)
     |None -> Lwt_io.printf "Destination Node UUID parameter missing!!\n")
  | None -> Lwt_io.printf "FDU Instance UUID parameter missing!!\n"



let fdu_list api =
(** [fdu_list api] Gets all the FDU registered in the system catalog
    Returns Lwt.unit
  *)
  let print_fdu (f:User.Descriptors.FDU.descriptor) =
    Lwt_io.printf "FDU ID: %s Descriptor %s\n" f.id (User.Descriptors.FDU.string_of_descriptor f)
  in
  FDU.list api >>=
  Lwt_list.iter_p print_fdu
  >>= fun _ -> Lwt.return_unit

let fdu_cmd api action nodeid fduid instanceid destid descriptor =
(** [fdu_cmd api action nodeid fduid instanceid destid descriptor] fdu command function for the CLI.
    Returns Lwt.unit
  *)
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


(* let atomic_entity_cmd faemapi action instanceid aeid descriptor =
  (match action with
   | "onboard" ->
     add_ae_descriptor_to_catalog faemapi descriptor
   | "offload" ->
     remove_ae_descriptor_from_catalog faemapi aeid
   | "instantiate" ->
     ae_instantiate faemapi aeid
   | "terminate" ->
     ae_terminate faemapi instanceid
   | "info" ->
     ae_info faemapi aeid
   | "record" ->
     ae_record faemapi instanceid
   | "list" ->
     atomic_entity_list faemapi
   | "instance_list" ->
     atomic_entity_instance_list faemapi aeid
   | _  ->  Lwt_io.printf "%s Is not a command\n" action) *)


let entity_cmd feoapi action instanceid eid descriptor =
(** [entity_cmd feoapi action instanceid eid descriptor] entity command function for the CLI.
    Returns Lwt.unit
  *)
  (match action with
   | "onboard" ->
     add_entity_descriptor_to_catalog feoapi descriptor
   | "offload" ->
     remove_entity_descriptor_from_catalog feoapi eid
   | "instantiate" ->
     entity_instantiate feoapi eid
   | "terminate" ->
     entity_terminate feoapi instanceid
   | "info" ->
     entity_info feoapi eid
   | "record" ->
     entity_record feoapi instanceid
   | "list" ->
     entity_list feoapi
   | "instance_list" ->
     entity_instance_list feoapi eid
   | _  ->  Lwt_io.printf "%s Is not a command\n" action)


let parser component cmd action netid imgid nodeid fduid instanceid destid descriptor aeid eid =
(** [parser component cmd action netid imgid nodeid fduid instanceid destid descriptor aeid eid] parserfunction for the CLI, calls the right function depending on the parameters
    Returns Lwt.unit
  *)
  match String.lowercase_ascii component with
  | "fim" ->
    (match cmd with
     | "fdu" ->
       let%lwt fimapi = Cli_helper.yapi () in
       fdu_cmd fimapi action nodeid fduid instanceid destid descriptor
     | "network" ->
       let%lwt fimapi = Cli_helper.yapi () in
       network_cmd fimapi action descriptor netid
     | "plugin" ->
       plugin_cmd action nodeid None descriptor
     | "image" ->
       let%lwt fimapi = Cli_helper.yapi () in
       image_cmd fimapi action descriptor imgid
     | "flavor" ->
       Lwt.return_unit
     | "descriptor" ->
       descriptor_cmd action descriptor
     | "node" ->
       let%lwt fimapi = Cli_helper.yapi () in
       node_cmd fimapi action nodeid
     | _ -> Lwt_io.printf "%s Is not a command\n" cmd)
  (* | "faem" ->
    (match cmd with
     | "atomic_entity" ->
       let%lwt faemapi = Cli_helper.faemapy () in
       atomic_entity_cmd faemapi action instanceid aeid descriptor
     | _  ->  Lwt_io.printf "%s Is not a recognized, maybe atomic_entity\n" cmd) *)
  | "feo" ->
    (match cmd with
     | "entity" ->
       let%lwt feoapi = Cli_helper.feoapi () in
       entity_cmd feoapi action instanceid eid descriptor
     | _  ->  Lwt_io.printf "%s Is not a recognized, maybe entity\n" cmd)

  | _ -> Lwt_io.printf "%s not implemented\n" component


let p1 component cmd action netid imgid nodeid fduid instanceid destid descriptor aeid eid =
(** [p1 component cmd action netid imgid nodeid fduid instanceid destid descriptor aeid eid] Calls parser inside Lwt
    Returns Lwt.unit
  *)
  Lwt_main.run @@ parser component cmd action netid imgid nodeid fduid instanceid destid descriptor aeid eid

let usage = "usage: " ^ Sys.argv.(0) ^ " [fim|faem|feo] "

let node_uuid_par = Arg.(value & opt (some string) None & info ["n";"node-uuid"] ~docv:"node uuid")
let fdu_uuid_par = Arg.(value & opt (some string) None & info ["f";"fdu-uuid"] ~docv:"fdu uuid")
let ae_uuid_par = Arg.(value & opt (some string) None & info ["ae";"atomic-entity-uuid"] ~docv:"atomic entity uuid")
let e_uuid_par = Arg.(value & opt (some string) None & info ["e";"entity-uuid"] ~docv:"atomic entity uuid")
let instance_uuid_par = Arg.(value & opt (some string) None & info ["i";"instance-uuid"] ~docv:"instance uuid")
let dest_node_uuid_par = Arg.(value & opt (some string) None & info ["du";"destination-uuid"] ~docv:"destination uuid")
let net_uuid_par = Arg.(value & opt (some string) None & info ["net";"network-uuid"] ~docv:"network uuid")
let img_uuid_par = Arg.(value & opt (some string) None & info ["img";"image-uuid"] ~docv:"image uuid")
let descriptor_par = Arg.(value & opt (some string) None & info ["d";"descriptor"] ~docv:"descriptor file")

let act_t = Arg.(required & pos 2 (some string) None & info [] ~docv:"action")
let cmd_t = Arg.(required & pos 1 (some string) None & info [] ~docv:"type")
let component_t = Arg.(required & pos 0 (some string) None & info [] ~docv:"component [fim|faem|feo]")

let fos_t =
  Term.(
    const p1 $ component_t $ cmd_t $ act_t $ net_uuid_par $ img_uuid_par
    $ node_uuid_par $ fdu_uuid_par $ instance_uuid_par $ dest_node_uuid_par $ descriptor_par $ ae_uuid_par $ e_uuid_par)


let () =
  Printexc.record_backtrace true;
  Term.exit @@ Term.eval (fos_t, Term.info "fos-ng")