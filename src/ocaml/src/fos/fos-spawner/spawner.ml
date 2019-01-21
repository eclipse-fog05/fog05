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

open Fos_core
open Lwt.Infix

module PluginMap = Map.Make(String)


type state = {
  yaks : Yaks_connector.connector
;  mutable plugins : (FTypes.plugin * Lwt_process.process_full) PluginMap.t
; conf : Fos_core.configuration
; lock : int MVar.t
}

type t = state MVar.t


let max_tentatives = 5


let rec print_plugin_output process =  Lwt_io.read_line_opt process#stdout
  >>= fun line ->
  (match line with   | None -> Lwt.return_unit
                     | Some s -> Lwt_io.printf "{PLUGIN OUTPUT} - %s\n" s)
  >>= fun _ -> print_plugin_output process



let rec check_plugins_pid state process cmd (manifest:FTypes.plugin) n =
  let open Unix in
  process#status >>= fun s ->
  match s with
  | WEXITED 2 | WSIGNALED 2 ->    let%lwt _ = Lwt_io.printf "[SPAWNER]: Plugin process %d extied, Killed by SIGINT not going to restart\n" process#pid in
    Lwt.return_unit
  | _ ->    if n < max_tentatives then      (        let%lwt _ = Lwt_io.printf "[SPAWNER]: Plugin process %d extied, launch number %d\n" process#pid n in
                                                     let p = Lwt_process.open_process_full cmd in
                                                     MVar.guarded state @@ fun self ->
                                                     let _ = check_plugins_pid state p cmd manifest (n+1) in
                                                     let _ = print_plugin_output p in
                                                     MVar.return () {self with plugins = PluginMap.add manifest.uuid (manifest,p) self.plugins})
    else
      let%lwt _ = Lwt_io.printf "[SPAWNER]: Plugin process %d extied, no more tentatives are available\n" process#pid in
      MVar.guarded state @@ fun self ->
      Yaks_connector.Local.Actual.remove_node_plugin (Apero.Option.get self.conf.agent.uuid) manifest.uuid self.yaks
      >>= fun _ ->
      MVar.return () {self with plugins = PluginMap.remove manifest.uuid  self.plugins}


let load_plugin state (manifest:FTypes.plugin) =
  MVar.read state >>= fun self ->
  let ya = self.conf.agent.yaks in
  let%lwt _ = Lwt_io.printf "Manifest: %s\n" @@ FTypesJson.string_of_plugin manifest in
  let pl = Printf.sprintf "%s/%s/%s_plugin \"%s\" %s\n" self.conf.plugins.plugin_path manifest.name manifest.name ya (Apero.Option.get self.conf.agent.uuid)  in
  MVar.guarded state @@ fun self ->
  let%lwt _ = Lwt_io.printf "CLI FOR PLUGIN IS %s" pl in
  let cmd = Lwt_process.shell pl in
  let p = Lwt_process.open_process_full cmd in
  let _ = check_plugins_pid state p cmd manifest 0 in
  let _ = print_plugin_output p in
  let%lwt _ = Yaks_connector.Local.Actual.add_node_plugin (Apero.Option.get self.conf.agent.uuid) manifest self.yaks in
  MVar.return (manifest, p) {self with plugins = PluginMap.add manifest.uuid (manifest,p) self.plugins}

let load_plugin_from_file state name =
  MVar.read state >>= fun self ->
  let pl_manifest = FTypesJson.plugin_of_string @@ read_file (Printf.sprintf "%s/%s/%s_plugin.json" self.conf.plugins.plugin_path name name) in
  load_plugin state pl_manifest


let plugin_listener _ data =
  Lwt_io.printf ">>>> [SPAWNER] OBSERVER\n"
  >>= fun _ -> Lwt_list.iter_p (fun (k,v) ->
      Lwt_io.printf ">>>> [SPAWNER] [OBS] K %s - V: %s\n"  (Yaks_types.Path.to_string k) (Yaks_types.Value.to_string v)
    ) data

let remove_plugin state pluginid process =
  process#kill Sys.sigint;
  MVar.guarded state @@ fun self ->
  Yaks_connector.Local.Actual.remove_node_plugin (Apero.Option.get self.conf.agent.uuid) pluginid self.yaks
  >>= fun _ ->
  MVar.return () {self with plugins = PluginMap.remove pluginid  self.plugins}


let wait_os_plugin (manifest: FTypes.plugin) state =
  MVar.read state >>= fun self ->
  let wait_os_plugin_cb state (pl:Types_t.plugin) =
    MVar.read state >>= fun self ->
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - ##############\n" in
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - Wait OS plugin load - Received update\n" in
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - Status : %s\n" @@ Apero.Option.get pl.status  in
    match Apero.Option.get pl.status with
    | "running" ->
      MVar.put self.lock 1
    | _ ->
      let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - OS PLUGIN NOT READY!\n"  in
      Lwt.return_unit
  in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_plugin (Apero.Option.get self.conf.agent.uuid) manifest.uuid (wait_os_plugin_cb state) self.yaks in
  MVar.read self.lock >>= fun _ -> Lwt.return_unit


