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


let ylocator = Apero.Option.get @@ Apero_net.Locator.of_string @@ Apero.Option.get_or_default (Sys.getenv_opt "FOS_YAKS_ENDPOINT") "tcp/127.0.0.1:7887"
let ysystem = Apero.Option.get_or_default (Sys.getenv_opt "FOS_SYS_ID") "0"
let ytenant = Apero.Option.get_or_default (Sys.getenv_opt "FOS_TENANT_ID") "0"


type api = {
  yconnector : Yaks_connector.connector;
  sysid : string;
  tenantid: string;
}



module Manifest = struct

  let check manifest =
    ignore manifest;
    true


end


module Node = struct


  let list api =
    Yaks_connector.Global.Actual.get_all_nodes api.sysid api.tenantid api.yconnector
    >>=
    Lwt_list.map_p (fun e -> Yaks_connector.Global.Actual.get_node_info api.sysid api.tenantid e api.yconnector)


  let info nodeid api =
    Yaks_connector.Global.Actual.get_node_info api.sysid api.tenantid nodeid api.yconnector

  let status nodeid api =
    Yaks_connector.Global.Actual.get_node_status api.sysid api.tenantid nodeid api.yconnector

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

  let add_connection_point (descriptor:FTypes.connection_point) api =
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

  let onboard (fdu:FTypes.fdu) ?(wait=true) api =
    ignore wait;
    let fduid = fdu.uuid in
    Yaks_connector.Global.Desired.add_fdu_info api.sysid api.tenantid fduid fdu api.yconnector
    >>= fun _ -> Lwt.return_true

  let offload fduid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Desired.remove_fdu_info api.sysid api.tenantid fduid api.yconnector
    >>= fun _ -> Lwt.return_true

  let define fduid nodeid ?(wait=true) api =
    ignore wait;
    let%lwt _ = Yaks_connector.Global.Actual.get_fdu_info api.sysid api.tenantid fduid api.yconnector in
    let record = Fos_im.FTypesRecord.{ fdu_uuid = fduid;  status = `DEFINE; interfaces =  []; connection_points = []; error_code = None; migration_properties = None; hypervisor_info = Fos_im.JSON.create_empty () } in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid record api.yconnector
    >>= fun _ -> Lwt.return_true

  let undeifne fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector
    >>= fun descriptor ->
    let descriptor = {descriptor with status = `UNDEFINE } in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let configure  fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = `CONFIGURE } in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let clean fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = `CLEAN } in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let run fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = `RUN } in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let stop fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = `STOP } in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let pause fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = `PAUSE} in
    Yaks_connector.Global.Desired.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let migrate fduid nodeid destination ?(wait=true) api =
    ignore wait;
    Printf.printf "%s %s %s %b" fduid nodeid destination wait;
    ignore api.yconnector;
    Lwt.return true
  let info_node fduid nodeid api =
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector

  let list_node nodeid api =
    Yaks_connector.Global.Actual.get_node_fdus api.sysid api.tenantid nodeid api.yconnector >>=
    Lwt_list.map_p (fun (_,_,f) -> Lwt.return f)

  let get_nodes fduid api =
    Yaks_connector.Global.Actual.get_fdu_nodes api.sysid api.tenantid fduid api.yconnector

  let info fduid api =
    Yaks_connector.Global.Actual.get_fdu_info api.sysid api.tenantid fduid api.yconnector

  let instance_info fduid nodeid api =
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector

  let list api =
    Yaks_connector.Global.Actual.get_all_fdus api.sysid api.tenantid api.yconnector >>=
    Lwt_list.map_p (fun e ->
        Yaks_connector.Global.Actual.get_fdu_info api.sysid api.tenantid e api.yconnector
      )

end

module Image = struct

  let add (descriptor:FTypes.image) api =
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