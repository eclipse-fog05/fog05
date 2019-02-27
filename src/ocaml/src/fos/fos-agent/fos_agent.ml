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
open Lwt.Infix
open Fos_core
open Fos_im

type state = {
  yaks : Yaks_connector.connector
; spawner : Lwt_process.process_full option
; configuration : Fos_core.configuration
; cli_parameters : string list
; completer : unit Lwt.u
; constrained_nodes : string ConstraintMap.t
}

type t = state MVar.t

let max_tentatives = 5

let register_handlers completer () =
  let _ = Lwt_unix.on_signal Sys.sigint (
      fun _ -> Lwt.wakeup_later completer ())
  in
  Lwt_unix.on_signal Sys.sigterm (
    fun _ -> Lwt.wakeup_later completer ())

let rec print_spawner_output process =
  Lwt_io.read_line_opt process#stdout
  >>= fun line ->
  (match line with
   | None -> Lwt.return_unit
   | Some s -> Lwt_io.printf "{SPAWNER OUTPUT} - %s\n" s)
  >>= fun _ -> print_spawner_output process

let load_spawner path state =
  MVar.guarded state @@ fun self ->
  let cmd = Lwt_process.shell (Printf.sprintf "%s -c %s -v" path (List.nth self.cli_parameters 0))in
  let p = Lwt_process.open_process_full cmd in
  MVar.return (p, cmd) {self with spawner = Some p}


let rec check_spawner_pid process cmd state n =
  let open Unix in
  process#status >>= fun s ->
  match s with
  | WEXITED 2 | WSIGNALED 2 ->
    let%lwt _ = Lwt_io.printf "[FOSAGENT]: Spawner PID: %d died, Killed by SIGINT\n" process#pid in
    Lwt.return_unit
  | _ ->
    if n < max_tentatives then
      (
        let%lwt _ = Lwt_io.printf "[FOSAGENT]: Spawner process %d extied, launch number %d\n" process#pid n in
        let p = Lwt_process.open_process_full cmd in
        MVar.guarded state @@ fun self ->
        let _ = check_spawner_pid p cmd state (n+1) in
        MVar.return () {self with spawner = Some p})
    else
      let%lwt _ = Lwt_io.printf "[FOSAGENT]: Spawner process %d extied, no more tentatives are available\n" process#pid in
      MVar.guarded state @@ fun self ->
      Lwt.wakeup_later self.completer ();
      MVar.return () {self with spawner = None}



let react_to_plugins loader data =
  ignore loader;
  Lwt_io.printf ">>>> [FOS] OBSERVER\n"
  >>= fun _ -> Lwt_list.iter_p (fun (k,v) ->
      Lwt_io.printf ">>>> [FOS] [OBS] K %s - V: %s\n"  (Yaks_types.Path.to_string k) (Yaks_types.Value.to_string v)
    ) data



let main_loop state promise =
  let _ = Lwt_io.printf "[FOSAGENT] Up & Running!\n" in
  let _ =  Lwt_io.flush_all () in
  Lwt.join [promise] >>= fun _ ->
  MVar.guarded state @@ fun self ->
  let self = match self.spawner with
    | Some p ->
      p#kill Sys.sigint;
      {self with spawner = None}
    | None ->   self
  in
  Yaks_connector.close_connector self.yaks
  >>= fun _ ->
  MVar.return (Lwt_io.printf "Bye!\n") self



