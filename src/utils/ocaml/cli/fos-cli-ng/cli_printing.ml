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


open Fos_im


let print_network_info (net_info :FTypes.network) node_id =
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  let%lwt _ = Lwt_io.printf "| UUID : %s\n" net_info.uuid  in
  let%lwt _ = Lwt_io.printf "| Name: %s \n" net_info.name in
  let%lwt _ = Lwt_io.printf "| Type: %s \n" net_info.network_type  in
  let%lwt _ = Lwt_io.printf "| Node: %s \n" node_id in
  Lwt_io.printf "+-------------------------------------------------------+\n"

let print_node_plugin (plugins : (FTypes.plugin option) list) =
  Lwt_list.iter_p (
    fun (p:FTypes.plugin option) ->
      let p = Apero.Option.get p in
      let%lwt _ = Lwt_io.printf "| Name: %s \t| UUID: %s\t | Type: %s\n" p.name p.uuid p.plugin_type in
      Lwt_io.printf "+-------------------------------------------------------+\n";
  ) plugins

let print_node_info (node_info: FTypes.node_info) =
  (* TODO fix types, only one module for all types *)
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  let%lwt _ = Lwt_io.printf "| Name: %s \t| UUID: %s\t\n" node_info.name node_info.uuid in
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  let cpus = node_info.cpu in
  let%lwt _ = Lwt_io.printf "+------------------------CPU----------------------------+\n" in
  let%lwt _ = Lwt_io.printf "| Total CPU %d\n" @@ List.length cpus in
  let _ = Lwt_list.iter_p (
      fun (c:FTypes.cpu_spec_type) ->
        let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
        let%lwt _ = Lwt_io.printf "| ARCH: %s\n" c.arch in
        let%lwt _ = Lwt_io.printf "| Model: %s\n" c.model in
        Lwt_io.printf "| Frequency: %f\n" c.frequency;
    ) cpus in
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  let ram = node_info.ram in
  let%lwt _ = Lwt_io.printf "| RAM: %f\n" ram.size in
  let%lwt _ = Lwt_io.printf "+----------------------NETWORKS-------------------------+\n" in
  let networks = node_info.network in
  let _ = Lwt_list.iter_p (
      fun (n:FTypes.network_spec_type) ->
        let intf_conf = n.intf_configuration in
        let%lwt _ = Lwt_io.printf "| Interface: %s\n" n.intf_name in
        let%lwt _ = Lwt_io.printf "| MAC: %s \n" n.intf_mac_address in
        let%lwt _ = Lwt_io.printf "| type: %s\n" n.intf_type in
        let%lwt _ = Lwt_io.printf "| Default gateway: %b \n" n.default_gw in
        let%lwt _ = Lwt_io.printf "| Speed: %d\n" n.intf_speed in
        let%lwt _ = Lwt_io.printf "| IPV4: %s Netmask: %s Gateway: %s\n" intf_conf.ipv4_address intf_conf.ipv4_netmask  intf_conf.ipv4_gateway in
        Lwt_io.printf "+-------------------------------------------------------+\n";
    ) networks in
  let acc = node_info.accelerator in
  let _ = Lwt_list.iter_p (
      fun (a:FTypes.accelerator_spec_type) ->
        let%lwt _ = Lwt_io.printf "| Name: %s\n" a.name in
        let%lwt _ = Lwt_io.printf "| HW Address: %s \n" a.hw_address in
        Lwt_io.printf "+-------------------------------------------------------+\n";
    ) acc in
  let ios = node_info.io in
  Lwt_list.iter_p (
    fun (i:FTypes.io_spec_type) ->
      let%lwt _ = Lwt_io.printf "| Name: %s\n" i.name in
      let%lwt _ = Lwt_io.printf "| Type: %s \n" i.io_type; in
      let%lwt _ = Lwt_io.printf "| File: %s\n" i.io_file in
      Lwt_io.printf "+-------------------------------------------------------+\n";
  ) ios

