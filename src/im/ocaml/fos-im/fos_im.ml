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

(* module MEC_Types = Im
   module MEC_Json = Im
   module MEC_Validator = Im_v *)

module FAgentTypes = Agent_types
(* module FAgentTypesJson = Agent_types *)
module FAgentTypesValidator = Agent_types_v

module FTypes = Fos_types
module FTypesRecord = Fos_records_types
module FTypesValidator = Fos_types_v
module JSON = Abs_json



module Errors = Fos_errors
module FDU = Fdu

module MEC = Mec
module NFV = Nfv
module MEC_Interfaces = Mec_interfaces


module ConstraintMap = Map.Make(String)

let string_of_hv_type (kind:Fdu.hv_kind) =
  match kind with
  | `BARE -> "native"
  | `KVM | `KVM_UK -> "kvm"
  | `XEN | `XEN_UK -> "xen"
  | `LXD -> "lxd"
  | `DOCKER -> "dock"
  | `MCU -> "mcu"

let hv_type_of_string hv =
  match hv with
  | "native" -> `BARE
  | "kvm" -> `KVM
  | "xen" -> `XEN
  | "lxd" -> `LXD
  | "dock" -> `DOCKER
  | "mcu" -> `MCU
  | _ -> raise @@ Errors.FException (`InformationModelError (`Msg ( Printf.sprintf "Hypervisor %s not recognized" hv)))



let fdu_of_mecapp (mecapp:MEC.appd_descriptor) =
  let uuid = mecapp.id in
  let name = mecapp.name in
  let hypervisor = List.hd mecapp.sw_image_descriptor.supported_virtualisation_environment |> hv_type_of_string in
  let migration_kind = `LIVE in
  let io_ports = [] in
  let depends_on = [] in
  let interfaces = [
    FDU.{
      name = "eth0";
      is_mgmt = false;
      if_type = `INTERNAL;
      mac_address = None;
      virtual_interface = {
        intf_type = `VIRTIO;
        vpci = "0:0:0";
        bandwidth = 100;
      };
      cp_id = None
    };
    FDU.{
      name = "eth1";
      is_mgmt = true;
      if_type = `INTERNAL;
      mac_address = None;
      virtual_interface = {
        intf_type = `VIRTIO;
        vpci = "0:0:0";
        bandwidth = 100;
      };
      cp_id = None
    };
  ]
  in
  let computation_requirements = FDU.{
      cpu_arch = mecapp.virtual_compute_descriptor.virtual_cpu.cpu_architecture;
      cpu_min_freq = Apero.Option.get_or_default mecapp.virtual_compute_descriptor.virtual_cpu.virtual_cpu_clock 0;
      cpu_min_count = mecapp.virtual_compute_descriptor.virtual_cpu.num_virtual_cpu;
      ram_size_mb = float_of_int @@ mecapp.virtual_compute_descriptor.virtual_memory.virtual_mem_size;
      storage_size_gb =  float_of_int @@ mecapp.sw_image_descriptor.min_disk;
      uuid = None;
      name = None;
      gpu_min_count = None;
      fpga_min_count = None;
      duty_cycle = None;
    }
  in
  let image = FDU.{
      uuid = None;
      name = None;
      uri = mecapp.sw_image_descriptor.id;
      checksum = mecapp.sw_image_descriptor.checksum;
      format = mecapp.sw_image_descriptor.disk_format;
    }
  in
  FDU.create_descriptor ~uuid ~name ~hypervisor ~image ~computation_requirements ~migration_kind ~io_ports ~depends_on ~interfaces