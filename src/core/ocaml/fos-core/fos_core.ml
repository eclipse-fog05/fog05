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
module Str = Re.Str
module MVar = Apero.MVar_lwt

type configuration  = FAgentTypes.configuration

type system_status = {

  mutable tenants : FAgentTypes.tenant_type list;
  mutable users :  FAgentTypes.user_type list;
}

let contains s1 s2 =
  try
    let len = String.length s2 in
    for i = 0 to String.length s1 - len do
      if String.sub s1 i len = s2 then raise Exit
    done;
    false
  with Exit -> true

let replace input output = Str.global_replace (Str.regexp_string input) output

let rec read_from_ic s ic =
  try
    let s = s ^ input_line ic in
    read_from_ic s ic
  with
  | End_of_file -> s


let string_split token data =
  String.split_on_char token data

let read_file path =
  let ic = Pervasives.open_in path in
  let data = read_from_ic "" ic in
  let _ = close_in ic in
  data


let get_platform () =
  try
    let ic = Unix.open_process_in "uname" in
    let uname = input_line ic in
    let _ = close_in ic in
    uname
  with
  | _ -> "windows"


let get_unix_syslog_reporter () =
  match String.uppercase_ascii @@ get_platform () with
  | "LINUX" ->
    (Apero.Result.get (Logs_syslog_unix.unix_reporter ()))
  | "DARWIN" ->
    (Apero.Result.get (Logs_syslog_unix.unix_reporter ~socket:"/var/run/syslog"  ()))
  | "WINDOWS" -> (Apero.Result.get (Logs_syslog_unix.unix_reporter ()))
  | _ -> failwith "[ ERRO ] Operating System not recognized!"


let getuuid () =
  match String.uppercase_ascii @@ get_platform () with
  | "LINUX" ->
    let ic = Pervasives.open_in "/etc/machine-id" in
    let uuid = input_line ic in
    let _ = close_in ic in
    String.sub uuid 0 8 ^ "-" ^ String.sub uuid 8 4 ^ "-" ^ String.sub uuid 12 4 ^ "-" ^ String.sub uuid 16 4 ^ "-" ^ String.sub uuid 20 12
  | "DARWIN" ->
    let ic = Unix.open_process_in "ioreg -rd1 -c IOPlatformExpertDevice |  awk '/IOPlatformUUID/ { print $3; }'" in
    let uuid = input_line ic in
    let _ = close_in ic in
    String.sub uuid 1 ((String.length uuid)-2)
  | "WINDOWS" ->
    (* uuid_regex = r"UUID.+\r\r\n(.{0,36})"
       p = psutil.Popen('wmic csproduct get UUID'.split(), stdout=PIPE)
       uuid is group 1
    *)
    ""
  | _ -> failwith "[ ERRO ] Operating System not recognized!"


let load_config filename =
  let cont = read_file filename in
  let conf = FAgentTypes.configuration_of_string cont in
  let conf =
    match conf.agent.uuid with
    | Some _ -> conf
    | None -> {conf with agent = {conf.agent with uuid = Some( getuuid () )} }
  in
  conf


let config_to_json config =
  FAgentTypes.string_of_configuration config