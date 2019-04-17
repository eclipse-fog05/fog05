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
open Lwt.Infix
open Fos_errors

let ylocator = Apero.Option.get @@ Apero_net.Locator.of_string @@ Apero.Option.get_or_default (Sys.getenv_opt "FOS_YAKS_ENDPOINT") "tcp/127.0.0.1:7887"
let ysystem = Apero.Option.get_or_default (Sys.getenv_opt "FOS_SYS_ID") "0"
let ytenant = Apero.Option.get_or_default (Sys.getenv_opt "FOS_TENANT_ID") "0"


type api = {
  yconnector : Yaks_connector.connector;
  sysid : string;
  tenantid: string;
}


let rec remove_duplicates nl ol =
  match ol with
  | [] -> nl
  | hd::tl ->
    (match List.mem hd nl with
     | false -> remove_duplicates (nl@[hd]) tl
     | true -> remove_duplicates nl tl)


module Manifest = struct

  let check manifest =
    ignore manifest;
    true


end


module Node = struct


  let list api =
    Yaks_connector.Global.Actual.get_all_nodes api.sysid api.tenantid api.yconnector
    >>=
    Lwt_list.filter_map_p (fun e -> Yaks_connector.Global.Actual.get_node_info api.sysid api.tenantid e api.yconnector)


  let info nodeid api =
    match%lwt Yaks_connector.Global.Actual.get_node_info api.sysid api.tenantid nodeid api.yconnector with
    | Some info -> Lwt.return info
    | None -> raise @@ FException (`InternalError (`Msg ("Unable to node with this id")))

  let status nodeid api =
    match%lwt Yaks_connector.Global.Actual.get_node_status api.sysid api.tenantid nodeid api.yconnector  with
    | Some status -> Lwt.return status
    | None -> raise @@ FException (`InternalError (`Msg ("Unable to node with this id")))

  let plugins nodeid api =
    Yaks_connector.Global.Actual.get_node_plugins api.sysid api.tenantid nodeid api.yconnector

end


module Network = struct

  let add_network (descriptor:FTypes.virtual_network) api =
    let netid = descriptor.uuid in
    Yaks_connector.Global.Desired.add_network api.sysid api.tenantid netid descriptor api.yconnector
    >>= fun _ -> Lwt.return true
  let remove_network netid  api =
    Yaks_connector.Global.Desired.remove_network api.sysid api.tenantid netid api.yconnector
    >>= fun _ -> Lwt.return true

  let list_networks api =
    Yaks_connector.Global.Actual.get_all_networks api.sysid api.tenantid api.yconnector

  let add_connection_point (descriptor:FDU.connection_point) api =
    let cpid = descriptor.uuid in
    Yaks_connector.Global.Desired.add_port api.sysid api.tenantid cpid descriptor api.yconnector
    >>= fun _ -> Lwt.return true

  let remove_connection_point cpid api =
    Yaks_connector.Global.Desired.remove_port api.sysid api.tenantid cpid api.yconnector
    >>= fun _ -> Lwt.return true
  let list_connection_points api =
    Yaks_connector.Global.Actual.get_all_ports api.sysid api.tenantid api.yconnector

end

