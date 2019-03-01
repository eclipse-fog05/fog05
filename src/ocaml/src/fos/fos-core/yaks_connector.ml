open Yaks_ocaml
open Lwt.Infix
open Fos_errors
open Fos_core
open Fos_im




let global_actual_prefix = "/agfos"
let global_desired_prefix = "/dgfos"
let local_actual_prefix = "/alfos"
let local_desired_prefix = "/dlfos"
let local_constraint_actual_prefix = "/aclfos"
let local_constaint_desired_prefix = "/dclfos"


let default_system_id = "0"
let default_tenant_id = "0"

let create_path tokens =
  Yaks_types.Path.of_string @@ String.concat "/" tokens

let create_selector tokens =
  Yaks_types.Selector.of_string @@ String.concat "/" tokens


type state = {
  yaks_client : Yaks_api.t
; yaks_admin : Yaks.Admin.t
; ws : Yaks.Workspace.t
; listeners : string list
; evals : Yaks.Path.t list;
}

type connector = state MVar.t

let get_connector (config:configuration)=
  let loc = Apero.Option.get @@ Apero_net.Locator.of_string config.agent.yaks in
  let%lwt yclient = Yaks.login loc Apero.Properties.empty in
  let%lwt admin = Yaks.admin yclient in
  let%lwt ws = Yaks.workspace (create_path [global_actual_prefix; ""]) yclient in
  Lwt.return @@ MVar.create {  ws = ws
                            ; yaks_client = yclient
                            ; yaks_admin = admin
                            ; listeners = []
                            ; evals = []
                            }
let get_connector_of_locator loc =
  let%lwt yclient = Yaks.login loc Apero.Properties.empty in
  let%lwt admin = Yaks.admin yclient in
  let%lwt ws = Yaks.workspace (create_path [global_actual_prefix; ""]) yclient in
  Lwt.return @@ MVar.create {  ws = ws
                            ; yaks_client = yclient
                            ; yaks_admin = admin
                            ; listeners = []
                            ; evals = []
                            }

let close_connector y =
  MVar.guarded y @@ fun state ->
  Lwt_list.iter_p (fun e -> Yaks.Workspace.unsubscribe e state.ws) state.listeners
  >>= fun _ ->
  Lwt_list.iter_p (fun e -> Yaks.Workspace.unregister_eval e state.ws) state.evals
  >>= fun _ ->
  Yaks.logout state.yaks_client
  >>=  fun _ ->
  MVar.return () state


