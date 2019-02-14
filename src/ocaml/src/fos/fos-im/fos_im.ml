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

module IM_Types = Im
module IM_Json = Im
module IM_Validator = Im_v

module FAgentTypes = Agent_types
(* module FAgentTypesJson = Agent_types *)
module FAgentTypesValidator = Agent_types_v

module FTypes = Fos_types
(* module FTypesJson = Types *)
module FTypesValidator = Fos_types_v


let string_of_hv_type (hvtype:FTypes.hv_types) =
  match hvtype with
  | `BARE -> "native"
  | `KVM | `KVM_UK -> "kvm"
  | `XEN | `XEN_UK -> "xen"
  | `LXC -> "lxc"
  | `DOCKER -> "dock"