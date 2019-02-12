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

open Lwt_io
open Fos_im


let print_network_info (net_info :Types_t.network) node_id =
  let _ = printf "+-------------------------------------------------------+\n" in
  let _ = printf "| UUID : %s\n" net_info.uuid  in
  let _ = printf "| Name: %s \n" net_info.name in
  let _ = printf "| Type: %s \n" net_info.network_type  in
  let _ = printf "| Node: %s \n" node_id in
  printf "+-------------------------------------------------------+\n"

let print_node_plugin (plugins : FTypes.plugin list) =
  Lwt_list.iter_p (
    fun (p:FTypes.plugin) ->
      let _ = printf "| Name: %s \t| UUID: %s\t | Type: %s\n" p.name p.uuid p.plugin_type in
      printf "+-------------------------------------------------------+\n";
  ) plugins

let print_node_info (node_info: FTypes.node_info) =
  (* TODO fix types, only one module for all types *)
  let _ = printf "+-------------------------------------------------------+\n" in
  let _ = printf "| Name: %s \t| UUID: %s\t\n" node_info.name node_info.uuid in
  let _ = printf "+-------------------------------------------------------+\n" in
  let cpus = node_info.cpu in
  let _ = printf "+------------------------CPU----------------------------+\n" in
  let _ = printf "| Total CPU %d\n" @@ List.length cpus in
  let _ = Lwt_list.iter_p (
      fun (c:FTypes.cpu_spec_type) ->
        let _ = printf "+-------------------------------------------------------+\n" in
        let _ = printf "| ARCH: %s\n" c.arch in
        let _ =  printf "| Model: %s\n" c.model in
        printf "| Frequency: %f\n" c.frequency;
    ) cpus in
  let _ = printf "+-------------------------------------------------------+\n" in
  let ram = node_info.ram in
  let _ = printf "| RAM: %f\n" ram.size in
  let _ = printf "+----------------------NETWORKS-------------------------+\n" in
  let networks = node_info.network in
  let _ = Lwt_list.iter_p (
      fun (n:FTypes.network_spec_type) ->
        let intf_conf = n.intf_configuration in
        let _ =  printf "| Interface: %s\n" n.intf_name in
        let _ =  printf "| MAC: %s \n" n.intf_mac_address in
        let _ =  printf "| type: %s\n" n.intf_type in
        let _ =  printf "| Default gateway: %b \n" n.default_gw in
        let _ =  printf "| Speed: %d\n" n.intf_speed in
        let _ =  printf "| IPV4: %s Netmask: %s Gateway: %s\n" intf_conf.ipv4_address intf_conf.ipv4_netmask  intf_conf.ipv4_gateway in
        printf "+-------------------------------------------------------+\n";
    ) networks in
  let acc = node_info.accelerator in
  let _ = Lwt_list.iter_p (
      fun (a:FTypes.accelerator_spec_type) ->
        let _ =  printf "| Name: %s\n" a.name in
        let _ =  printf "| HW Address: %s \n" a.hw_address in
        printf "+-------------------------------------------------------+\n";
    ) acc in
  let ios = node_info.io in
  Lwt_list.iter_p (
    fun (i:FTypes.io_spec_type) ->
      let _ =  printf "| Name: %s\n" i.name in
      let _ =  printf "| Type: %s \n" i.io_type; in
      let _ = printf "| File: %s\n" i.io_file in
      printf "+-------------------------------------------------------+\n";
  ) ios

let print_networks netlist =
  let _ = printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (nid, nodes, (manifest:FTypes.network) ) ->
      let _ = printf "| Name: %s \n| UUID: %s\n| Type: %s\n" manifest.name nid manifest.network_type in
      let _ = printf "| Nodes: " in
      let _ = Lwt_list.iter_p (fun e -> printf " %s " e ) nodes in
      printf "\n+-------------------------------------------------------+\n";
  ) netlist

let print_fdus aelist =
  let _ = printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (nid, fduid, (manifest:FTypes.atomic_entity) ) ->
      let _ = printf "| Name: %s \n| UUID: %s\n| Type: %s\n" manifest.name fduid manifest.atomic_type in
      let _ = printf "| Node: %s\n" nid in
      let _ = printf "| Status: %s\n" (Apero.Option.get_or_default manifest.status "ND") in
      printf "\n+-------------------------------------------------------+\n";
  ) aelist


let print_entities elist =
  let _ = printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (eid, (manifest:FTypes.entity), nets, atomics ) ->
      let _ = printf "| Name: %s \n| UUID: %s\n| Type: %s\n" manifest.name eid manifest.entity_type in
      let _ = printf "|- Networks:\n" in
      let _ = Lwt_list.iter_p (
          fun (nid, nodes, (manifest:FTypes.network) ) ->
            let _ = printf "| <-> Name: %s \n| <-> UUID: %s\n| <->  Type: %s\n" manifest.name nid manifest.network_type in
            let _ = printf "| <-> Nodes: " in
            let _ = Lwt_list.iter_p (fun e -> printf " %s " e ) nodes in
            printf "\n";
        ) nets
      in
      let _ = printf "|- Components:\n" in
      let _ = Lwt_list.iter_p (
          fun (aeid, nid, (manifest:FTypes.atomic_entity), instance_list ) ->
            let _ = printf "|----* Name: %s \n|----* UUID: %s\n|----* Type: %s\n" manifest.name aeid manifest.atomic_type in
            let _ = printf "|----* Node: %s\n" nid in
            let _ = printf "|----* Instances:\n" in
            let _ = Lwt_list.iter_p (fun (iid, (imanifest:FTypes.atomic_entity)) -> printf "|----*-> Instance ID %s\n|----*--> Status: %s" iid (Apero.Option.get_or_default imanifest.status "ND")) instance_list in
            printf "\n";
        ) atomics in
      printf "+-------------------------------------------------------+\n";
  ) elist