module MakeGAD(P: sig val prefix: string end) = struct

  let get_sys_info_path sysid =
    create_path [P.prefix; sysid; "info"]

  let get_sys_configuration_path sysid =
    create_path [P.prefix; sysid; "configuration"]

  let get_all_users_selector sysid =
    create_selector [P.prefix; sysid; "users"; "*"]

  let get_user_info_path sysid userid =
    create_path [P.prefix; sysid; "users"; userid; "info"]

  let get_all_tenants_selector sysid =
    create_selector [P.prefix; sysid; "tenants"; "*"]

  let get_tenant_info_path sysid tenantid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "info"]

  let get_tenant_configuration_path sysid tenantid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "configuration"]

  let get_fdu_info_path sysid tenantid fduid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "fdu"; fduid; "info"]

  let get_all_fdu_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "fdu"; "*"; "info"]

  let get_all_nodes_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; "*"; "info"]

  let get_node_info_path sysid tenantid nodeid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "info"]

  let get_node_configuration_path sysid tenantid nodeid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "configuration"]

  let get_node_plugins_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; "*"; "info"]

  let get_node_plugins_subscriber_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; "*"; "info"]

  let get_node_plugin_info_path sysid tenantid nodeid pluginid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; pluginid; "info"]

  let get_node_plugin_eval_path sysid tenantid nodeid pluginid func_name =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; pluginid; "exec"; func_name]

  let get_node_fdu_info_path sysid tenantid nodeid fduid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "fdu"; fduid; "info"]

  let get_node_fdu_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "fdu"; "*"; "info"]

  let get_node_network_port_info_path sysid tenantid nodeid portid =
    create_path [P.prefix; sysid; "tenants"; tenantid;"nodes"; nodeid; "networks"; "ports"; portid; "info"]

  let get_node_network_ports_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid;"networks"; "ports"; "*"; "info"]

  let get_all_node_networks_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; "*"; "info"]

  let get_node_network_info_path sysid tenantid nodeid networkid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; networkid; "info"]

  let get_all_entities_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "entities"; "*"; "info"]

  let get_all_networks_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "networks"; "*"; "info"]

  let get_entity_info_path sysid tenantid entityid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "entities"; entityid; "info"]

  let get_network_info_path sysid tenantid networkid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "networks"; networkid; "info"]

  let get_entity_all_instances_selector sysid tenantid entityid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "entities"; entityid; "instances"; "*"]

  let get_entity_instance_info_path sysid tenantid entityid instanceid=
    create_path [P.prefix; sysid; "tenants"; tenantid; "entities"; entityid; "instances"; instanceid; "info"]

  let get_network_port_info_path sysid tenantid portid=
    create_path [P.prefix; sysid; "tenants"; tenantid; "networks"; "ports"; portid; "info"]

  let get_network_ports_selector sysid tenantid  =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "networks"; "ports"; "*"; "info"]

  let extract_userid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_tenantid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_fduid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_nodeid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_pluginid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let extract_node_fduid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let get_sys_info sysid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_sys_info_path sysid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_sys_info") ))
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ FAgentTypes.system_info_of_string (Yaks.Value.to_string v)
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_sys_info") ))
      | exn -> Lwt.fail exn

  let get_sys_config sysid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_sys_configuration_path sysid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_sys_config") ))
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ FAgentTypes.system_config_of_string (Yaks.Value.to_string v)
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_sys_config") ))
      | exn -> Lwt.fail exn

  let get_all_users_ids sysid connector =
    MVar.read connector >>= fun connector ->
    let s = get_all_users_selector sysid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_users_ids") ))
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_userid_from_path k) res

  let get_all_tenants_ids sysid connector =
    MVar.read connector >>= fun connector ->
    let s = get_all_tenants_selector sysid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_tenents_ids") ))
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_tenantid_from_path k) res

  let get_all_nodes sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_all_nodes_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_nodes") ))
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_nodeid_from_path k) res

  let get_node_info sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_info_path sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_node_info") ))
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ FTypes.node_info_of_string (Yaks.Value.to_string v)
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_node_info") ))
      | exn -> Lwt.fail exn

  let remove_node_info sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path sysid tenantid nodeid in
    Yaks.Workspace.remove p connector.ws

  let add_node_info sysid tenantid nodeid nodeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path sysid tenantid nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_info nodeinfo )in
    Yaks.Workspace.put p value connector.ws

  let add_node_configuration sysid tenantid nodeid nodeconf connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_configuration_path sysid tenantid nodeid in
    let value = Yaks.Value.StringValue (FAgentTypes.string_of_configuration nodeconf )in
    Yaks.Workspace.put p value connector.ws


  let get_all_fdus sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_all_fdu_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_fdus") ))
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_fduid_from_path k) res

  let get_fdu_info sysid tenantid fduid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_fdu_info_path sysid tenantid fduid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_fdu_info") ))
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ FTypes.fdu_of_string (Yaks.Value.to_string v)
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_fdu_info") ))
      | exn -> Lwt.fail exn

  let add_fdu_info sysid tenantid fduid fduinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_fdu_info_path sysid tenantid fduid in
    let value = Yaks.Value.StringValue (FTypes.string_of_fdu fduinfo )in
    Yaks.Workspace.put p value connector.ws

  let remove_fdu_info sysid tenantid fduid connector =
    MVar.read connector >>= fun connector ->
    let p = get_fdu_info_path sysid tenantid fduid in
    Yaks.Workspace.remove p connector.ws

  let observe_fdu sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_all_fdu_selector sysid tenantid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ Fos_im.FTypes.fdu_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let get_all_plugins_ids sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_plugins_selector sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_plugins_ids") ))
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_pluginid_from_path k) res

  let get_plugin_info sysid tenantid nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path sysid tenantid nodeid pluginid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_plugin_info") ))
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ FTypes.plugin_of_string (Yaks.Value.to_string v)
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_plugin_info") ))
      | exn -> Lwt.fail exn

  let add_node_plugin sysid tenantid nodeid (plugininfo:FTypes.plugin) connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path sysid tenantid nodeid plugininfo.uuid  in
    let value = Yaks.Value.StringValue (FTypes.string_of_plugin plugininfo) in
    Yaks.Workspace.put p value connector.ws

  let observe_node_plugins sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_plugins_subscriber_selector sysid tenantid nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.plugin_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let get_node_plugins sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_plugins_selector sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws >>=
    fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plguins received empty data!!") ))
    | _ ->
      Lwt_list.map_p (fun (_,v) ->
          Lwt.return @@ FTypes.plugin_of_string (Yaks.Value.to_string v))
        kvs


  let add_plugin_eval sysid tenantid nodeid pluginid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_node_plugin_eval_path sysid tenantid nodeid pluginid func_name in
    let cb _ props =
      Lwt.return @@ Yaks.Value.StringValue (func props)
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let observe_node_fdu sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_fdu_selector sysid tenantid nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ Fos_im.FTypesRecord.fdu_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_fdu sysid tenantid nodeid fduid (fduinfo:FTypesRecord.fdu) connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path sysid tenantid nodeid fduid in
    let value = Yaks.Value.StringValue (Fos_im.FTypesRecord.string_of_fdu fduinfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_fdus sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_fdu_selector sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_fdu_info received empty data!!") ))
    | _ ->
      Lwt_list.map_p (fun (k,v) -> Lwt.return (
          extract_nodeid_from_path k,
          extract_node_fduid_from_path k,
          Fos_im.FTypesRecord.fdu_of_string (Yaks.Value.to_string v) )) kvs

  let remove_node_fdu sysid tenantid nodeid fduid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path sysid tenantid nodeid fduid in
    Yaks.Workspace.remove p connector.ws

  let get_node_fdu_info sysid tenantid nodeid fduid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_fdu_info_path sysid tenantid nodeid fduid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_fdu_info received empty data!!") ))
    | _ ->
      let _,v = List.hd kvs in
      Lwt.return @@ Fos_im.FTypesRecord.fdu_of_string (Yaks.Value.to_string v)

  (* Global Network descriptors *)
  let add_network sysid tenantid netid net_info connector =
    let p = get_network_info_path sysid tenantid netid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (FTypes.string_of_virtual_network net_info)) connector.ws

  let get_network sysid tenantid netid connector =
    let s = Yaks.Selector.of_path @@ get_network_info_path sysid tenantid netid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_network received empty data!!") ))
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ FTypes.virtual_network_of_string (Yaks.Value.to_string v)

  let observe_network sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_all_networks_selector sysid tenantid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ Fos_im.FTypes.virtual_network_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_network sysid tenantid netid connector =
    let p = get_network_info_path sysid tenantid netid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_networks sysid tenantid connector =
    let s = get_all_networks_selector sysid tenantid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_network received empty data!!") ))
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ FTypes.virtual_network_of_string (Yaks.Value.to_string v)) kvs

  let add_port sysid tenantid portid port_info connector =
    let p = get_network_port_info_path sysid tenantid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (FTypes.string_of_connection_point port_info)) connector.ws

  let get_port sysid tenantid portid connector =
    let s = Yaks.Selector.of_path @@ get_network_port_info_path sysid tenantid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_port received empty data!!") ))
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ FTypes.connection_point_of_string (Yaks.Value.to_string v)

  let observe_ports sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_network_ports_selector sysid tenantid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ Fos_im.FTypes.connection_point_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_port sysid tenantid portid connector =
    let p = get_network_port_info_path sysid tenantid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_ports sysid tenantid connector =
    let s = get_network_ports_selector sysid tenantid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_all_ports received empty data!!") ))
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ FTypes.connection_point_of_string (Yaks.Value.to_string v)) kvs

  (* Node Network records *)

  let add_node_network sysid tenantid nodeid netid net_info connector =
    let p = get_node_network_info_path sysid tenantid nodeid netid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (FTypesRecord.string_of_virtual_network net_info)) connector.ws

  let get_node_network sysid tenantid nodeid netid connector =
    let s = Yaks.Selector.of_path @@ get_node_network_info_path sysid tenantid nodeid netid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_network received empty data!!") ))
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ FTypesRecord.virtual_network_of_string (Yaks.Value.to_string v)

  let observe_node_network sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_all_node_networks_selector sysid tenantid nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypesRecord.virtual_network_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_node_network sysid tenantid nodeid netid connector =
    let p = get_node_network_info_path sysid tenantid nodeid netid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_node_networks sysid tenantid nodeid connector =
    let s = get_all_node_networks_selector sysid tenantid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_all_node_networks received empty data!!") ))
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ FTypesRecord.virtual_network_of_string (Yaks.Value.to_string v)) kvs

  let add_node_port sysid tenantid nodeid portid port_info connector =
    let p = get_node_network_port_info_path sysid tenantid nodeid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (FTypesRecord.string_of_connection_point port_info)) connector.ws

  let get_node_port sysid tenantid nodeid portid connector =
    let s = Yaks.Selector.of_path @@ get_node_network_port_info_path sysid tenantid nodeid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_port received empty data!!") ))
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ FTypesRecord.connection_point_of_string (Yaks.Value.to_string v)

  let observe_node_ports sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_ports_selector sysid tenantid nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypesRecord.connection_point_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_node_port sysid tenantid nodeid portid connector =
    let p = get_node_network_port_info_path sysid tenantid portid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_node_ports sysid tenantid nodeid connector =
    let s = get_node_network_ports_selector sysid tenantid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_all_node_ports received empty data!!") ))
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ FTypesRecord.connection_point_of_string (Yaks.Value.to_string v)) kvs
end


