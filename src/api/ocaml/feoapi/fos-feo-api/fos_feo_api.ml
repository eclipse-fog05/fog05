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
open Errors

let ylocator = Apero.Option.get_or_default (Sys.getenv_opt "FOS_YAKS_ENDPOINT") "tcp/127.0.0.1:7887"
let ysystem = Apero.Option.get_or_default (Sys.getenv_opt "FOS_SYS_ID") "0"
let ytenant = Apero.Option.get_or_default (Sys.getenv_opt "FOS_TENANT_ID") "0"


type feoapi = {
  yconnector : Yaks_connector.connector;
  sysid : string;
  tenantid: string;
}







module Entity = struct

  let onboard (entity:User.Descriptors.Entity.descriptor) api =
    let%lwt nodes = Yaks_connector.Global.Actual.get_all_nodes api.sysid api.tenantid api.yconnector in
    let n = List.nth nodes (Random.int (List.length nodes)) in
    let%lwt res = Yaks_connector.Global.Actual.onboard_entity_from_node api.sysid api.tenantid n entity api.yconnector in
    match res.result with
    | Some js ->
      Lwt.return @@ User.Descriptors.Entity.descriptor_of_string (JSON.to_string js)
    | None -> raise @@ FException (`InternalError (`Msg ("Error during onboarding")))

  let instantiate entity_id api =
    let%lwt nodes = Yaks_connector.Global.Actual.get_all_nodes api.sysid api.tenantid api.yconnector in
    let n = List.nth nodes (Random.int (List.length nodes)) in
    let%lwt res = Yaks_connector.Global.Actual.instantiate_entity_from_node api.sysid api.tenantid n entity_id api.yconnector in
    match res.result with
    | Some js ->
      Lwt.return @@ Infra.Descriptors.Entity.record_of_string (JSON.to_string js)
    | None -> raise @@ FException (`InternalError (`Msg ("Error during onboarding")))


  let terminate inst_id api =
    let%lwt nodes = Yaks_connector.Global.Actual.get_all_nodes api.sysid api.tenantid api.yconnector in
    let n = List.nth nodes (Random.int (List.length nodes)) in
    let%lwt res = Yaks_connector.Global.Actual.terminate_entity_from_node api.sysid api.tenantid n inst_id api.yconnector in
    match res.result with
    | Some js ->
      Lwt.return @@ Infra.Descriptors.Entity.record_of_string (JSON.to_string js)
    | None -> raise @@ FException (`InternalError (`Msg ("Error during onboarding")))

  let offload entity_id api =
    let%lwt nodes = Yaks_connector.Global.Actual.get_all_nodes api.sysid api.tenantid api.yconnector in
    let n = List.nth nodes (Random.int (List.length nodes)) in
    let%lwt res = Yaks_connector.Global.Actual.offload_entity_from_node api.sysid api.tenantid n entity_id api.yconnector in
    match res.result with
    | Some js ->
      Lwt.return @@ User.Descriptors.Entity.descriptor_of_string (JSON.to_string js)
    | None -> raise @@ FException (`InternalError (`Msg ("Error during onboarding")))

  let get_entity_descriptor entity_id  api =
    let%lwt res  = Yaks_connector.Global.Actual.get_catalog_entity_info api.sysid api.tenantid entity_id api.yconnector in
    match res with
    | Some x -> Lwt.return x
    | None -> raise @@ FException (`InternalError (`Msg ("Atomic Entity not found")))

  let get_entity_instance_info instance_id  api =
    let%lwt res = Yaks_connector.Global.Actual.get_records_entity_instance_info api.sysid api.tenantid "*" instance_id api.yconnector in
    match res with
    | Some x -> Lwt.return x
    | None -> raise @@ FException (`InternalError (`Msg ("Atomic Entity instance not found")))


  let list api =
    Yaks_connector.Global.Actual.get_catalog_all_entities api.sysid api.tenantid api.yconnector


  let instance_list entity_id api =
    Yaks_connector.Global.Actual.get_records_all_entity_instances api.sysid api.tenantid entity_id api.yconnector

end


module FEOAPI = struct

  let connect ?(locator=ylocator) ?(sysid=ysystem) ?(tenantid=ytenant) () =
    let%lwt yconnector = Yaks_connector.get_connector_of_locator locator in
    Lwt.return { yconnector; sysid; tenantid}

  let close api =
    Yaks_connector.close_connector api.yconnector
end