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

  let plugins nodeid api =
    Yaks_connector.Global.Actual.get_node_plugins api.sysid api.tenantid nodeid api.yconnector

end


module Network = struct

  let add descriptor api =
    let netid = "descriptor.uuid" in
    Yaks_connector.Global.Actual.add_network api.sysid api.tenantid netid descriptor api.yconnector
    >>= fun _ -> Lwt.return true
  let remove netid  api =
    Yaks_connector.Global.Actual.remove_network api.sysid api.tenantid netid api.yconnector
    >>= fun _ -> Lwt.return true

  let list api =
    Yaks_connector.Global.Actual.get_all_networks api.sysid api.tenantid api.yconnector

end

module FDU = struct

  let define (descriptor:FTypes.fdu) nodeid ?(wait=true) api =
    ignore wait;
    let descriptor = {descriptor with status = Some "define"} in
    let fduid = descriptor.uuid in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let undeifne fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector
    >>= fun descriptor ->
    let descriptor = {descriptor with status = Some "undefine"} in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let configure  fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = Some "configure"} in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let clean fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = Some "clean"} in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let run fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = Some "run"} in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let stop fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = Some "stop"} in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let pause fduid nodeid ?(wait=true) api =
    ignore wait;
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector>>= fun descriptor ->
    let descriptor = {descriptor with status = Some "pause"} in
    Yaks_connector.Global.Actual.add_node_fdu api.sysid api.tenantid nodeid fduid descriptor api.yconnector
    >>= fun _ -> Lwt.return_true

  let migrate fduid nodeid destination ?(wait=true) api =
    ignore wait;
    Printf.printf "%s %s %s %b" fduid nodeid destination wait;
    ignore api.yconnector;
    Lwt.return true
  let info fduid nodeid api =
    Yaks_connector.Global.Actual.get_node_fdu_info api.sysid api.tenantid nodeid fduid api.yconnector


  let list ?(nodeid="*") api =
    Yaks_connector.Global.Actual.get_node_fdus api.sysid api.tenantid nodeid api.yconnector >>=
    Lwt_list.map_p (fun (_,_,f) -> Lwt.return f)

end
(*
module Image = struct

  let add descriptor api =
    ignore [descriptor; api];
    Lwt.return true
  let remove descriptor api =
    ignore [descriptor; api];
    Lwt.return true
  let list api =
    ignore api;
    Lwt.return []

end


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