let load_os_plugin state =
  MVar.read state >>= fun self ->
  match String.uppercase_ascii @@ get_platform () with
  | "LINUX" ->
    let%lwt _ = Lwt_io.printf "Running on Linux\n" in
    let pl_manifest = FTypesJson.plugin_of_string @@ read_file (Printf.sprintf "%s/linux/linux_plugin.json" self.conf.plugins.plugin_path) in
    load_plugin state pl_manifest
    >>= fun _ ->
    wait_os_plugin pl_manifest state
    >>= Lwt.return
  | "DARWIN" ->
    let%lwt _ = Lwt_io.printf "Running on macOS\n" in
    let pl_manifest = FTypesJson.plugin_of_string @@ read_file (Printf.sprintf "%s/macos/macos_plugin.json" self.conf.plugins.plugin_path) in
    load_plugin state pl_manifest
    >>= fun _ ->
    wait_os_plugin pl_manifest state
    >>= Lwt.return
  (* let _ = Lwt_io.printf "Running on Darwin" in () *)
  | "WINDOWS" ->
    failwith "[ ERRO ] Windows not yet supported!"
  (* let _ = Lwt_io.printf "Running on Windows" in () *)
  | _ -> failwith "[ ERRO ] Operating System not recognized!"


let main_loop state promise =  Lwt.join [promise] >>= fun _ ->
  MVar.read state >>= fun self ->
  Lwt_list.iter_p (fun (id,(_,p)) -> remove_plugin state id p) (PluginMap.bindings self.plugins)
  >>= fun _ -> Yaks_connector.close_connector self.yaks
  >>= fun _ -> Lwt_io.printf "Exiting after SIGINT\n"
  >>= fun _ -> exit 2

let register_handlers completer () =
  Lwt_unix.on_signal Sys.sigint (
    fun _ -> Lwt.wakeup_later completer ())

let main _ cpath =
  let%lwt _ = Lwt_io.printf "Spawner main\n" in
  let%lwt _ = Lwt_io.printf "Load configuration\n" in
  let conf = load_config cpath in
  let%lwt _ = Lwt_io.printf "Accessing YAKS on %s\n" conf.agent.yaks in
  List.iter (fun e -> let _ = Lwt_io.printf "PL: %s\n" e in ()) (Apero.Option.get_or_default conf.plugins.auto []);
  let%lwt yaks = Yaks_connector.get_connector conf in
  let pm = PluginMap.empty in
  let state = MVar.create {yaks; plugins = pm; conf; lock= MVar.create_empty () } in
  let cb_ld state (pl:Types_t.plugin) =
    MVar.read state >>= fun _ ->
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - PLUGIN CB-LD - ##############\n" in
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - PLUGIN CB-LD - Received plugin\n" in
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - PLUGIN CB-LD - Name: %s\n" pl.name in
    let%lwt _ = Lwt_io.printf  "[FOS-SPAWNER] - PLUGIN CB-LD -  I'm the spwner I load the plugin \n" in
    Lwt.return_unit
    (* Yaks_connector.Global.Actual.add_node_plugin sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.conf.agent.uuid) pl self.yaks >>= Lwt.return *)
  in
  let%lwt _ = Yaks_connector.Local.Desired.observe_node_plugins (Apero.Option.get conf.agent.uuid) (cb_ld state) yaks in
  load_os_plugin state
  >>= fun _ ->
  List.iter (fun e -> let _ = load_plugin_from_file state e in ()) (Apero.Option.get_or_default conf.plugins.auto []);
  let p,c = Lwt.wait () in
  let _ = register_handlers c () in
  main_loop state p


let start verbose_flag daemon_flag configuration_path =
  match daemon_flag with
  | true ->
    let pid = Unix.fork () in
    if pid=0 then
      begin
        let tmp = Filename.get_temp_dir_name () in
        let pid_file = Filename.concat tmp "fos_agent.pid" in
        let agent_out_file = Filename.concat tmp "fos_agent.out" in
        let agent_err_file = Filename.concat tmp "fos_agent.err" in
        let mpid = Unix.getpid () in
        let pid_out = open_out pid_file in
        ignore @@ Printf.fprintf pid_out "%d" mpid;
        ignore @@ close_out pid_out;
        let file_out = open_out agent_out_file in
        let file_err = open_out agent_err_file in
        ignore @@ Unix.dup2 (Unix.descr_of_out_channel file_out) Unix.stdout;
        ignore @@ Unix.dup2 (Unix.descr_of_out_channel file_err) Unix.stderr;
        Lwt_main.run @@ main verbose_flag configuration_path
      end
    else exit 0
  | false -> Lwt_main.run @@ main verbose_flag configuration_path

let verbose =
  let doc = "Set verbose output." in
  Cmdliner.Arg.(value & flag & info ["v";"verbose"] ~doc)

let daemon =
  let doc = "Set daemon" in
  Cmdliner.Arg.(value & flag & info ["d";"daemon"] ~doc)

let config =
  let doc = "Configuration file path" in
  Cmdliner.Arg.(value & opt string "/usr/local/share/fog05/agent.ini" & info ["c";"conf"] ~doc)


let spawner_t = Cmdliner.Term.(const start $ verbose $ daemon  $ config)

let info =
  let doc = "fog05 | Plugin Spawner" in
  let man = [
    `S Cmdliner.Manpage.s_bugs;
    `P "Email bug reports to fog05-dev at eclipse.org>." ]
  in
  Cmdliner.Term.info "spawner" ~version:"%%VERSION%%" ~doc ~exits:Cmdliner.Term.default_exits ~man

let () = Cmdliner.Term.exit @@ Cmdliner.Term.eval (spawner_t, info)
let () = Cmdliner.Term.exit @@ Cmdliner.Term.eval (spawner_t, info)
let info =
  let doc = "fog05 | Plugin Spawner" in
  let man = [
    `S Cmdliner.Manpage.s_bugs;
    `P "Email bug reports to fog05-dev at eclipse.org>." ]
  in
  Cmdliner.Term.info "spawner" ~version:"%%VERSION%%" ~doc ~exits:Cmdliner.Term.default_exits ~man

let () = Cmdliner.Term.exit @@ Cmdliner.Term.eval (spawner_t, info)