module MakeLAD(P: sig val prefix: string end) = struct
  let get_node_info_path nodeid =
    create_path [P.prefix; nodeid; "info"]

  let get_node_configuration_path nodeid =
    create_path [P.prefix; nodeid; "configuration"]

  let get_node_plugins_selector nodeid =
    create_selector [P.prefix; nodeid; "plugins"; "*"; "info"]

  let get_node_plugins_subscriber_selector nodeid =
    create_selector [P.prefix; nodeid; "plugins"; "*"; "info"]

  let get_node_plugin_info_path nodeid pluginid=
    create_path [P.prefix; nodeid; "plugins"; pluginid; "info"]

  let get_node_runtimes_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"]

  let get_node_network_managers_selector nodeid =
    create_selector [P.prefix; nodeid; "network_managers"; "*"]

  let get_node_runtime_fdus_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  let get_node_fdus_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"; "fdu"; "*"; "info"]

  let get_node_fdus_subscriber_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  let get_node_runtime_fdu_atomic_entitiy_selector nodeid pluginid fduid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "atomic_entity"; "*"]

  let get_node_fdu_info_path nodeid pluginid fduid=
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "info"]

  let get_node_image_info_path nodeid pluginid imgid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "images"; imgid; "info"]

  let get_node_flavor_info_path nodeid pluginid flvid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "flavors"; flvid; "info"]

  let get_node_fdu_atomic_entity_info_path nodeid pluginid fduid atomicid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "atomic_entity"; atomicid; "info"]

  let get_node_networks_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "network_managers"; pluginid; "networks"; "*"; "info"]

  let get_node_networks_find_selector nodeid netid =
    create_path [P.prefix; nodeid; "network_managers"; "*"; "networks"; netid; "info"]


  let get_node_network_info_path nodeid pluginid networkid =
    create_path [P.prefix; nodeid; "network_managers"; pluginid;"networks"; networkid; "info"]

  let get_node_network_port_info_path nodeid pluginid portid =
    create_path [P.prefix; nodeid; "network_managers"; pluginid; "ports"; portid; "info"]

  let get_node_network_ports_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "network_managers"; pluginid; "ports"; "*"; "info"]

  let get_node_os_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "os"; "exec"; func_name]

  let get_node_plugin_eval_path nodeid pluginid func_name =
    create_path [P.prefix; nodeid; "plugins"; pluginid; "exec"; func_name ]

  let get_agent_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "agent"; "exec"; func_name]

  let extract_pluginid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let add_agent_eval nodeid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_agent_exec_path nodeid func_name in
    let cb _ props =
      let%lwt r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let add_os_eval nodeid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_node_os_exec_path nodeid func_name in
    let cb _ props =
      let%lwt r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let add_plugin_eval nodeid pluginid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_node_plugin_eval_path nodeid pluginid func_name in
    let cb _ props =
      let%lwt r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}


  let observe_node_plugins nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_plugins_subscriber_selector nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.plugin_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let observe_node_plugin nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path nodeid pluginid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.plugin_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_info nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_info_path nodeid  in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.node_info_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_plugin nodeid (plugininfo:FTypes.plugin) connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path nodeid plugininfo.uuid in
    let value = Yaks.Value.StringValue (FTypes.string_of_plugin plugininfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_plugin nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path nodeid pluginid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plugin received empty data!!") ))
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@ FTypes.plugin_of_string (Yaks.Value.to_string v)

  let get_node_plugins nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_plugins_selector nodeid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plugin received empty data!!") ))
    | _ ->  Lwt_list.map_p (fun (k,_ )-> Lwt.return @@ extract_pluginid_from_path k) data

  let remove_node_plugin nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path nodeid pluginid in
    Yaks.Workspace.remove p connector.ws

  let add_node_info nodeid nodeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path  nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_info nodeinfo )in
    Yaks.Workspace.put p value connector.ws

  let add_node_configuration nodeid nodeconf connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_configuration_path nodeid in
    let value = Yaks.Value.StringValue (FAgentTypes.string_of_configuration nodeconf )in
    Yaks.Workspace.put p value connector.ws

  let observe_node_runtime_fdu nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_runtime_fdus_selector nodeid pluginid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypesRecord.fdu_of_string(Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_fdu nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_fdus_selector nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypesRecord.fdu_of_string(Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_fdu nodeid pluginid fduid fduinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid in
    let value = Yaks.Value.StringValue (FTypesRecord.string_of_fdu fduinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_fdu nodeid pluginid fduid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_network nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_networks_selector nodeid "*" in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypesRecord.virtual_network_of_string(Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_network nodeid pluginid netid netinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_info_path nodeid pluginid netid in
    let value = Yaks.Value.StringValue (FTypesRecord.string_of_virtual_network netinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_network nodeid pluginid netid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_info_path nodeid pluginid netid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_port nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_ports_selector nodeid "*" in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypesRecord.connection_point_of_string(Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_port nodeid pluginid portid portinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_port_info_path nodeid pluginid portid in
    let value = Yaks.Value.StringValue (FTypesRecord.string_of_connection_point portinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_port nodeid pluginid portid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_port_info_path nodeid pluginid portid in
    Yaks.Workspace.remove p connector.ws

end

module MakeCLAD(P: sig val prefix: string end) = struct
  let get_node_info_path nodeid =
    create_path [P.prefix; nodeid; "info"]

  let get_node_selector =
    create_selector [P.prefix; "*"; "info"]

  let get_node_configuration_path nodeid =
    create_path [P.prefix; nodeid; "configuration"]

  let get_node_plugins_selector nodeid =
    create_selector [P.prefix; nodeid; "plugins"; "*"; "info"]

  let get_node_plugins_subscriber_selector nodeid =
    create_selector [P.prefix; nodeid; "plugins"; "*"; "info"]

  let get_node_plugin_info_path nodeid pluginid=
    create_path [P.prefix; nodeid; "plugins"; pluginid; "info"]

  let get_node_runtimes_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"]

  let get_node_runtime_fdus_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  let get_node_fdus_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"; "fdu"; "*"; "info"]

  let get_node_fdus_subscriber_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  (* let get_node_runtime_fdu_atomic_entitiy_selector nodeid pluginid fduid =
     create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "atomic_entity"; "*"] *)

  let get_node_fdu_info_path nodeid pluginid fduid=
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "info"]

  let get_node_image_info_path nodeid pluginid imgid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "images"; imgid; "info"]

  let get_node_flavor_info_path nodeid pluginid flvid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "flavors"; flvid; "info"]

  (* let get_node_fdu_atomic_entity_info_path nodeid pluginid fduid atomicid =
     create_path [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "atomic_entity"; atomicid; "info"] *)

  let get_node_os_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "os"; "exec"; func_name]

  let get_agent_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "agent"; "exec"; func_name]


  let get_node_plugin_eval_path nodeid pluginid func_name =
    create_path [P.prefix; nodeid; "plugins"; pluginid; "exec"; func_name ]

  let extract_pluginid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_nodeid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 2

  let add_os_eval nodeid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_node_os_exec_path nodeid func_name in
    let cb _ props =
      let r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}


  let add_agent_eval nodeid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_agent_exec_path nodeid func_name in
    let cb _ props =
      let%lwt r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let add_plugin_eval nodeid pluginid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_node_plugin_eval_path nodeid pluginid func_name in
    let cb _ props =
      Lwt.return @@ Yaks.Value.StringValue (func props)
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let observe_nodes callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_selector in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.node_info_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node nodeid nodeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path nodeid  in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_info nodeinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path nodeid  in
    Yaks.Workspace.remove p connector.ws

  let observe_node_plugins nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_plugins_subscriber_selector nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.plugin_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let observe_node_plugin nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path nodeid pluginid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.plugin_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_info nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_info_path nodeid  in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ FTypes.node_info_of_string (Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_plugin nodeid (plugininfo:FTypes.plugin) connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path nodeid plugininfo.uuid in
    let value = Yaks.Value.StringValue (FTypes.string_of_plugin plugininfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_plugin nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path nodeid pluginid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plugin received empty data!!") ))
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@ FTypes.plugin_of_string (Yaks.Value.to_string v)

  let get_node_plugins nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_plugins_selector nodeid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plugin received empty data!!") ))
    | _ ->  Lwt_list.map_p (fun (k,_ )-> Lwt.return @@ extract_pluginid_from_path k) data

  let remove_node_plugin nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path nodeid pluginid in
    Yaks.Workspace.remove p connector.ws

  let add_node_info nodeid nodeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path  nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_info nodeinfo )in
    Yaks.Workspace.put p value connector.ws

  let add_node_configuration nodeid nodeconf connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_configuration_path nodeid in
    let value = Yaks.Value.StringValue (FAgentTypes.string_of_configuration nodeconf )in
    Yaks.Workspace.put p value connector.ws

  let observe_node_runtime_fdu nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_runtime_fdus_selector nodeid pluginid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ Fos_im.FTypesRecord.fdu_of_string(Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_fdu nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_fdus_selector nodeid in
    let cb data =
      match data with
      | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
      | _ ->
        let _,v = List.hd data in
        callback @@ Fos_im.FTypesRecord.fdu_of_string(Yaks.Value.to_string v)
    in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:cb s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_fdu nodeid pluginid fduid fduinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid in
    let value = Yaks.Value.StringValue (Fos_im.FTypesRecord.string_of_fdu fduinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_fdu nodeid pluginid fduid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid in
    Yaks.Workspace.remove p connector.ws

end

module Global = struct

  module Actual = MakeGAD(struct let prefix = global_actual_prefix end)
  module Desired = MakeGAD(struct let prefix = global_desired_prefix end)


end

module Local = struct

  module Actual = MakeLAD(struct let prefix = local_actual_prefix end)
  module Desired = MakeLAD(struct let prefix = local_desired_prefix end)

end

module LocalConstraint = struct
  module Actual = MakeCLAD(struct let prefix  = local_constraint_actual_prefix end )
  module Desired = MakeCLAD(struct let prefix = local_constaint_desired_prefix end)

end