let agent verbose_flag debug_flag configuration =
  let level, reporter = (match verbose_flag with
      | true -> Apero.Result.get @@ Logs.level_of_string "debug" ,  (Logs_fmt.reporter ())
      | false -> Apero.Result.get @@ Logs.level_of_string "error",  (Fos_core.get_unix_syslog_reporter ())
    )
  in
  Logs.set_level level;
  Logs.set_reporter reporter;
  let prom,c = Lwt.wait () in
  let _ = register_handlers c () in
  let conf = load_config configuration in
  let conf = match conf.agent.system with
    | Some _ -> conf
    | None -> {conf with agent = {conf.agent with uuid = Some( Yaks_connector.default_system_id )} }
  in
  let mpid = Unix.getpid () in
  let pid_out = open_out conf.agent.pid_file in
  ignore @@ Printf.fprintf pid_out "%d" mpid;
  ignore @@ close_out pid_out;
  let sys_id = Apero.Option.get @@ conf.agent.system in
  let uuid = (Apero.Option.get conf.agent.uuid) in
  let plugin_path = conf.plugins.plugin_path in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - DEBUG IS: %b"  debug_flag) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - ##############") in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - Agent Configuration is:") in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - SYSID: %s" sys_id) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - UUID: %s"  uuid) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - LLDPD: %b" conf.agent.enable_lldp) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - SPAWNER: %b" conf.agent.enable_spawner) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - PID FILE: %s" conf.agent.pid_file) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - YAKS Server: %s" conf.agent.yaks) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - Plugin Directory: %s" plugin_path) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - AUTOLOAD: %b" conf.plugins.autoload) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - Plugins:") in
  List.iter (fun p -> ignore @@ Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - %s" p )) (Apero.Option.get_or_default conf.plugins.auto []);
  (* let sys_info = system_info sys_id uuid in *)
  let%lwt yaks = Yaks_connector.get_connector conf in
  let cli_parameters = [configuration] in
  let self = {yaks; configuration = conf; cli_parameters; spawner = None; completer = c; constrained_nodes = ConstraintMap.empty} in
  let state = MVar.create self in
  let%lwt _ = MVar.read state >>= fun state ->
    Yaks_connector.Global.Actual.add_node_configuration sys_id Yaks_connector.default_tenant_id uuid conf state.yaks
  in
  let%lwt _ = MVar.read state >>= fun state ->
    Yaks_connector.Local.Actual.add_node_configuration uuid conf state.yaks
  in
  (* Evals *)
  let eval_get_fdu_info self (props:Apero.properties) =
    MVar.read self >>= fun state ->
    let fdu_uuid = Apero.Option.get @@ Apero.Properties.get "fdu_uuid" props in
    let%lwt descriptor = Yaks_connector.Global.Actual.get_fdu_info sys_id Yaks_connector.default_tenant_id fdu_uuid state.yaks in
    let js = FAgentTypes.json_of_string @@ FTypes.string_of_fdu descriptor in
    let eval_res = FAgentTypes.{result = Some js ; error=None} in
    Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  (* Listeners *)
  (* Global Desired *)
  let cb_gd_plugin self (pl:FTypes.plugin) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN - Received plugin") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN - Name: %s" pl.name) in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN -  Calling the spawner by writing this on local desired") in
    Yaks_connector.Local.Desired.add_node_plugin (Apero.Option.get self.configuration.agent.uuid) pl self.yaks >>= Lwt.return
  in
  let cb_gd_fdu self (fdu:FTypes.fdu) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - FDU Updated! Advertising on GA") in
    Yaks_connector.Global.Actual.add_fdu_info sys_id Yaks_connector.default_tenant_id fdu.uuid fdu self.yaks >>= Lwt.return
  in
  let cb_gd_node_fdu self (fdu:FTypesRecord.fdu) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NODE-FDU - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NODE-FDU - FDU Updated! Agent will call the right plugin!") in
    let%lwt fdu_d = Yaks_connector.Global.Actual.get_fdu_info sys_id Yaks_connector.default_tenant_id fdu.fdu_uuid self.yaks in
    let fdu_type = Fos_im.string_of_hv_type fdu_d.hypervisor in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - FDU Type %s" fdu_type) in
    let%lwt plugins = Yaks_connector.Local.Actual.get_node_plugins (Apero.Option.get self.configuration.agent.uuid) self.yaks in
    Lwt_list.iter_p (fun e ->
        let%lwt pl = Yaks_connector.Local.Actual.get_node_plugin (Apero.Option.get self.configuration.agent.uuid) e self.yaks in
        if String.uppercase_ascii (pl.name) = String.uppercase_ascii (fdu_type) then
          let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - Calling %s plugin" pl.name) in
          Yaks_connector.Local.Desired.add_node_fdu (Apero.Option.get self.configuration.agent.uuid) pl.uuid fdu.fdu_uuid fdu self.yaks >>= Lwt.return
        else
          Lwt.return_unit
      ) plugins >>= Lwt.return
  in
  let cb_gd_net self (net:FTypes.virtual_network) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET Updated! Agent will call the right plugin!") in
    let%lwt plugins = Yaks_connector.Local.Actual.get_node_plugins (Apero.Option.get self.configuration.agent.uuid) self.yaks in
    let%lwt p = Lwt_list.find_s (fun e ->
        let%lwt pl = Yaks_connector.Local.Actual.get_node_plugin (Apero.Option.get self.configuration.agent.uuid) e self.yaks in
        match String.lowercase_ascii pl.plugin_type with
        | "network" -> Lwt.return_true
        | _ -> Lwt.return_false
      ) plugins
    in
    Yaks_connector.Local.Desired.add_node_network (Apero.Option.get self.configuration.agent.uuid) p net.uuid net self.yaks
    >>= Lwt.return
  in
  let cb_gd_cp self (cp:FTypes.connection_point) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CP - CP Updated! Agent will call the right plugin!") in
    let%lwt plugins = Yaks_connector.Local.Actual.get_node_plugins (Apero.Option.get self.configuration.agent.uuid) self.yaks in
    let%lwt p = Lwt_list.find_s (fun e ->
        let%lwt pl = Yaks_connector.Local.Actual.get_node_plugin (Apero.Option.get self.configuration.agent.uuid) e self.yaks in
        match String.lowercase_ascii pl.plugin_type with
        | "network" -> Lwt.return_true
        | _ -> Lwt.return_false
      ) plugins
    in
    Yaks_connector.Local.Desired.add_node_port (Apero.Option.get self.configuration.agent.uuid) p cp.uuid cp self.yaks
    >>= Lwt.return
  in
  (* Local Actual *)
  let cb_la_net self (net:FTypes.virtual_network) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NET - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NET - vNET Updated! Advertising on GA") in
    (* match net.status with
       | Some "remove" -> Yaks_connector.Global.Actual.remove_network sys_id Yaks_connector.default_tenant_id net.uuid self.yaks
       | _ -> *)
    Yaks_connector.Global.Actual.add_network sys_id Yaks_connector.default_tenant_id net.uuid net self.yaks >>= Lwt.return
  in
  let cb_la_cp self (cp:FTypes.connection_point) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-CP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-CP - CP Updated! Advertising on GA") in
    (* match cp.status with
       | Some "remove" -> Yaks_connector.Global.Actual.remove_port sys_id Yaks_connector.default_tenant_id cp.uuid self.yaks
       | _ -> *)
    Yaks_connector.Global.Actual.add_port sys_id Yaks_connector.default_tenant_id cp.uuid cp self.yaks >>= Lwt.return
  in
  let cb_la_plugin self (pl:FTypes.plugin) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN - Received plugin") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN - Name: %s" pl.name) in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN -  Plugin loaded advertising on GA") in
    Yaks_connector.Global.Actual.add_node_plugin sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) pl self.yaks >>= Lwt.return
  in
  let cb_la_ni self (ni:FTypes.node_info) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NI - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NI - Updated node info advertising of GA") in
    Yaks_connector.Global.Actual.add_node_info sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) ni self.yaks >>= Lwt.return
  in
  let cb_la_node_fdu self (fdu:FTypesRecord.fdu) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NODE-FDU - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NODE-FDU - FDU Updated! Advertising on GA") in
    match fdu.status with
    | `UNDEFINE -> Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) fdu.fdu_uuid self.yaks
    | _ ->
      Yaks_connector.Global.Actual.add_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) fdu.fdu_uuid fdu self.yaks >>= Lwt.return
  in
  (* Constrained Nodes *)
  let cb_lac_node_fdu self nodeid (fdu:FTypesRecord.fdu) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-FDU - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LACs-NODE-FDU - FDU Updated! Advertising on GA") in
    match fdu.status with
    | `UNDEFINE -> Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id nodeid fdu.fdu_uuid self.yaks
    | _ ->
      Yaks_connector.Global.Actual.add_node_fdu sys_id Yaks_connector.default_tenant_id nodeid fdu.fdu_uuid fdu self.yaks >>= Lwt.return
  in
  let cb_lac_plugin self nodeid (pl:FTypes.plugin) =
    MVar.read self >>= fun self ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN - Received plugin") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN - Name: %s" pl.name) in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN -  Plugin loaded advertising on GA") in
    Yaks_connector.Global.Actual.add_node_plugin sys_id Yaks_connector.default_tenant_id nodeid pl self.yaks >>= Lwt.return
  in
  (* let cb_lac_node_configuration self nodeid (pl:FTypes.node_info) =
     MVar.read self >>= fun self ->
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF - ##############") in
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF - Received plugin") in
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF - Name: %s" pl.name) in
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF -  Plugin loaded advertising on GA") in
     Yaks_connector.Global.Actual.add_node_configuration sys_id Yaks_connector.default_tenant_id nodeid pl self.yaks >>= Lwt.return
     in *)
  let cb_lac_nodes self (ni:FTypes.node_info) =
    MVar.read self >>= fun state ->
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NI - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NI - Updated node info advertising of GA") in
    (* TODO should generate the NodeID *)
    Yaks_connector.Global.Actual.add_node_info sys_id Yaks_connector.default_tenant_id "" ni state.yaks
    >>= fun _ ->  Yaks_connector.LocalConstraint.Actual.observe_node_plugins uuid (cb_lac_plugin self  ni.uuid ) yaks
    >>= fun _ ->  Yaks_connector.LocalConstraint.Actual.observe_node_fdu uuid (cb_lac_node_fdu self ni.uuid) yaks
    >>= fun _ -> Lwt.return_unit
  in
  (* Registering Evals *)
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_fdu_info" (eval_get_fdu_info state) yaks in
  (* Registering listeners *)
  let%lwt _ = Yaks_connector.Global.Desired.observe_node_plugins sys_id Yaks_connector.default_tenant_id uuid (cb_gd_plugin state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_fdu sys_id Yaks_connector.default_tenant_id (cb_gd_fdu state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_node_fdu sys_id Yaks_connector.default_tenant_id uuid (cb_gd_node_fdu state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_network sys_id Yaks_connector.default_tenant_id (cb_gd_net state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_ports sys_id Yaks_connector.default_tenant_id (cb_gd_cp state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_plugins uuid (cb_la_plugin state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_info uuid (cb_la_ni state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_fdu uuid (cb_la_node_fdu state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_network uuid (cb_la_net state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_port uuid (cb_la_cp state) yaks in
  let%lwt _ = Yaks_connector.LocalConstraint.Actual.observe_nodes (cb_lac_nodes state) yaks in
  (* let load_spawner_fun =
     let spawner_path = "_build/default/src/fos/fos-spawner/spawner.exe" in
     load_spawner spawner_path state
     >>= fun (p,c) ->
     let _ = check_spawner_pid p c state 0 in
     print_spawner_output p
     in
     match (conf.agent.enable_spawner) with
     | true ->
     load_spawner_fun
     | false -> Lwt.return_unit
     >>= fun _ -> *)
  main_loop state prom

(* AGENT CMD  *)

let start verbose_flag daemon_flag debug_flag configuration_path =
  (* ignore verbose_flag; ignore daemon_flag; ignore configuration_path; *)
  (* match daemon_flag with
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
        Lwt_main.run @@ agent verbose_flag debug_flag configuration_path
      end
     else exit 0
     | false -> Lwt_main.run @@ agent verbose_flag debug_flag configuration_path
  *)
  ignore daemon_flag;
  Lwt_main.run @@ agent verbose_flag debug_flag configuration_path

let verbose =
  let doc = "Set verbose output." in
  Cmdliner.Arg.(value & flag & info ["v";"verbose"] ~doc)

let daemon =
  let doc = "Set daemon" in
  Cmdliner.Arg.(value & flag & info ["d";"daemon"] ~doc)

let debug =
  let doc = "Set debug (not load spawner)" in
  Cmdliner.Arg.(value & flag & info ["b";"debug"] ~doc)

let config =
  let doc = "Configuration file path" in
  Cmdliner.Arg.(value & opt string "/etc/fos/agent.json" & info ["c";"conf"] ~doc)


let agent_t = Cmdliner.Term.(const start $ verbose $ daemon $ debug $ config)

let info =
  let doc = "fog05 | The Fog-Computing IaaS" in
  let man = [
    `S Cmdliner.Manpage.s_bugs;
    `P "Email bug reports to fog05-dev at eclipse.org>." ]
  in
  Cmdliner.Term.info "agent" ~version:"%%VERSION%%" ~doc ~exits:Cmdliner.Term.default_exits ~man

let () = Cmdliner.Term.exit @@ Cmdliner.Term.eval (agent_t, info)

