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

type json = Yojson.Safe.json
let write_json = Yojson.Safe.write_json
let read_json = Yojson.Safe.read_json
let to_string = Yojson.Safe.to_string
let of_string = Yojson.Safe.from_string
let validate_json = Yojson.Safe.validate_json

(* type role =  Admin
            |Operator

   let role_of_string = function 
    | Admin -> "admin" | Operator -> "operator"

   let string_of_role = function 
    | "admin" -> Admin | "operator" -> Operator *)