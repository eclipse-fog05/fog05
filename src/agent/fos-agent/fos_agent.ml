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
(* open Fos_errors *)

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


(* UTILS *)

let get_network_plugin self =
  MVar.read self >>= fun self ->
  let%lwt plugins = Yaks_connector.Local.Actual.get_node_plugins (Apero.Option.get self.configuration.agent.uuid) self.yaks in
  let%lwt p = Lwt_list.find_s (fun e ->
      let%lwt pl = Yaks_connector.Local.Actual.get_node_plugin (Apero.Option.get self.configuration.agent.uuid) e self.yaks in
      match String.lowercase_ascii pl.plugin_type with
      | "network" -> Lwt.return_true
      | _ -> Lwt.return_false
    ) plugins
  in
  Lwt.return p


(* MAIN *)

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
  (* Here we should store all information in a persistent YAKS
   * and remove them from the in memory YAKS
  *)
  Yaks_connector.close_connector self.yaks
  >>= fun _ ->
  MVar.return (Lwt_io.printf "Bye!\n") self



let agent verbose_flag debug_flag configuration custom_uuid =
  let level, reporter = (match verbose_flag with
      | true -> Apero.Result.get @@ Logs.level_of_string "debug" ,  (Logs_fmt.reporter ())
      | false -> Apero.Result.get @@ Logs.level_of_string "error",  (Fos_core.get_unix_syslog_reporter ())
    )
  in
  Logs.set_level level;
  Logs.set_reporter reporter;
  let prom,c = Lwt.wait () in
  let _ = register_handlers c () in
  let conf = load_config configuration custom_uuid in
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
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - MGMT Interface: %s" conf.agent.mgmt_interface) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - Plugin Directory: %s" plugin_path) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - AUTOLOAD: %b" conf.plugins.autoload) in
  let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - Plugins:") in
  List.iter (fun p -> ignore @@ Logs_lwt.debug (fun m -> m "[FOS-AGENT] - INIT - %s" p )) (Apero.Option.get_or_default conf.plugins.auto []);
  (* let sys_info = system_info sys_id uuid in *)
  let%lwt yaks = Yaks_connector.get_connector conf in
  (*
   * Here we should check if state is present in local persistent YAKS and
   * recoved from that
   *)
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
    try%lwt
      let%lwt descriptor = Yaks_connector.Global.Actual.get_fdu_info sys_id Yaks_connector.default_tenant_id fdu_uuid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let js = FAgentTypes.json_of_string @@ FDU.string_of_descriptor descriptor in
      let eval_res = FAgentTypes.{result = Some js ; error=None} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_get_image_info self (props:Apero.properties) =
    MVar.read self >>= fun state ->
    let image_uuid = Apero.Option.get @@ Apero.Properties.get "image_uuid" props in
    try%lwt
      let%lwt descriptor = Yaks_connector.Global.Actual.get_image sys_id Yaks_connector.default_tenant_id image_uuid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let js = FAgentTypes.json_of_string @@ FDU.string_of_image descriptor in
      let eval_res = FAgentTypes.{result = Some js ; error=None} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_get_node_fdu_info self (props:Apero.properties) =
    MVar.read self >>= fun state ->
    let fdu_uuid = Apero.Option.get @@ Apero.Properties.get "fdu_uuid" props in
    let node_uuid = Apero.Option.get @@ Apero.Properties.get "node_uuid" props in
    let instanceid = Apero.Option.get @@ Apero.Properties.get "instance_uuid" props in
    try%lwt
      let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - eval_get_node_fdu_info - Search for FDU Info") in
      let%lwt descriptor = Yaks_connector.Global.Actual.get_node_fdu_info sys_id Yaks_connector.default_tenant_id node_uuid fdu_uuid instanceid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let js = FAgentTypes.json_of_string @@ FDU.string_of_record  descriptor in
      let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - eval_get_node_fdu_info - INFO %s" (FAgentTypes.string_of_json js)) in
      let eval_res = FAgentTypes.{result = Some js ; error=None} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_get_network_info self (props:Apero.properties) =
    MVar.read self >>= fun state ->
    let net_uuid = Apero.Option.get @@ Apero.Properties.get "uuid" props in
    try%lwt
      let%lwt descriptor = Yaks_connector.Global.Actual.get_network sys_id Yaks_connector.default_tenant_id net_uuid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let js = FAgentTypes.json_of_string @@ FTypes.string_of_virtual_network descriptor in
      let eval_res = FAgentTypes.{result = Some js ; error=None} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 22} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_get_port_info self (props:Apero.properties) =
    MVar.read self >>= fun state ->
    let cp_uuid = Apero.Option.get @@ Apero.Properties.get "cp_uuid" props in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - eval_get_port_info - Getting info for port %s" cp_uuid ) in
    try%lwt
      let%lwt descriptor = Yaks_connector.Global.Actual.get_port sys_id Yaks_connector.default_tenant_id cp_uuid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let js = FAgentTypes.json_of_string @@ FDU.string_of_connection_point  descriptor in
      let eval_res = FAgentTypes.{result = Some js ; error=None} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ ->
      let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - eval_get_port_info - Search port on FDU") in
      let%lwt fdu_ids = Yaks_connector.Global.Actual.get_all_fdus sys_id Yaks_connector.default_tenant_id state.yaks in
      let%lwt cps = Lwt_list.filter_map_p (fun e ->
          let%lwt fdu =  Yaks_connector.Global.Actual.get_fdu_info sys_id Yaks_connector.default_tenant_id e state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
          let%lwt c = Lwt_list.filter_map_p (fun (cp:FDU.connection_point) ->
              let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - eval_get_port_info - %s == %s ? %d " cp.uuid cp_uuid (String.compare cp.uuid  cp_uuid)) in
              if (String.compare cp.uuid cp_uuid) == 0 then  Lwt.return @@ Some cp
              else Lwt.return None
            ) fdu.connection_points
          in Lwt.return @@ List.nth_opt c 0
        ) fdu_ids
      in
      try%lwt
        let cp = List.hd cps in
        let js = FAgentTypes.json_of_string @@ FDU.string_of_connection_point cp in
        let eval_res = FAgentTypes.{result = Some js ; error=None} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
      with
      | _ ->
        let eval_res = FAgentTypes.{result = None ; error=Some 33} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_get_node_mgmt_address self (props:Apero.properties) =
    MVar.read self >>= fun state ->
    let node_uuid = Apero.Option.get @@ Apero.Properties.get "node_uuid" props in
    try%lwt
      let%lwt nconf = Yaks_connector.Global.Actual.get_node_configuration sys_id Yaks_connector.default_tenant_id node_uuid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let%lwt descriptor = Yaks_connector.Global.Actual.get_node_info sys_id Yaks_connector.default_tenant_id node_uuid state.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
      let nws = descriptor.network in
      let%lwt addr = (Lwt_list.filter_map_p (
          fun (e:FTypes.network_spec_type) ->
            if (String.compare e.intf_name  nconf.agent.mgmt_interface) == 0 then
              Lwt.return @@ Some e.intf_configuration
            else
              Lwt.return None
        ) nws) >>= fun l -> Lwt.return @@ List.hd l
      in
      let js = FAgentTypes.json_of_string @@ FTypes.string_of_intf_conf_type addr in
      let eval_res = FAgentTypes.{result =  Some js; error=None} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  (* NM Evals *)
  let eval_connect_cp_to_network self (props:Apero.properties) =
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-CONNECT-CP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-CONNECT-CP - Properties: %s" (Apero.Properties.to_string props) ) in
    MVar.read self >>= fun state ->
    let%lwt net_p = get_network_plugin self in
    let cp_id = Apero.Option.get @@ Apero.Properties.get "cp_uuid" props in
    let net_id = Apero.Option.get @@ Apero.Properties.get "network_uuid" props in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-CONNECT-CP - # NetManager: %s" net_p) in
    try%lwt
      let parameters = [("cp_id",cp_id);("vnet_id", net_id)] in
      let fname = "connect_cp_to_vnetwork" in
      Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get state.configuration.agent.uuid) net_p fname parameters state.yaks
      >>= fun res ->
      match res with
      | Some r -> Lwt.return @@ FAgentTypes.string_of_eval_result r
      | None -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_remove_cp_from_network self (props:Apero.properties) =
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DISCONNECT-CP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DISCONNECT-CP - Properties: %s" (Apero.Properties.to_string props) ) in
    MVar.read self >>= fun state ->
    let%lwt net_p = get_network_plugin self in
    let cp_id = Apero.Option.get @@ Apero.Properties.get "cp_uuid" props in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DISCONNECT-CP - # NetManager: %s" net_p) in
    try%lwt
      let parameters = [("cp_id",cp_id)] in
      let fname = "disconnect_cp" in
      Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get state.configuration.agent.uuid) net_p fname parameters state.yaks
      >>= fun res ->
      match res with
      | Some r -> Lwt.return @@ FAgentTypes.string_of_eval_result r
      | None -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  (* NM Floating IPs *)
  let eval_create_floating_ip self (props:Apero.properties) =
    ignore props;
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-NEW-FLOATING-IP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-NEW-FLOATING-IP - Properties: %s" (Apero.Properties.to_string props) ) in
    MVar.read self >>= fun state ->
    let%lwt net_p = get_network_plugin self in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-NEW-FLOATING-IP - # NetManager: %s" net_p) in
    try%lwt
      let fname = "create_floating_ip" in
      Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get state.configuration.agent.uuid) net_p fname [] state.yaks
      >>= fun res ->
      match res with
      | Some r ->
        let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-NEW-FLOATING-IP - GOT RESPONSE FROM EVAL %s" (FAgentTypes.string_of_eval_result r)) in
        (* Convertion from record *)
        let floating_r = FTypes.floating_ip_record_of_string @@ JSON.to_string (Apero.Option.get r.result) in
        let floating = FTypes.{uuid = floating_r.uuid; ip_version = floating_r.ip_version; address = floating_r.address} in
        Yaks_connector.Global.Actual.add_node_floating_ip sys_id Yaks_connector.default_tenant_id (Apero.Option.get state.configuration.agent.uuid) floating.uuid floating state.yaks
        >>= fun _ ->
        let eval_res = FAgentTypes.{result = Some (JSON.of_string (FTypes.string_of_floating_ip floating)) ; error=None} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
      |  None -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | _ ->
      let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - EV-NEW-FLOATING-IP - # ERROR WHEN CREATING FLOATING IP") in
      let eval_res = FAgentTypes.{result = None ; error=Some 22} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_delete_floating_ip self (props:Apero.properties) =
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DEL-FLOATING-IP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DEL-FLOATING-IP - Properties: %s" (Apero.Properties.to_string props) ) in
    MVar.read self >>= fun state ->
    let%lwt net_p = get_network_plugin self in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DEL-FLOATING-IP - # NetManager: %s" net_p) in
    try%lwt
      let ip_id = Apero.Option.get @@ Apero.Properties.get "floating_uuid" props in
      let parameters = [("ip_id",ip_id)] in
      let fname = "delete_floating_ip" in
      Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get state.configuration.agent.uuid) net_p fname parameters state.yaks
      >>= fun res ->
      match res with
      | Some r ->
        let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-DEL-FLOATING-IP - GOT RESPONSE FROM EVAL %s" (FAgentTypes.string_of_eval_result r)) in
        (* Convertion from record *)
        let floating_r = FTypes.floating_ip_record_of_string @@ JSON.to_string (Apero.Option.get r.result) in
        let floating = FTypes.{uuid = floating_r.uuid; ip_version = floating_r.ip_version; address = floating_r.address} in
        Yaks_connector.Global.Actual.add_node_floating_ip sys_id Yaks_connector.default_tenant_id (Apero.Option.get state.configuration.agent.uuid) floating.uuid floating state.yaks
        >>= fun _ ->
        let eval_res = FAgentTypes.{result = Some (JSON.of_string (FTypes.string_of_floating_ip floating)) ; error=None} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
      |  None -> let eval_res = FAgentTypes.{result = None ; error=Some 11} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | e ->
      let msg = Printexc.to_string e
      and stack = Printexc.get_backtrace () in
      Printf.eprintf "there was an error: %s%s\n" msg stack;
      let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - EV-NEW-FLOATING-IP - # ERROR WHEN DELETING FLOATING IP") in
      let eval_res = FAgentTypes.{result = None ; error=Some 22} in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_assign_floating_ip self (props:Apero.properties) =
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-ASSOC-FLOATING-IP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-ASSOC-FLOATING-IP - Properties: %s" (Apero.Properties.to_string props) ) in
    MVar.read self >>= fun state ->
    let%lwt net_p = get_network_plugin self in
    try%lwt
      let ip_id = Apero.Option.get @@ Apero.Properties.get "floating_uuid" props in
      let cp_id = Apero.Option.get @@ Apero.Properties.get "cp_uuid" props in
      let parameters = [("ip_id",ip_id);("cp_id",cp_id)] in
      let fname = "assign_floating_ip" in
      Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get state.configuration.agent.uuid) net_p fname parameters state.yaks
      >>= fun res ->
      match res with
      | Some r ->
        (* Convertion from record *)
        let floating_r = FTypes.floating_ip_record_of_string @@ JSON.to_string (Apero.Option.get r.result) in
        let floating = FTypes.{uuid = floating_r.uuid; ip_version = floating_r.ip_version; address = floating_r.address} in
        Yaks_connector.Global.Actual.add_node_floating_ip sys_id Yaks_connector.default_tenant_id (Apero.Option.get state.configuration.agent.uuid) floating.uuid floating state.yaks
        >>= fun _ ->
        let eval_res = FAgentTypes.{result = Some (JSON.of_string (FTypes.string_of_floating_ip floating)) ; error=None} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
      |  None -> let eval_res = FAgentTypes.{result = None ; error=Some 33} in
        let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - EV-ASSOC-FLOATING-IP - EVAL RETURNED NONE") in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | exn -> let eval_res = FAgentTypes.{result = None ; error=Some 22} in
      let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - EV-ASSOC-FLOATING-IP - EXCEPTION: %s" (Printexc.to_string exn)) in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  let eval_remove_floating_ip self (props:Apero.properties) =
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-REMOVE-FLOATING-IP - ##############") in
    let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - EV-REMOVE-FLOATING-IP - Properties: %s" (Apero.Properties.to_string props) ) in
    MVar.read self >>= fun state ->
    let%lwt net_p = get_network_plugin self in
    try%lwt
      let ip_id = Apero.Option.get @@ Apero.Properties.get "floating_uuid" props in
      let cp_id = Apero.Option.get @@ Apero.Properties.get "cp_uuid" props in
      let parameters = [("ip_id",ip_id);("cp_id",cp_id)] in
      let fname = "remove_floating_ip" in
      Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get state.configuration.agent.uuid) net_p fname parameters state.yaks
      >>= fun res ->
      match res with
      | Some r ->
        (* Convertion from record *)
        let floating_r = FTypes.floating_ip_record_of_string @@ JSON.to_string (Apero.Option.get r.result) in
        let floating = FTypes.{uuid = floating_r.uuid; ip_version = floating_r.ip_version; address = floating_r.address} in
        Yaks_connector.Global.Actual.add_node_floating_ip sys_id Yaks_connector.default_tenant_id (Apero.Option.get state.configuration.agent.uuid) floating.uuid floating state.yaks
        >>= fun _ ->
        let eval_res = FAgentTypes.{result = Some (JSON.of_string (FTypes.string_of_floating_ip floating)) ; error=None} in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
      |  None -> let eval_res = FAgentTypes.{result = None ; error=Some 33} in
        let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - EV-REMOVE-FLOATING-IP - EVAL RETURNED NONE") in
        Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
    with
    | exn -> let eval_res = FAgentTypes.{result = None ; error=Some 22} in
      let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - EV-REMOVE-FLOATING-IP - EXCEPTION: %s" (Printexc.to_string exn)) in
      Lwt.return @@ FAgentTypes.string_of_eval_result eval_res
  in
  (* Listeners *)
  (* Global Desired *)
  let cb_gd_plugin self (pl:FTypes.plugin option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match pl with
       | Some pl ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN - Received plugin") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN - Name: %s" pl.name) in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-PLUGIN -  Calling the spawner by writing this on local desired") in
         Yaks_connector.Local.Desired.add_node_plugin (Apero.Option.get self.configuration.agent.uuid) pl self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some plid ->
         MVar.read self >>= fun self ->
         Yaks_connector.Local.Desired.remove_node_plugin (Apero.Option.get self.configuration.agent.uuid) plid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_gd_fdu self (fdu:FDU.descriptor option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match fdu with
       | Some fdu -> MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - FDU Updated! Advertising on GA") in
         Yaks_connector.Global.Actual.add_fdu_info sys_id Yaks_connector.default_tenant_id (Apero.Option.get fdu.uuid) fdu self.yaks >>= Lwt.return
       | None -> Lwt.return_unit
      )
    | true ->
      (match uuid with
       | Some fduid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_fdu_info sys_id Yaks_connector.default_tenant_id fduid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_gd_image self (img:FDU.image option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match img with
       | Some img ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-IMAGE - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-IMAGE - Image Updated! Advertising on GA") in
         (match img.uuid with
          | Some id -> Yaks_connector.Global.Actual.add_image sys_id Yaks_connector.default_tenant_id id img self.yaks >>= Lwt.return
          | None -> Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-IMAGE - Ignoring Image as UUID is missing!!") >>= Lwt.return)
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some nodeid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_image sys_id Yaks_connector.default_tenant_id nodeid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_gd_flavor self (flv:FDU.computational_requirements option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match flv with
       | Some flv ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FLAVOR - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FLAVOR - Flavor Updated! Advertising on GA") in
         (match flv.uuid with
          | Some id -> Yaks_connector.Global.Actual.add_flavor sys_id Yaks_connector.default_tenant_id id flv self.yaks >>= Lwt.return
          | None -> Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FLAVOR - Ignoring Flavor as UUID is missing!!") >>= Lwt.return)
       | None -> Lwt.return_unit
      )
    | true ->
      (match uuid with
       | Some flvid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_flavor sys_id Yaks_connector.default_tenant_id flvid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_gd_node_fdu self (fdu:FDU.record option) (is_remove:bool) (fduid:string option) (instanceid:string option) =
    match is_remove with
    | false ->
      (match fdu with
       | Some fdu ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NODE-FDU - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NODE-FDU - FDU Updated! Agent will call the right plugin!") in
         let%lwt fdu_d = Yaks_connector.Global.Actual.get_fdu_info sys_id Yaks_connector.default_tenant_id fdu.fdu_uuid self.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
         let fdu_type = Fos_im.string_of_hv_type fdu_d.hypervisor in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - FDU Type %s" fdu_type) in
         let%lwt plugins = Yaks_connector.Local.Actual.get_node_plugins (Apero.Option.get self.configuration.agent.uuid) self.yaks in
         let%lwt matching_plugins = Lwt_list.filter_map_p (fun e ->
             let%lwt pl = Yaks_connector.Local.Actual.get_node_plugin (Apero.Option.get self.configuration.agent.uuid) e self.yaks in
             if String.uppercase_ascii (pl.name) = String.uppercase_ascii (fdu_type) then
               Lwt.return @@ Some pl
             else
               Lwt.return None
           ) plugins
         in
         (match matching_plugins with
          | [] ->
            let%lwt _ = Logs_lwt.err (fun m -> m "[FOS-AGENT] - CB-GD-FDU - No plugin found for this FDU") in
            let r = { fdu with status = `ERROR} in
            Yaks_connector.Global.Actual.add_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) r.fdu_uuid (Apero.Option.get r.uuid) r self.yaks >>= Lwt.return
          | _ ->
            let pl = List.hd matching_plugins in
            let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - Calling %s plugin" pl.name) in
            (* Here we should at least update the record interfaces and connection points *)
            let%lwt ncpids = Lwt_list.map_p (fun (e:FDU.connection_point) -> Lwt.return (e.uuid, Apero.Uuid.to_string @@ Apero.Uuid.make ())) fdu_d.connection_points in
            let%lwt rcps = Lwt_list.map_p (fun (e:FDU.connection_point) ->
                let rcpid = List.assoc e.uuid ncpids in
                let cpr = FDU.{uuid =  rcpid; status = `CREATE; cp_uuid = e.uuid; veth_face_name = None; br_name = None; properties = None } in
                Lwt.return cpr
              ) fdu_d.connection_points
            in
            let%lwt rfaces = Lwt_list.map_p (fun (e:FDU.interface) ->
                let facer = FDU.{vintf_name = e.name; status = `CREATE; if_type = e.virtual_interface.intf_type; phy_face = None; cp_id = None; veth_face_name=None; properties=None; mac_address = e.mac_address} in
                let facer =
                  match e.if_type with
                  | `INTERNAL -> (match e.cp_id with
                      | Some cpid ->
                        let ncpid = List.assoc cpid ncpids in
                        {facer with cp_id = Some ncpid}
                      | None -> facer)
                  | _ ->
                    {facer with phy_face = Some e.virtual_interface.vpci}
                in
                Lwt.return facer
              ) fdu_d.interfaces
            in
            let fdu = {fdu with interfaces = rfaces; connection_points = rcps} in
            Yaks_connector.Local.Desired.add_node_fdu (Apero.Option.get self.configuration.agent.uuid) pl.uuid fdu.fdu_uuid (Apero.Option.get fdu.uuid) fdu self.yaks >>= Lwt.return
         )

       | None -> Lwt.return_unit)
    | true ->
      (match( fduid,instanceid)  with
       | Some fduid , Some instanceid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) fduid instanceid self.yaks >>= Lwt.return
       | (_,_) -> Lwt.return_unit)

  in
  (*  *)
  let cb_gd_net_all self (net:FTypes.virtual_network option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      (match net with
       | Some net ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET Updated! Agent will update actual store and call the right plugin!") in
         let%lwt _ = Yaks_connector.Global.Actual.add_network sys_id Yaks_connector.default_tenant_id net.uuid net self.yaks in
         let record = FTypesRecord.{uuid = net.uuid; status = `CREATE; properties = None; ip_configuration = net.ip_configuration; overlay = None; vni = None; mcast_addr = None; vlan_id = None; face = None} in
         Yaks_connector.Local.Desired.add_node_network (Apero.Option.get self.configuration.agent.uuid) net_p net.uuid record self.yaks
         >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some netid -> MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET Removed!") in
         let%lwt net_info = Yaks_connector.Local.Actual.get_node_network (Apero.Option.get self.configuration.agent.uuid) net_p netid self.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
         let net_info = {net_info with status = `DESTROY} in
         let%lwt _ = Yaks_connector.Local.Desired.add_node_network (Apero.Option.get self.configuration.agent.uuid) net_p netid net_info self.yaks in
         Yaks_connector.Global.Actual.remove_network sys_id Yaks_connector.default_tenant_id netid self.yaks >>= Lwt.return
       | None ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET NO UUID!!!!") in
         Lwt.return_unit)

  in
  (*  *)
  let cb_gd_net self (net:FTypesRecord.virtual_network option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      (match net with
       | Some net ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET Updated! Agent will update actual store and call the right plugin!") in
         (* let%lwt _ = Yaks_connector.Global.Actual.add_network sys_id Yaks_connector.default_tenant_id net.uuid net self.yaks in *)
         (* let record = FTypesRecord.{uuid = net.uuid; status = `CREATE; properties = None; ip_configuration = net.ip_configuration} in *)
         Yaks_connector.Local.Desired.add_node_network (Apero.Option.get self.configuration.agent.uuid) net_p net.uuid net self.yaks
         >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some netid -> MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET Removed!") in
         let%lwt net_info = Yaks_connector.Local.Actual.get_node_network (Apero.Option.get self.configuration.agent.uuid) net_p netid self.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
         let net_info = {net_info with status = `DESTROY} in
         let%lwt _ = Yaks_connector.Local.Desired.add_node_network (Apero.Option.get self.configuration.agent.uuid) net_p netid net_info self.yaks in
         Yaks_connector.Global.Actual.remove_network sys_id Yaks_connector.default_tenant_id netid self.yaks >>= Lwt.return
       | None ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-NET - vNET NO UUID!!!!") in
         Lwt.return_unit)

  in
  let cb_gd_cp self (cp:FDU.connection_point option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      ( match cp with
        | Some cp ->
          MVar.read self >>= fun self ->
          let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CP - ##############") in
          let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CP - CP Updated! Agent will update actual store and call the right plugin!") in
          let%lwt _ = Yaks_connector.Global.Actual.add_port sys_id Yaks_connector.default_tenant_id cp.uuid cp self.yaks in
          let record = FDU.{cp_uuid = cp.uuid; uuid = cp.uuid; status = `CREATE; properties = None; veth_face_name = None; br_name = None} in
          Yaks_connector.Local.Desired.add_node_port (Apero.Option.get self.configuration.agent.uuid) net_p record.cp_uuid record self.yaks
          >>= Lwt.return
        | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some cpid -> MVar.read self >>= fun self ->
         let%lwt _ = Yaks_connector.Global.Actual.remove_node_port sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) cpid self.yaks in
         Yaks_connector.Global.Actual.remove_port sys_id Yaks_connector.default_system_id cpid self.yaks  >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_gd_router self (router:Router.descriptor option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      (match router with
       | Some router ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-ROUTER - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-ROUTER - vRouter Updated! Agent will update actual store and call the right plugin!") in
         (* Converting to record *)
         let rid = (Apero.Option.get_or_default router.uuid (Apero.Uuid.to_string (Apero.Uuid.make ()))) in
         let%lwt port_records = Lwt_list.mapi_p (fun i (e:Router.router_port) ->
             match e.port_type with
             | `EXTERNAL ->
               let%lwt res = Yaks_connector.Local.Actual.exec_nm_eval (Apero.Option.get self.configuration.agent.uuid) net_p "get_overlay_interface" [] self.yaks  in
               let face =(JSON.to_string (Apero.Option.get (Apero.Option.get res).result)) in
               let wan_face = Printf.sprintf "r-%s-e%d" (List.hd (String.split_on_char '-' rid)) i in
               Lwt.return Router.{port_type = `EXTERNAL; faces = [wan_face]; ext_face = Some face; ip_address = ""; pair_id = None}
             | `INTERNAL ->
               let face_i = Printf.sprintf "r-%s-e%d-i" (List.hd (String.split_on_char '-' rid)) i in
               let face_e = Printf.sprintf "r-%s-e%d-e" (List.hd (String.split_on_char '-' rid)) i in
               Lwt.return Router.{port_type = `INTERNAL; faces = [face_i; face_e]; ip_address = ""; ext_face = None; pair_id = e.vnet_id}
           ) router.ports
         in
         let vrouter_ns =  Printf.sprintf "r-%s-ns" (List.hd (String.split_on_char '-' rid))  in
         let router_record = Router.{uuid = rid; state = `CREATE; ports = port_records; router_ns = vrouter_ns; nodeid = (Apero.Option.get self.configuration.agent.uuid)} in
         Yaks_connector.Local.Desired.add_node_router (Apero.Option.get self.configuration.agent.uuid) net_p  router_record.uuid router_record self.yaks
         >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some routerid -> MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-ROUTER - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-ROUTER - vRouter Removed!") in
         let%lwt router_info = Yaks_connector.Local.Actual.get_node_router (Apero.Option.get self.configuration.agent.uuid) net_p routerid self.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
         let router_info = {router_info with state = `DESTROY} in
         Yaks_connector.Local.Desired.add_node_router (Apero.Option.get self.configuration.agent.uuid) net_p routerid router_info self.yaks
       (* Yaks_connector.Global.Actual.reove_ sys_id Yaks_connector.default_tenant_id routerid self.yaks >>= Lwt.return *)
       | None ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-ROUTER - vRouter NO UUID!!!!") in
         Lwt.return_unit)

  in
  (* Local Actual *)
  let cb_la_net self (net:FTypesRecord.virtual_network option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      (match net with
       | Some net ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NET - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NET - vNET Updated! Advertising on GA") in
         let nid = (Apero.Option.get self.configuration.agent.uuid) in
         (match net.status with
          | `DESTROY -> Yaks_connector.Global.Actual.remove_node_network sys_id Yaks_connector.default_tenant_id nid net.uuid self.yaks
          | _ ->
            Yaks_connector.Global.Actual.add_node_network sys_id Yaks_connector.default_tenant_id nid net.uuid net self.yaks >>= Lwt.return)
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some netid ->
         MVar.read self >>= fun self ->
         Yaks_connector.Local.Desired.remove_node_network (Apero.Option.get self.configuration.agent.uuid) net_p netid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_la_cp self (cp:FDU.connection_point_record option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      (match cp with
       | Some cp ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-CP - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-CP - CP Updated! Advertising on GA") in
         let nid = (Apero.Option.get self.configuration.agent.uuid) in
         ( match cp.status with
           | `DESTROY -> Yaks_connector.Global.Actual.remove_node_port sys_id Yaks_connector.default_tenant_id nid cp.cp_uuid self.yaks
           | _ ->
             Yaks_connector.Global.Actual.add_node_port sys_id Yaks_connector.default_tenant_id nid cp.cp_uuid cp self.yaks >>= Lwt.return)
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some cpid ->
         MVar.read self >>= fun self ->
         Yaks_connector.Local.Desired.remove_node_port (Apero.Option.get self.configuration.agent.uuid) net_p cpid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)

  in
  let cb_la_router self (router:Router.record option) (is_remove:bool) (uuid:string option) =
    let%lwt net_p = get_network_plugin self in
    match is_remove with
    | false ->
      (match router with
       | Some router ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-ROUTER - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-ROUTER - vRouter Updated! Advertising on GA") in
         let nid = (Apero.Option.get self.configuration.agent.uuid) in
         (match router.state with
          | `DESTROY -> Yaks_connector.Global.Actual.remove_node_router sys_id Yaks_connector.default_tenant_id nid router.uuid self.yaks
          | _ ->
            (* Convert to back to descriptor *)
            let%lwt ports = Lwt_list.map_p (fun (e:Router.router_port_record) ->
                Lwt.return Router.{port_type = e.port_type; vnet_id = e.pair_id; ip_address = Some e.ip_address}
              ) router.ports
            in
            let router_desc = Router.{uuid = Some router.uuid; ports = ports; } in
            Yaks_connector.Global.Actual.add_node_router sys_id Yaks_connector.default_tenant_id nid router.uuid router_desc self.yaks >>= Lwt.return)
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some routerid ->
         MVar.read self >>= fun self ->
         Yaks_connector.Local.Desired.remove_node_router (Apero.Option.get self.configuration.agent.uuid) net_p routerid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_la_plugin self (pl:FTypes.plugin option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match pl with
       | Some pl ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN - Received plugin") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN - Name: %s" pl.name) in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-PLUGIN -  Plugin loaded advertising on GA") in
         Yaks_connector.Global.Actual.add_node_plugin sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) pl self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some plid -> MVar.read self >>= fun self ->
         Yaks_connector.Local.Actual.remove_node_plugin (Apero.Option.get self.configuration.agent.uuid) plid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)

  in
  let cb_la_ni self (ni:FTypes.node_info option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match ni with
       | Some ni ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NI - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NI - Updated node info advertising of GA") in
         Yaks_connector.Global.Actual.add_node_info sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) ni self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some nid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_node_info sys_id Yaks_connector.default_tenant_id nid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)

  in
  let cb_la_ns self (ns:FTypes.node_status option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match ns with
       | Some ns ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NI - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NI - Updated node info advertising of GA") in
         Yaks_connector.Global.Actual.add_node_status sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) ns self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some nid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_node_status sys_id Yaks_connector.default_tenant_id nid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  let cb_la_node_fdu self (fdu:FDU.record option) (is_remove:bool) (fduid:string option) (instanceid:string option) =
    match is_remove with
    | false ->
      (match fdu with
       | Some fdu ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NODE-FDU - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LA-NODE-FDU - FDU Updated! Advertising on GA") in
         ( match fdu.status with
           | `UNDEFINE -> Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) fdu.fdu_uuid (Apero.Option.get fdu.uuid) self.yaks
           | _ ->
             Yaks_connector.Global.Actual.add_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) fdu.fdu_uuid (Apero.Option.get fdu.uuid) fdu self.yaks >>= Lwt.return)
       | None -> Lwt.return_unit)
    | true ->
      (match( fduid,instanceid)  with
       | Some fduid , Some instanceid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id (Apero.Option.get self.configuration.agent.uuid) fduid instanceid self.yaks >>= Lwt.return
       | (_,_) -> Lwt.return_unit)


  in
  (* Constrained Nodes Global *)
  (* let cb_gd_cnode_fdu self nodeid (fdu:FDU.record option) (is_remove:bool) (uuid:string option) =
     match is_remove with
     | false ->
      (match fdu with
       | Some fdu ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CNODE-FDU - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CNODE-FDU - FDU Updated! Agent will call the right plugin!") in
         let%lwt fdu_d = Yaks_connector.Global.Actual.get_fdu_info sys_id Yaks_connector.default_tenant_id fdu.fdu_uuid self.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
         let fdu_type = Fos_im.string_of_hv_type fdu_d.hypervisor in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-CNODE-FDU - FDU Type %s" fdu_type) in
         let%lwt plugins = Yaks_connector.LocalConstraint.Actual.get_node_plugins nodeid self.yaks in
         Lwt_list.iter_p (fun e ->
             let%lwt pl = Yaks_connector.LocalConstraint.Actual.get_node_plugin nodeid e self.yaks >>= fun x -> Lwt.return @@ Apero.Option.get x in
             if String.uppercase_ascii (pl.name) = String.uppercase_ascii (fdu_type) then
               let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-GD-FDU - Calling %s plugin" pl.name) in
               Yaks_connector.LocalConstraint.Desired.add_node_fdu nodeid pl.uuid fdu.fdu_uuid fdu self.yaks >>= Lwt.return
             else
               Lwt.return_unit
           ) plugins >>= Lwt.return
       | None -> Lwt.return_unit)
     | true ->
      (match uuid with
       | Some fduid -> MVar.read self >>= fun self ->
         Lwt.return_unit
       (* Yaks_connector.Global.Desired.remove_node_fdu sys_id Yaks_connector.default_tenant_id nodeid fduid self.yaks >>= Lwt.return *)
       | None -> Lwt.return_unit)
     in *)
  (* Constrained Nodes Local *)
  let cb_lac_node_fdu self _ (fdu:FDU.record option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match fdu with
       | Some fdu ->
         MVar.read self >>= fun _ ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-FDU - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-FDU - FDU Updated! Advertising on GA") in
         ( match fdu.status with
           | `UNDEFINE -> Lwt.return_unit
           (* Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id nodeid fdu.fdu_uuid self.yaks *)
           | _ ->Lwt.return_unit)
       (* Yaks_connector.Global.Actual.add_node_fdu sys_id Yaks_connector.default_tenant_id nodeid fdu.fdu_uuid fdu self.yaks >>= Lwt.return) *)
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some _ -> MVar.read self >>= fun _ -> Lwt.return_unit
       (* Yaks_connector.Global.Actual.remove_node_fdu sys_id Yaks_connector.default_tenant_id nodeid fduid self.yaks >>= Lwt.return *)
       | None -> Lwt.return_unit)
  in
  let cb_lac_plugin self nodeid (pl:FTypes.plugin option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match pl with
       | Some pl ->
         MVar.read self >>= fun self ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN - Received plugin") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN - Name: %s" pl.name) in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-PLUGIN -  Plugin loaded advertising on GA") in
         Yaks_connector.Global.Actual.add_node_plugin sys_id Yaks_connector.default_tenant_id nodeid pl self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some plid -> MVar.read self >>= fun self ->
         Yaks_connector.Global.Actual.remove_node_plugin sys_id Yaks_connector.default_tenant_id nodeid plid self.yaks >>= Lwt.return
       | None -> Lwt.return_unit)
  in
  (* let cb_lac_node_configuration self nodeid (pl:FTypes.node_info) =
     MVar.read self >>= fun self ->
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF - ##############") in
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF - Received plugin") in
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF - Name: %s" pl.name) in
     let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NODE-CONF -  Plugin loaded advertising on GA") in
     Yaks_connector.Global.Actual.add_node_configuration sys_id Yaks_connector.default_tenant_id nodeid pl self.yaks >>= Lwt.return
     in *)
  let cb_lac_nodes self (ni:FTypes.node_info option) (is_remove:bool) (uuid:string option) =
    match is_remove with
    | false ->
      (match ni with
       | Some ni ->
         MVar.guarded self @@ fun state ->
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NI - ##############") in
         let%lwt _ = Logs_lwt.debug (fun m -> m "[FOS-AGENT] - CB-LAC-NI - Updated node info advertising of GA") in
         let intid = ni.uuid in
         let extid = Apero.Uuid.to_string @@ Apero.Uuid.make () in
         let ext_ni = {ni with uuid = extid } in
         let%lwt _ = Yaks_connector.Global.Actual.add_node_info sys_id Yaks_connector.default_tenant_id extid ext_ni state.yaks in
         let%lwt _ = Yaks_connector.LocalConstraint.Actual.observe_node_plugins intid (cb_lac_plugin self  extid) state.yaks in
         let%lwt _ =  Yaks_connector.LocalConstraint.Actual.observe_node_fdu intid (cb_lac_node_fdu self extid) state.yaks in
         (* let%lwt _ = Yaks_connector.Global.Desired.observe_node_fdu sys_id Yaks_connector.default_tenant_id extid (cb_gd_cnode_fdu self intid) state.yaks in *)
         MVar.return () {state with constrained_nodes = ConstraintMap.add extid intid state.constrained_nodes}
       | None -> Lwt.return_unit)
    | true ->
      (match uuid with
       | Some nid -> MVar.guarded self @@ fun state ->
         let%lwt _ = Yaks_connector.Global.Actual.remove_node_info sys_id Yaks_connector.default_tenant_id nid state.yaks in
         MVar.return () {state with constrained_nodes =  ConstraintMap.remove nid state.constrained_nodes}
       | None -> Lwt.return_unit)
  in
  (* Registering Evals *)
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_fdu_info" (eval_get_fdu_info state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_node_fdu_info" (eval_get_node_fdu_info state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_node_mgmt_address" (eval_get_node_mgmt_address state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_network_info" (eval_get_network_info state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_port_info" (eval_get_port_info state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.add_agent_eval uuid "get_image_info" (eval_get_image_info state) yaks in
  (* Network Mgmt Evals *)
  let%lwt _ = Yaks_connector.Global.Actual.add_agent_eval sys_id Yaks_connector.default_tenant_id uuid "add_port_to_network" (eval_connect_cp_to_network state) yaks in
  let%lwt _ = Yaks_connector.Global.Actual.add_agent_eval sys_id Yaks_connector.default_tenant_id uuid "remove_port_from_network" (eval_remove_cp_from_network state) yaks in
  let%lwt _ = Yaks_connector.Global.Actual.add_agent_eval sys_id Yaks_connector.default_tenant_id uuid "create_floating_ip" (eval_create_floating_ip state) yaks in
  let%lwt _ = Yaks_connector.Global.Actual.add_agent_eval sys_id Yaks_connector.default_tenant_id uuid "delete_floating_ip" (eval_delete_floating_ip state) yaks in
  let%lwt _ = Yaks_connector.Global.Actual.add_agent_eval sys_id Yaks_connector.default_tenant_id uuid "assign_floating_ip" (eval_assign_floating_ip state) yaks in
  let%lwt _ = Yaks_connector.Global.Actual.add_agent_eval sys_id Yaks_connector.default_tenant_id uuid "remove_floating_ip" (eval_remove_floating_ip state) yaks in
  (* Constraint Eval  *)
  let%lwt _ = Yaks_connector.LocalConstraint.Actual.add_agent_eval uuid "get_fdu_info" (eval_get_fdu_info state) yaks in
  (* Registering listeners *)
  (* Global Desired Listeners *)
  let%lwt _ = Yaks_connector.Global.Desired.observe_node_plugins sys_id Yaks_connector.default_tenant_id uuid (cb_gd_plugin state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_fdu sys_id Yaks_connector.default_tenant_id (cb_gd_fdu state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_node_fdu sys_id Yaks_connector.default_tenant_id uuid (cb_gd_node_fdu state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_network sys_id Yaks_connector.default_tenant_id (cb_gd_net_all state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_node_network sys_id Yaks_connector.default_tenant_id uuid (cb_gd_net state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_ports sys_id Yaks_connector.default_tenant_id (cb_gd_cp state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_images sys_id Yaks_connector.default_tenant_id (cb_gd_image state) yaks in
  let%lwt _ = Yaks_connector.Global.Desired.observe_flavors sys_id Yaks_connector.default_tenant_id (cb_gd_flavor state) yaks in
  (* Global Actual with NodeID *)
  let%lwt _ = Yaks_connector.Global.Desired.observe_node_routers sys_id Yaks_connector.default_tenant_id uuid (cb_gd_router state) yaks in
  (* Local Actual Listeners *)
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_plugins uuid (cb_la_plugin state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_info uuid (cb_la_ni state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_status uuid (cb_la_ns state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_fdu uuid (cb_la_node_fdu state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_network uuid (cb_la_net state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_port uuid (cb_la_cp state) yaks in
  let%lwt _ = Yaks_connector.Local.Actual.observe_node_router uuid (cb_la_router state) yaks in
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

let start verbose_flag daemon_flag debug_flag configuration_path custom_uuid =
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
  Lwt_main.run @@ agent verbose_flag debug_flag configuration_path custom_uuid

let verbose =
  let doc = "Set verbose output." in
  Cmdliner.Arg.(value & flag & info ["v";"verbose"] ~doc)

let daemon =
  let doc = "Set daemon" in
  Cmdliner.Arg.(value & flag & info ["d";"daemon"] ~doc)

let id =
  let doc = "Set custom node ID" in
  Cmdliner.Arg.(value & opt (some string) None & info ["i";"id"] ~doc)

let debug =
  let doc = "Set debug (not load spawner)" in
  Cmdliner.Arg.(value & flag & info ["b";"debug"] ~doc)

let config =
  let doc = "Configuration file path" in
  Cmdliner.Arg.(value & opt string "/etc/fos/agent.json" & info ["c";"conf"] ~doc)


let agent_t = Cmdliner.Term.(const start $ verbose $ daemon $ debug $ config $ id)

let info =
  let doc = "fog05 | The Fog-Computing IaaS" in
  let man = [
    `S Cmdliner.Manpage.s_bugs;
    `P "Email bug reports to fog05-dev at eclipse.org>." ]
  in
  Cmdliner.Term.info "agent" ~version:"%%VERSION%%" ~doc ~exits:Cmdliner.Term.default_exits ~man

let () = Cmdliner.Term.exit @@ Cmdliner.Term.eval (agent_t, info)
let () = Cmdliner.Term.exit @@ Cmdliner.Term.eval (agent_t, info)