let print_networks (netlist:FTypes.virtual_network list) =
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (manifest:FTypes.virtual_network) ->
      Lwt_io.printf "| Name: %s \n| UUID: %s\n| Mgmt: %b\n" manifest.name manifest.uuid manifest.is_mgmt
  ) netlist

let print_images (imglist:Base.Descriptors.FDU.image list) =
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (descr:Base.Descriptors.FDU.image) ->
      Lwt_io.printf "| Name: %s \n| UUID: %s\n| URI: %s\n| Checksum: %s\n| Format: %s\n"
        (Apero.Option.get_or_default descr.name "ND") (Apero.Option.get_or_default descr.uuid "ND")
        descr.uri descr.checksum descr.format

  ) imglist

let print_fdus aelist =
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (_, fduid, (desc:User.Descriptors.FDU.descriptor) ) ->
      let%lwt _ = Lwt_io.printf "| Name: %s \n| UUID: %s\n| Type: %s\n" desc.name fduid (Fos_im.string_of_hv_type desc.hypervisor) in
      (* let%lwt _ = Lwt_io.printf "| Node: %s\n" nid in
         let%lwt _ = Lwt_io.printf "| Status: %s\n" (Apero.Option.get_or_default manifest.status "ND") in *)
      Lwt_io.printf "\n+-------------------------------------------------------+\n";
  ) aelist

let print_fdu_instances ilist  =
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_s (fun (nid, instances) ->
      let%lwt _ = Lwt_io.printf "| Node %s\n" nid in
      Lwt_list.iter_p (
        fun iid ->
          let%lwt _ = Lwt_io.printf "|   + UUID: %s\n" iid in
          (* let%lwt _ = Lwt_io.printf "|  UUID: %s\n| Status: %s\n" (Apero.Option.get record.uuid) record.status in *)
          (* let%lwt _ = Lwt_io.printf "| Node: %s\n" nid in
             let%lwt _ = Lwt_io.printf "| Status: %s\n" (Apero.Option.get_or_default manifest.status "ND") in *)
          Lwt_io.printf "\n+-------------------------------------------------------+\n";
      ) instances

    ) ilist



let print_entities elist =
  let%lwt _ = Lwt_io.printf "+-------------------------------------------------------+\n" in
  Lwt_list.iter_p (
    fun (eid, (manifest:FTypes.entity), nets, atomics ) ->
      let%lwt _ = Lwt_io.printf "| Name: %s \n| UUID: %s\n| Type: %s\n" manifest.name eid manifest.entity_type in
      let%lwt _ = Lwt_io.printf "|- Networks:\n" in
      let _ = Lwt_list.iter_p (
          fun (nid, nodes, (manifest:FTypes.network) ) ->
            let%lwt _ = Lwt_io.printf "| <-> Name: %s \n| <-> UUID: %s\n| <->  Type: %s\n" manifest.name nid manifest.network_type in
            let%lwt _ = Lwt_io.printf "| <-> Nodes: " in
            let _ = Lwt_list.iter_p (fun e -> Lwt_io.printf " %s " e ) nodes in
            Lwt_io.printf "\n";
        ) nets
      in
      let%lwt _ = Lwt_io.printf "|- Components:\n" in
      let _ = Lwt_list.iter_p (
          fun (aeid, nid, (manifest:FTypes.atomic_entity), instance_list ) ->
            let%lwt _ = Lwt_io.printf "|----* Name: %s \n|----* UUID: %s\n|----* Type: %s\n" manifest.name aeid manifest.atomic_type in
            let%lwt _ = Lwt_io.printf "|----* Node: %s\n" nid in
            let%lwt _ = Lwt_io.printf "|----* Instances:\n" in
            let _ = Lwt_list.iter_p (fun (iid, (imanifest:FTypes.atomic_entity)) -> Lwt_io.printf "|----*-> Instance ID %s\n|----*--> Status: %s" iid (Apero.Option.get_or_default imanifest.status "ND")) instance_list in
            Lwt_io.printf "\n";
        ) atomics in
      Lwt_io.printf "+-------------------------------------------------------+\n";
  ) elist