module FDU = struct


  let rec wait_fdu_onboarding sysid tenantid fduid api =
    Yaks_connector.Global.Actual.get_fdu_info sysid tenantid fduid api.yconnector
    >>= fun r ->
    match r with
    | Some _ -> Lwt.return_unit
    | None -> wait_fdu_onboarding sysid tenantid fduid api

  let rec wait_fdu_offloading sysid tenantid fduid api =
    Yaks_connector.Global.Actual.get_fdu_info sysid tenantid fduid api.yconnector
    >>= fun r ->
    match r with
    | Some _ -> wait_fdu_offloading sysid tenantid fduid api
    | None -> Lwt.return_unit


  let rec wait_fdu_instance_state_change new_state sysid tenantid nodeid fdu_uuid instance_uuid api =
    Yaks_connector.Global.Actual.get_node_fdu_info sysid tenantid nodeid fdu_uuid instance_uuid api.yconnector
    >>= fun r ->
    match r with
    | Some fduinfo ->
      if fduinfo.status == new_state then
        Lwt.return_unit
      else
        wait_fdu_instance_state_change new_state sysid tenantid nodeid fdu_uuid instance_uuid api
    | None -> wait_fdu_instance_state_change new_state sysid tenantid nodeid fdu_uuid instance_uuid api

  let rec wait_fdu_instance_undefine sysid tenantid nodeid fdu_uuid instance_uuid api =
    Yaks_connector.Global.Actual.get_node_fdu_info sysid tenantid nodeid fdu_uuid instance_uuid api.yconnector
    >>= fun r ->
    match r with
    | Some _ ->
      wait_fdu_instance_undefine sysid tenantid nodeid fdu_uuid instance_uuid api
    | None -> Lwt.return_unit

  let change_fdu_instance_state instanceid state newstate wait api =
    let%lwt nodeid = Yaks_connector.Global.Actual.get_fdu_instance_node api.sysid api.tenantid "*" instanceid api.yconnector in
    let nodeid =
      match nodeid with
      | Some nid -> nid
      | None ->  raise @@ FException (`InternalError (`Msg ("Unable to find nodeid for this instance id" )))
    in
    let%lwt record = Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid "*" instanceid api.yconnector in
    match record with
    | Some record ->
      let fduid =  record.fdu_uuid in
      let record = {record with status = state } in
      let%lwt  _ = Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid instanceid record api.yconnector in
      (match wait with
       | true ->
         let%lwt _ = wait_fdu_instance_state_change newstate api.sysid api.tenantid nodeid fduid instanceid api in
         Lwt.return instanceid
       | false -> Lwt.return instanceid)
    | None -> raise @@ FException (`InternalError (`Msg ("Unable to find record for this instance" ) ))


  let onboard (fdu:FDU.descriptor) ?(wait=true) api =
    let fduid =
      match fdu.uuid with
      | Some fduid -> fduid
      | None -> Apero.Uuid.to_string @@ Apero.Uuid.make_from_alias fdu.name
    in
    let%lwt _ = Yaks_connector.Global.Desired.add_fdu_info api.sysid api.tenantid fduid fdu api.yconnector in
    match wait with
    | true ->
      let%lwt _ = wait_fdu_onboarding api.sysid api.tenantid fduid api in
      Lwt.return fduid
    | false ->
      Lwt.return fduid


  let offload fduid ?(wait=true) api =
    let%lwt _ = Yaks_connector.Global.Desired.remove_fdu_info api.sysid api.tenantid fduid api.yconnector in
    match wait with
    | true ->
      let%lwt _ = wait_fdu_offloading api.sysid api.tenantid fduid api in
      Lwt.return fduid
    | false -> Lwt.return fduid

  let define fduid nodeid ?(wait=true) api =
    let%lwt _ = Yaks_connector.Global.Actual.get_fdu_info api.sysid api.tenantid fduid api.yconnector in
    let ar = FDU.{fpga = []; gpu= []} in
    let instance_uuid = Apero.Uuid.to_string @@ Apero.Uuid.make () in
    let record = FDU.{uuid = Some instance_uuid; fdu_uuid = fduid; node = nodeid; status = `DEFINE; interfaces =  []; connection_points = []; error_code = None; error_msg = None; migration_properties = None; hypervisor_info = Fos_im.JSON.create_empty (); accelerators = ar; io_ports = [] } in
    let%lwt _ = Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid instance_uuid record api.yconnector in
    match wait with
    | true ->
      let%lwt _ = wait_fdu_instance_state_change `DEFINE api.sysid api.tenantid nodeid fduid instance_uuid api in
      Lwt.return instance_uuid
    | false -> Lwt.return instance_uuid

  let undefine instanceid ?(wait=true) api =
    let%lwt nodeid = Yaks_connector.Global.Actual.get_fdu_instance_node api.sysid api.tenantid "*" instanceid api.yconnector in
    let nodeid =
      match nodeid with
      | Some nid -> nid
      | None ->  raise @@ FException (`InternalError (`Msg ("Unable to find nodeid for this instance id" ) ))
    in
    let%lwt record = Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid "*" instanceid api.yconnector in
    match record with
    | Some record ->
      let fduid =  record.fdu_uuid in
      let record = {record with status = `UNDEFINE } in
      let%lwt  _ = Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid instanceid record api.yconnector in
      (match wait with
       | true ->
         let%lwt _ = wait_fdu_instance_undefine api.sysid api.tenantid nodeid fduid instanceid api in
         Lwt.return instanceid
       | false -> Lwt.return instanceid)
    | None -> raise @@ FException (`InternalError (`Msg ("Unable to find record for this instance" ) ))

  let configure instanceid ?(wait=true) api =
    change_fdu_instance_state instanceid `CONFIGURE `CONFIGURE wait api

  let clean instanceid ?(wait=true) api =
    change_fdu_instance_state instanceid `CLEAN `DEFINE wait api

  let start instanceid ?(wait=true) api =
    change_fdu_instance_state instanceid `RUN `RUN wait api

  let stop instanceid ?(wait=true) api =
    change_fdu_instance_state instanceid `STOP `CONFIGURE wait api

  let pause instanceid ?(wait=true) api =
    change_fdu_instance_state instanceid `PAUSE `PAUSE wait api

  let resume instanceid ?(wait=true) api =
    change_fdu_instance_state instanceid `RESUME `RUN wait api

  let migrate insanceid destination ?(wait=true) api =
    Printf.printf "%s %s %b" insanceid destination wait;
    ignore api.yconnector;
    Lwt.return insanceid
  (* let info_node fduid nodeid api =
     Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector

     let list_node nodeid api =
     Yaks_connector.Global.Actual.get_node_fdus api.sysid api.tenantid nodeid api.yconnector >>=
     Lwt_list.map_p (fun (_,_,f) -> Lwt.return f) *)


  let instantiate fduid nodeid ?(wait=true) api =
    define fduid nodeid ~wait:true api
    >>= fun instanceid -> configure instanceid ~wait:true api
    >>= fun instanceid -> start instanceid ~wait:wait api
    >>= Lwt.return

  let terminate instanceid ?(wait=true) api =
    stop instanceid ~wait:true api
    >>= fun instanceid -> clean instanceid ~wait:true api
    >>= fun instanceid -> undefine instanceid ~wait:wait api
    >>= Lwt.return


  let get_nodes fduid api =
    Yaks_connector.Global.Actual.get_fdu_nodes api.sysid api.tenantid fduid api.yconnector

  let info fduid api =
    match%lwt Yaks_connector.Global.Actual.get_fdu_info api.sysid api.tenantid fduid api.yconnector with
    | Some descriptor -> Lwt.return descriptor
    | None -> raise @@ FException (`InternalError (`Msg ("Unable to find descriptor for this FDU" ) ))

  let instance_info instanceid api =
    let%lwt nodeid = Yaks_connector.Global.Actual.get_fdu_instance_node api.sysid api.tenantid "*" instanceid api.yconnector in
    let nodeid =
      match nodeid with
      | Some nid -> nid
      | None ->  raise @@ FException (`InternalError (`Msg ("Unable to find nodeid for this instance id" ) ))
    in
    let%lwt record = Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid "*" instanceid api.yconnector in
    match record with
    | Some record ->
      Lwt.return record
    | None -> raise @@ FException (`InternalError (`Msg ("Unable to find record for this instance" ) ))

  let list api =
    Yaks_connector.Global.Actual.get_all_fdus api.sysid api.tenantid api.yconnector >>=
    Lwt_list.filter_map_p (fun e -> Yaks_connector.Global.Actual.get_fdu_info api.sysid api.tenantid e api.yconnector)

  let instance_list fduid ?(nodeid="*") api =
    Yaks_connector.Global.Actual.get_node_fdu_instances api.sysid api.tenantid nodeid fduid api.yconnector
    >>= fun res ->
    let nids = res |> List.map (fun  (n,_,_,_ )-> n) |> remove_duplicates [] in
    Lwt.return @@ List.map (fun nid ->
        let iids = (List.filter (fun (n,_,_,_) -> n == nid) res ) |> List.map (fun (_,_,iid,_) -> iid ) in
        (nid, iids)
      ) nids




end

module Image = struct

  let add (descriptor:Fdu.image) api =
    let imgid = (match descriptor.uuid with
        | Some id -> id
        | None -> Apero.Uuid.to_string (Apero.Uuid.make ()) ) in
    let descriptor = {descriptor with uuid = Some imgid} in
    Yaks_connector.Global.Desired.add_image api.sysid api.tenantid imgid descriptor api.yconnector
    >>= fun _ -> Lwt.return imgid
  let remove imgid api =
    Yaks_connector.Global.Desired.remove_image api.sysid api.tenantid imgid api.yconnector
    >>= fun _ -> Lwt.return true
  let list api =
    Yaks_connector.Global.Actual.get_all_images api.sysid api.tenantid api.yconnector

end

(*
module Flavor = struct
  let add descriptor api =
    ignore [descriptor; api];
    Lwt.return true
  let remove descriptor api =
    ignore [descriptor; api];
    Lwt.return true
  let list api =
    ignore api;
    Lwt.return []

end *)

module FIMAPI = struct

  let connect ?(locator=ylocator) ?(sysid=ysystem) ?(tenantid=ytenant) () =
    let%lwt yconnector = Yaks_connector.get_connector_of_locator locator in
    Lwt.return { yconnector; sysid; tenantid}

  let close api =
    Yaks_connector.close_connector api.yconnector
end