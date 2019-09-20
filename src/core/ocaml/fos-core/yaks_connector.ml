open Yaks_ocaml
open Lwt.Infix
open Fos_core
open Fos_im
open Errors



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
; listeners : Yaks_api.subid list
; evals : Yaks.Path.t list;
}

type connector = state MVar.t


let get_connector (config:configuration)=
  (* let loc = Apero.Option.get @@ Apero_net.Locator.of_string config.agent.yaks in
     let%lwt yclient = Yaks.login loc Apero.Properties.empty in *)
  let%lwt yclient = Yaks.login  config.agent.yaks Apero.Properties.empty in
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

let sub_cb callback of_string extract_uuid (data:(Yaks.Path.t * Yaks.change) list)  =
  match data with
  | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
  | _ ->
    let p,c = List.hd data in
    ( match c with
      | Put tv | Update tv ->
        let v = tv.value in
        callback (Some (of_string (Yaks.Value.to_string v))) false None
      | Remove _ ->
        callback None true (Some (extract_uuid p))
    )

let sub_cb_2ids callback of_string extract_uuid1 extract_uuid2 (data:(Yaks.Path.t * Yaks.change) list)  =
  match data with
  | [] -> Lwt.fail @@ FException (`InternalError (`Msg ("Listener received empty data!!") ))
  | _ ->
    let p,c = List.hd data in
    ( match c with
      | Put tv | Update tv ->
        let v = tv.value in
        callback (Some (of_string (Yaks.Value.to_string v))) false None None
      | Remove _ ->
        callback None true (Some (extract_uuid1 p)) (Some (extract_uuid2 p))


    )

module MakeGAD(P: sig val prefix: string end) = struct

  (* System *)
  let get_sys_info_path sysid =
    create_path [P.prefix; sysid; "info"]

  let get_sys_configuration_path sysid =
    create_path [P.prefix; sysid; "configuration"]

  let get_all_users_selector sysid =
    create_selector [P.prefix; sysid; "users"; "*"]

  let get_user_info_path sysid userid =
    create_path [P.prefix; sysid; "users"; userid; "info"]

  (* Tenants *)
  let get_all_tenants_selector sysid =
    create_selector [P.prefix; sysid; "tenants"; "*"]

  let get_tenant_info_path sysid tenantid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "info"]

  let get_tenant_configuration_path sysid tenantid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "configuration"]

  (* Catalog *)

  let get_catalog_atomic_entity_info_path sysid tenantid aeid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "catalog"; "atomic-entities"; aeid; "info"]

  let get_catalog_all_atomic_entity_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "catalog"; "atomic-entities"; "*"; "info"]

  let get_catalog_fdu_info_path sysid tenantid fduid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "catalog"; "fdu"; fduid; "info"]

  let get_catalog_all_fdu_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "catalog"; "fdu"; "*"; "info"]

  let get_catalog_entity_info_path sysid tenantid eid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "catalog"; "entities"; eid; "info"]

  let get_catalog_all_entities_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "catalog"; "entities"; "*"; "info"]

  (* Records *)

  let get_records_atomic_entity_instance_info_path sysid tenantid aeid instance_id =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "records"; "atomic-entities"; aeid; "instances"; instance_id; "info"]

  let get_records_all_atomic_entity_instance_selector sysid tenantid aeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "records"; "atomic-entities"; aeid; "instances"; "*"; "info"]

  let get_records_all_atomic_entities_instance_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "records"; "atomic-entities"; "*"; "instances"; "*"; "info"]

  let get_records_entity_instance_info_path sysid tenantid eid instance_id =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "records"; "entities"; eid; "instances"; instance_id; "info"]

  let get_records_all_entity_instances_selector sysid tenantid eid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "records"; "entities"; eid; "instances"; "*"; "info"]

  let get_records_all_entities_instances_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "records"; "entities"; "*"; "instances"; "*"; "info"]


  (* Nodes *)

  let get_all_nodes_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; "*"; "info"]

  let get_node_info_path sysid tenantid nodeid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "info"]

  let get_node_configuration_path sysid tenantid nodeid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "configuration"]

  let get_node_status_path sysid tenantid nodeid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "status"]

  let get_node_plugins_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; "*"; "info"]

  let get_node_plugins_subscriber_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; "*"; "info"]

  let get_node_plugin_info_path sysid tenantid nodeid pluginid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; pluginid; "info"]

  let get_node_plugin_eval_path sysid tenantid nodeid pluginid func_name =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "plugins"; pluginid; "exec"; func_name]

  let get_node_fdu_info_path sysid tenantid nodeid fduid instanceid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "fdu"; fduid; "instances"; instanceid ;"info"]

  (* Node FDUs *)

  let get_node_fdu_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "fdu"; "*"; "instances"; "*"; "info"]

  let get_node_fdu_instances_selector sysid tenantid nodeid fduid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "fdu"; fduid; "instances"; "*"; "info"]

  let get_node_fdu_instance_selector sysid tenantid nodeid instanceid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "fdu"; "*"; "instances"; instanceid; "info"]

  let get_fdu_instance_selector sysid tenantid instanceid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; "*"; "fdu"; "*"; "instances"; instanceid; "info"]

  (* Node Network *)

  let get_node_network_port_info_path sysid tenantid nodeid portid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; "ports"; portid; "info"]

  let get_node_network_ports_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid;"networks"; "ports"; "*"; "info"]

  let get_node_network_port_find_node sysid tenantid portid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; "*";"networks"; "ports"; portid; "info"]

  let get_node_network_router_info_path sysid tenantid nodeid routerid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; "routers"; routerid; "info"]

  let get_node_network_routers_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid;"networks"; "routers"; "*"; "info"]

  let get_all_node_networks_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; "*"; "info"]

  let get_node_network_info_path sysid tenantid nodeid networkid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; networkid; "info"]

  let get_node_network_floating_ip_info_path sysid tenantid nodeid floatingid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; "floating-ips"; floatingid; "info"]

  let get_all_node_network_floating_ips_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "networks"; "floating-ips"; "*"; "info"]


  (* Networoks *)

  let get_all_networks_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "networks"; "*"; "info"]

  let get_network_info_path sysid tenantid networkid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "networks"; networkid; "info"]

  let get_network_port_info_path sysid tenantid portid=
    create_path [P.prefix; sysid; "tenants"; tenantid; "networks"; "ports"; portid; "info"]

  let get_network_ports_selector sysid tenantid  =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "networks"; "ports"; "*"; "info"]

  let get_network_router_info_path sysid tenantid routerid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "networks"; "routers"; routerid; "info"]

  let get_network_routers_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "networks"; "routers"; "*"; "info"]

  (* Images *)

  let get_image_info_path sysid tenantid imageid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "image"; imageid; "info"]

  let get_all_image_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "image"; "*"; "info"]

  (* Node Images *)
  let get_node_image_info_path sysid tenantid nodeid imageid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "image"; imageid; "info"]

  let get_all_node_image_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "image"; "*"; "info"]

  (* Flavor *)

  let get_flavor_info_path sysid tenantid flavorid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "flavor"; flavorid; "info"]

  let get_all_flavor_selector sysid tenantid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "flavor"; "*"; "info"]

  (* Node Flavor *)

  let get_node_flavor_info_path sysid tenantid nodeid flavorid =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "flavor"; flavorid; "info"]

  let get_all_node_flavor_selector sysid tenantid nodeid =
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "flavor"; "*"; "info"]

  (* Node Evals *)

  let get_agent_exec_path sysid tenantid nodeid func_name =
    create_path [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "agent"; "exec"; func_name]

  let get_agent_exec_path_with_params sysid tenantid nodeid func_name (params: (string * string) list) =
    let rec assoc2args base index list =
      let len = List.length list in
      match index with
      | 0 ->
        let k,v = List.hd list in
        let b = base ^ "(" ^ k ^ "=" ^ v in
        assoc2args b (index+1) list
      | n when n < len ->
        let k,v = List.nth list index in
        let b  = base ^ ";" ^ k ^ "=" ^ v in
        assoc2args b (index+1) list
      | _-> base ^ ")"
    in  let  p = assoc2args "" 0 params in
    let f = func_name ^ "?" ^ p in
    create_selector [P.prefix; sysid; "tenants"; tenantid; "nodes"; nodeid; "agent"; "exec"; f]



  (* ID extraction *)

  let extract_userid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_tenantid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_entity_id_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 7

  let extract_entity_instanceid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 9

  let extract_aeid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 7

  let extract_aeid_instanceid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 9

  let extract_fduid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 7

  let extract_netid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_imageid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_flavorid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_portid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 7

  let extract_routerid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 7

  let extract_nodeid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_pluginid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let extract_node_fduid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let extract_node_fdu_instanceid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 10

  let extract_node_netid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let extract_node_portid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 9

  let extract_node_routerid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 9

  let extract_node_floatingid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 9

  let extract_node_imageid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let extract_node_flavorid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 9



  (* System *)
  let get_sys_info sysid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_sys_info_path sysid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_sys_info") )) *)
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FAgentTypes.system_info_of_string (Yaks.Value.to_string v))
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
    | [] -> Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_sys_config") )) *)
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FAgentTypes.system_config_of_string (Yaks.Value.to_string v))
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
    | [] ->
      Lwt.return []
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_users_ids") )) *)
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_userid_from_path k) res

  (* Tenants *)

  let get_all_tenants_ids sysid connector =
    MVar.read connector >>= fun connector ->
    let s = get_all_tenants_selector sysid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return []
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_tenents_ids") )) *)
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_tenantid_from_path k) res

  let get_all_nodes sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_all_nodes_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return []
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_all_nodes") )) *)
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_nodeid_from_path k) res

  (* Node *)

  let get_node_configuration sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_configuration_path sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_node_info") )) *)
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@  Some (FAgentTypes.configuration_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_node_configuration") ))
      | exn -> Lwt.fail exn

  let get_node_info sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_info_path sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FTypes.node_info_of_string (Yaks.Value.to_string v))
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

  let get_node_status sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_status_path sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FTypes.node_status_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_node_status") ))

  let observe_node_status sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_status_path sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.node_status_of_string extract_nodeid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let add_node_status sysid tenantid nodeid nodestatus connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_status_path sysid tenantid nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_status nodestatus )in
    Yaks.Workspace.put p value connector.ws

  let remove_node_status sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_status_path sysid tenantid nodeid in
    Yaks.Workspace.remove p connector.ws

  let add_node_configuration sysid tenantid nodeid nodeconf connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_configuration_path sysid tenantid nodeid in
    let value = Yaks.Value.StringValue (FAgentTypes.string_of_configuration nodeconf )in
    Yaks.Workspace.put p value connector.ws


  let get_all_plugins_ids sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_plugins_selector sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_pluginid_from_path k) res

  let get_plugin_info sysid tenantid nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path sysid tenantid nodeid pluginid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FTypes.plugin_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_plugin_info") ))
      | exn -> Lwt.fail exn

  let add_node_plugin sysid tenantid nodeid (plugininfo:FTypes.plugin) connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path sysid tenantid nodeid plugininfo.uuid  in
    let value = Yaks.Value.StringValue (FTypes.string_of_plugin plugininfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_plugin sysid tenantid nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path sysid tenantid nodeid pluginid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_plugins sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_plugins_subscriber_selector sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.plugin_of_string extract_pluginid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let get_node_plugins sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_plugins_selector sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws >>=
    fun kvs ->
    match kvs with
    | [] ->
      Lwt.return []
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

  (* Catalog  *)

  let get_catalog_all_entities sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_catalog_all_entities_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_entity_id_from_path k) res

  let get_catalog_entity_info sysid tenantid eid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_catalog_entity_info_path sysid tenantid eid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (User.Descriptors.Entity.descriptor_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_catalog_entity_info") ))
      | exn -> Lwt.fail exn

  let add_catalog_entity_info sysid tenantid eid einfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_catalog_entity_info_path sysid tenantid eid in
    let value = Yaks.Value.StringValue (User.Descriptors.Entity.string_of_descriptor einfo )in
    Yaks.Workspace.put p value connector.ws

  let remove_catalog_entity_info sysid tenantid aeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_catalog_entity_info_path sysid tenantid aeid in
    Yaks.Workspace.remove p connector.ws

  let observe_catalog_entities sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_catalog_all_entities_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback User.Descriptors.Entity.descriptor_of_string extract_entity_id_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let get_catalog_all_atomic_entities sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_catalog_all_atomic_entity_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_aeid_from_path k) res

  let get_catalog_atomic_entity_info sysid tenantid aeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_catalog_atomic_entity_info_path sysid tenantid aeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (User.Descriptors.AtomicEntity.descriptor_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_fdu_info") ))
      | exn -> Lwt.fail exn

  let add_catalog_atomic_entity_info sysid tenantid aeid aeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_catalog_atomic_entity_info_path sysid tenantid aeid in
    let value = Yaks.Value.StringValue (User.Descriptors.AtomicEntity.string_of_descriptor aeinfo )in
    Yaks.Workspace.put p value connector.ws

  let remove_catalog_atomic_entity_info sysid tenantid aeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_catalog_atomic_entity_info_path sysid tenantid aeid in
    Yaks.Workspace.remove p connector.ws

  let observe_catalog_atomic_entities sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_catalog_all_atomic_entity_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback User.Descriptors.AtomicEntity.descriptor_of_string extract_aeid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let get_catalog_all_fdus sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_catalog_all_fdu_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_fduid_from_path k) res

  let get_catalog_fdu_info sysid tenantid fduid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_catalog_fdu_info_path sysid tenantid fduid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (User.Descriptors.FDU.descriptor_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_fdu_info") ))
      | exn -> Lwt.fail exn

  let add_catalog_fdu_info sysid tenantid fduid fduinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_catalog_fdu_info_path sysid tenantid fduid in
    let value = Yaks.Value.StringValue (User.Descriptors.FDU.string_of_descriptor fduinfo )in
    Yaks.Workspace.put p value connector.ws

  let remove_catalog_fdu_info sysid tenantid fduid connector =
    MVar.read connector >>= fun connector ->
    let p = get_catalog_fdu_info_path sysid tenantid fduid in
    Yaks.Workspace.remove p connector.ws

  let observe_catalog_fdu sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_catalog_all_fdu_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback User.Descriptors.FDU.descriptor_of_string extract_fduid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  (* Record  *)

  let get_records_all_atomic_entities_instances sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_records_all_atomic_entities_instance_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> (extract_aeid_from_path k, extract_aeid_instanceid_from_path k)) res

  let get_records_all_atomic_entity_instances sysid tenantid aeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_records_all_atomic_entity_instance_selector sysid tenantid aeid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_aeid_instanceid_from_path k) res

  let get_records_atomic_entity_instance_info sysid tenantid aeid instanceid connector =
    MVar.read connector >>= fun connector ->
    let s = get_records_atomic_entity_instance_info_path sysid tenantid aeid instanceid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (Infra.Descriptors.AtomicEntity.record_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_fdu_info") ))
      | exn -> Lwt.fail exn

  let add_records_atomic_entity_instance_info sysid tenantid aeid instanceid aeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = Yaks.Path.of_string @@ Yaks.Selector.path @@  get_records_atomic_entity_instance_info_path sysid tenantid aeid instanceid  in
    let value = Yaks.Value.StringValue (Infra.Descriptors.AtomicEntity.string_of_record aeinfo )in
    Yaks.Workspace.put p value connector.ws

  let remove_records_atomic_entity_instance_info sysid tenantid aeid instanceid connector =
    MVar.read connector >>= fun connector ->
    let p = Yaks.Path.of_string @@  Yaks.Selector.path @@ get_records_atomic_entity_instance_info_path sysid tenantid aeid instanceid in
    Yaks.Workspace.remove p connector.ws

  let observe_records_atomic_entities_instances sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_records_all_atomic_entities_instance_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.AtomicEntity.record_of_string extract_aeid_instanceid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let get_records_all_entities_instances sysid tenantid connector =
    MVar.read connector >>= fun connector ->
    let s = get_records_all_entities_instances_selector sysid tenantid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> (extract_entity_id_from_path k, extract_entity_instanceid_from_path k)) res

  let get_records_all_entity_instances sysid tenantid eid connector =
    MVar.read connector >>= fun connector ->
    let s = get_records_all_entity_instances_selector sysid tenantid eid in
    Yaks.Workspace.get s  connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt.return @@ List.map (fun (k,_) -> extract_entity_instanceid_from_path k) res

  let get_records_entity_instance_info sysid tenantid eid instanceid connector =
    MVar.read connector >>= fun connector ->
    let s = get_records_entity_instance_info_path sysid tenantid eid instanceid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (Infra.Descriptors.Entity.record_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_fdu_info") ))
      | exn -> Lwt.fail exn

  let add_records_entity_instance_info sysid tenantid eid instanceid einfo connector =
    MVar.read connector >>= fun connector ->
    let p = Yaks.Path.of_string @@ Yaks.Selector.path @@  get_records_entity_instance_info_path sysid tenantid eid instanceid  in
    let value = Yaks.Value.StringValue (Infra.Descriptors.Entity.string_of_record einfo )in
    Yaks.Workspace.put p value connector.ws

  let remove_records_entity_instance_info sysid tenantid eid instanceid connector =
    MVar.read connector >>= fun connector ->
    let p = Yaks.Path.of_string @@  Yaks.Selector.path @@ get_records_entity_instance_info_path sysid tenantid eid instanceid in
    Yaks.Workspace.remove p connector.ws

  let observe_records_entities_instances sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_records_all_entities_instances_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.Entity.record_of_string extract_entity_instanceid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  (* Node FDU *)

  let observe_node_fdu sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_fdu_selector sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb_2ids callback Infra.Descriptors.FDU.record_of_string extract_node_fduid_from_path extract_node_fdu_instanceid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_fdu sysid tenantid nodeid fduid instanceid (fduinfo:Infra.Descriptors.FDU.record) connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path sysid tenantid nodeid fduid instanceid in
    let value = Yaks.Value.StringValue (Infra.Descriptors.FDU.string_of_record fduinfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_fdus sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_fdu_selector sysid tenantid nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt_list.map_p (fun (k,v) -> Lwt.return (
          extract_nodeid_from_path k,
          extract_node_fduid_from_path k,
          extract_node_fdu_instanceid_from_path k,
          Infra.Descriptors.FDU.record_of_string (Yaks.Value.to_string v) )) kvs

  let get_node_fdu_instances sysid tenantid nodeid fduid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_fdu_instances_selector sysid tenantid nodeid fduid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt_list.map_p (fun (k,v) -> Lwt.return (
          extract_nodeid_from_path k,
          extract_node_fduid_from_path k,
          extract_node_fdu_instanceid_from_path k,
          Infra.Descriptors.FDU.record_of_string (Yaks.Value.to_string v) )) kvs

  let remove_node_fdu sysid tenantid nodeid fduid instanceid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path sysid tenantid nodeid fduid instanceid in
    Yaks.Workspace.remove p connector.ws

  let get_node_fdu_info sysid tenantid nodeid fduid instanceid connector =
    MVar.read connector >>= fun connector ->
    let s =
      match fduid with
      | "*" -> get_node_fdu_instance_selector sysid tenantid nodeid instanceid
      | _ -> Yaks.Selector.of_path @@ get_node_fdu_info_path sysid tenantid nodeid fduid instanceid
    in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return None
    | _ ->
      let _,v = List.hd kvs in
      Lwt.return @@ Some (Infra.Descriptors.FDU.record_of_string (Yaks.Value.to_string v))

  let get_node_instance_info sysid tenantid nodeid instanceid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_fdu_instance_selector sysid tenantid nodeid instanceid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return None
    | _ ->
      let _,v = List.hd kvs in
      Lwt.return @@ Some (Infra.Descriptors.FDU.record_of_string (Yaks.Value.to_string v))

  let get_fdu_nodes sysid tenantid fduid connector =
    MVar.read connector >>= fun connector ->
    let s = get_node_fdu_instances_selector sysid tenantid "*" fduid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return []
    | _ ->
      Lwt_list.map_p (fun (k,_) -> Lwt.return (extract_nodeid_from_path k)) kvs

  let get_fdu_instance_node sysid tenantid instanceid connector =
    MVar.read connector >>= fun connector ->
    let s = get_fdu_instance_selector sysid tenantid instanceid in
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return None
    | _ ->
      let k,_ = List.hd kvs in
      Lwt.return @@ Some (extract_nodeid_from_path k)

  (* Networks *)

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
    | [] ->
      Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_network received empty data!!") )) *)
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (FTypes.virtual_network_of_string (Yaks.Value.to_string v))

  let observe_network sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_all_networks_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.virtual_network_of_string extract_netid_from_path) s connector.ws in
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
    | [] ->
      Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return @@ FTypes.virtual_network_of_string (Yaks.Value.to_string v)) kvs

  let add_port sysid tenantid portid port_info connector =
    let p = get_network_port_info_path sysid tenantid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (User.Descriptors.Network.string_of_connection_point_descriptor port_info)) connector.ws

  let get_port sysid tenantid portid connector =
    let s = Yaks.Selector.of_path @@ get_network_port_info_path sysid tenantid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (User.Descriptors.Network.connection_point_descriptor_of_string (Yaks.Value.to_string v))

  let observe_ports sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_network_ports_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback User.Descriptors.Network.connection_point_descriptor_of_string extract_portid_from_path) s connector.ws in
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
    | [] -> Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ User.Descriptors.Network.connection_point_descriptor_of_string (Yaks.Value.to_string v)) kvs

  let add_router sysid tenantid routerid router_info connector =
    let p = get_network_router_info_path sysid tenantid routerid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (Router.string_of_descriptor router_info)) connector.ws

  let get_router sysid tenantid routerid connector =
    let s = Yaks.Selector.of_path @@ get_network_router_info_path sysid tenantid routerid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (Router.descriptor_of_string (Yaks.Value.to_string v))


  let observe_routers sysid tenantid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_network_routers_selector sysid tenantid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Router.descriptor_of_string extract_routerid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_router sysid tenantid routerid connector =
    let p = get_network_router_info_path sysid tenantid routerid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_routers sysid tenantid connector =
    let s = get_network_routers_selector sysid tenantid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ Router.descriptor_of_string (Yaks.Value.to_string v)) kvs


  (* Node Network *)

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
    | [] -> Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (FTypesRecord.virtual_network_of_string (Yaks.Value.to_string v))

  let observe_node_network sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_all_node_networks_selector sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypesRecord.virtual_network_of_string extract_node_netid_from_path) s connector.ws in
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
    | [] ->
      Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ FTypesRecord.virtual_network_of_string (Yaks.Value.to_string v)) kvs

  let add_node_port sysid tenantid nodeid portid port_info connector =
    let p = get_node_network_port_info_path sysid tenantid nodeid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (Infra.Descriptors.Network.string_of_connection_point_record port_info)) connector.ws

  let get_node_port sysid tenantid nodeid portid connector =
    let s = Yaks.Selector.of_path @@ get_node_network_port_info_path sysid tenantid nodeid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (Infra.Descriptors.Network.connection_point_record_of_string (Yaks.Value.to_string v))

  let find_node_port sysid tenantid portid connector =
    let s = get_node_network_port_find_node sysid tenantid portid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    | _ -> let p,_ = List.hd kvs in
      Lwt.return @@ Some (extract_nodeid_from_path p)

  let observe_node_ports sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_ports_selector sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.Network.connection_point_record_of_string extract_node_portid_from_path) s connector.ws in
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
    | [] -> Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ Infra.Descriptors.Network.connection_point_record_of_string (Yaks.Value.to_string v)) kvs

  let add_node_router sysid tenantid nodeid routerid router_info connector =
    let p = get_node_network_router_info_path sysid tenantid nodeid routerid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (Router.string_of_descriptor router_info)) connector.ws

  let get_router sysid tenantid nodeid routerid connector =
    let s = Yaks.Selector.of_path @@ get_node_network_router_info_path sysid tenantid nodeid routerid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] ->
      Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (Router.descriptor_of_string (Yaks.Value.to_string v))

  let observe_node_routers sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_routers_selector sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Router.descriptor_of_string extract_node_routerid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_node_router sysid tenantid nodeid routerid connector =
    let p = get_node_network_router_info_path sysid tenantid nodeid routerid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_node_routers sysid tenantid nodeid connector =
    let s = get_node_network_routers_selector sysid tenantid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ Router.descriptor_of_string (Yaks.Value.to_string v)) kvs

  let add_node_floating_ip sysid tenantid nodeid floatingid ip_info connector =
    let p = get_node_network_floating_ip_info_path sysid tenantid nodeid floatingid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (FTypes.string_of_floating_ip ip_info)) connector.ws

  let get_node_floatin_ip sysid tenantid nodeid floatingid connector =
    let s = Yaks.Selector.of_path @@ get_node_network_floating_ip_info_path sysid tenantid nodeid floatingid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (FTypes.floating_ip_of_string (Yaks.Value.to_string v))

  let observe_node_floating_ips sysid tenantid nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_all_node_network_floating_ips_selector sysid tenantid nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.floating_ip_of_string extract_node_floatingid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_node_floating_ip sysid tenantid nodeid floatingid connector =
    let p = get_node_network_floating_ip_info_path sysid tenantid floatingid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_all_node_floating_ips sysid tenantid nodeid connector =
    let s = get_all_node_network_floating_ips_selector sysid tenantid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ ->
      Lwt_list.map_p (
        fun (_,v )-> Lwt.return  @@ FTypes.floating_ip_of_string (Yaks.Value.to_string v)) kvs

  (* Images *)

  let add_image sysid tenantid imageid imageinfo connector =
    let p = get_image_info_path sysid tenantid imageid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (User.Descriptors.FDU.string_of_image imageinfo)) connector.ws

  let remove_image sysid tenantid imageid connector =
    let p = get_image_info_path sysid tenantid imageid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_image sysid tenantid imageid connector =
    let s = Yaks.Selector.of_path @@ get_image_info_path sysid tenantid imageid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (User.Descriptors.FDU.image_of_string (Yaks.Value.to_string v ))

  let get_all_images sysid tenantid connector =
    let s = get_all_image_selector sysid tenantid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ -> Lwt_list.map_p(fun (_,v) ->
        Lwt.return @@ User.Descriptors.FDU.image_of_string (Yaks.Value.to_string v)
      ) kvs

  let observe_images sysid tenantid callback connector =
    let s = get_all_image_selector sysid tenantid in
    MVar.guarded connector @@ fun connector ->
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback User.Descriptors.FDU.image_of_string extract_imageid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  (* Node Images *)

  let add_node_image sysid tenantid  nodeid imageid imageinfo connector =
    let p = get_node_image_info_path sysid tenantid nodeid imageid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (Infra.Descriptors.FDU.string_of_image imageinfo)) connector.ws

  let remove__node_image sysid tenantid nodeid imageid connector =
    let p = get_node_image_info_path sysid tenantid nodeid imageid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_node_image sysid tenantid nodeid imageid connector =
    let s = Yaks.Selector.of_path @@ get_node_image_info_path sysid tenantid nodeid imageid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_node_image received empty data!!") )) *)
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (Infra.Descriptors.FDU.image_of_string (Yaks.Value.to_string v ))

  let get_all_node_images sysid tenantid nodeid connector =
    let s = get_all_node_image_selector sysid tenantid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ -> Lwt_list.map_p(fun (_,v) ->
        Lwt.return @@ Infra.Descriptors.FDU.image_of_string (Yaks.Value.to_string v)
      ) kvs

  let observe_node_images sysid tenantid nodeid callback connector =
    let s = get_all_node_image_selector sysid tenantid nodeid in
    MVar.guarded connector @@ fun connector ->
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.FDU.image_of_string extract_node_imageid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  (* Flavors *)

  let add_flavor sysid tenantid flavorid flavorinfo connector =
    let p = get_flavor_info_path sysid tenantid flavorid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (User.Descriptors.FDU.string_of_computational_requirements flavorinfo)) connector.ws

  let remove_flavor sysid tenantid flavorid connector =
    let p = get_flavor_info_path sysid tenantid flavorid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_flavor sysid tenantid flavorid connector =
    let s = Yaks.Selector.of_path @@ get_flavor_info_path sysid tenantid flavorid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (User.Descriptors.FDU.computational_requirements_of_string (Yaks.Value.to_string v ))

  let get_all_flavors sysid tenantid connector =
    let s = get_all_flavor_selector sysid tenantid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ -> Lwt_list.map_p(fun (_,v) ->
        Lwt.return @@ User.Descriptors.FDU.computational_requirements_of_string (Yaks.Value.to_string v)
      ) kvs

  let observe_flavors sysid tenantid callback connector =
    let s = get_all_flavor_selector sysid tenantid in
    MVar.guarded connector @@ fun connector ->
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback User.Descriptors.FDU.computational_requirements_of_string extract_flavorid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  (* Node Flavors *)

  let add_node_flavor sysid tenantid nodeid flavorid flavorinfo connector =
    let p = get_node_flavor_info_path sysid tenantid nodeid flavorid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.put p (Yaks.Value.StringValue (Infra.Descriptors.FDU.string_of_computational_requirements flavorinfo)) connector.ws

  let remove_node_flavor sysid tenantid nodeid flavorid connector =
    let p = get_node_flavor_info_path sysid tenantid flavorid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.remove p connector.ws

  let get_node_flavor sysid tenantid nodeid flavorid connector =
    let s = Yaks.Selector.of_path @@ get_node_flavor_info_path sysid tenantid nodeid flavorid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return None
    | _ -> let _,v = List.hd kvs in
      Lwt.return @@ Some (Infra.Descriptors.FDU.computational_requirements_of_string (Yaks.Value.to_string v ))

  let get_all_node_flavors sysid tenantid nodeid connector =
    let s = get_all_node_flavor_selector sysid tenantid nodeid in
    MVar.read connector >>= fun connector ->
    Yaks.Workspace.get s connector.ws
    >>= fun kvs ->
    match kvs with
    | [] -> Lwt.return []
    | _ -> Lwt_list.map_p(fun (_,v) ->
        Lwt.return @@ Infra.Descriptors.FDU.computational_requirements_of_string (Yaks.Value.to_string v)
      ) kvs

  let observe_node_flavors sysid tenantid nodeid callback connector =
    let s = get_all_node_flavor_selector sysid tenantid nodeid in
    MVar.guarded connector @@ fun connector ->
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.FDU.computational_requirements_of_string extract_node_flavorid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  (* Agent Evals *)
  let add_agent_eval sysid tenantid nodeid func_name func connector =
    MVar.guarded connector @@ fun connector ->
    let p = get_agent_exec_path sysid tenantid nodeid func_name in
    let cb _ props =
      let%lwt r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let exec_multi_node_eval sysid tenantid  func_name parametes connector =
    MVar.read connector >>= fun connector ->
    let s = get_agent_exec_path_with_params sysid tenantid "*" func_name parametes
    in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return []
    | lst ->
      Lwt_list.map_p (fun (_,v) ->
          try
            Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))
          with
          | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
            Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in exec_nm_eval") ))
        ) lst

  (* FDU Eval *)

  let onboard_fdu_from_node sysid tenantid nodeid fdu_info connector =
    MVar.read connector >>= fun connector ->
    let fname = "onboard_fdu" in
    let params = [("descriptor",User.Descriptors.FDU.string_of_descriptor fdu_info)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let define_fdu_in_node sysid tenantid nodeid fdu_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "define_fdu" in
    let params = [("fdu_id",fdu_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  (* Atomic Entity Eval *)

  let onboard_ae_from_node sysid tenantid nodeid ae_info connector =
    MVar.read connector >>= fun connector ->
    let fname = "onboard_ae" in
    let params = [("descriptor",User.Descriptors.AtomicEntity.string_of_descriptor ae_info)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let instantiate_ae_from_node sysid tenantid nodeid ae_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "instantiate_ae" in
    let params = [("ae_id",ae_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let offload_ae_from_node sysid tenantid nodeid ae_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "offload_ae" in
    let params = [("ae_id",ae_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let terminate_ae_from_node sysid tenantid nodeid ae_inst_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "terminate_ae" in
    let params = [("instance_id",ae_inst_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  (* Entity Eval *)

  let onboard_entity_from_node sysid tenantid nodeid ae_info connector =
    MVar.read connector >>= fun connector ->
    let fname = "onboard_entity" in
    let params = [("descriptor",User.Descriptors.Entity.string_of_descriptor ae_info)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let instantiate_entity_from_node sysid tenantid nodeid ae_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "instantiate_entity" in
    let params = [("entity_id",ae_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let offload_entity_from_node sysid tenantid nodeid ae_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "offload_entity" in
    let params = [("entity_id",ae_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let terminate_entity_from_node sysid tenantid nodeid ae_inst_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "terminate_entity" in
    let params = [("instance_id",ae_inst_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))


  (* Node CP eval *)

  let create_cp_in_node sysid tenantid nodeid cp connector =
    MVar.read connector >>= fun connector ->
    let fname = "create_cp" in
    let params = [("descriptor",User.Descriptors.Network.string_of_connection_point_descriptor cp)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let remove_cp_from_node sysid tenantid nodeid cpid connector =
    MVar.read connector >>= fun connector ->
    let fname = "remove_cp" in
    let params = [("cp_id",cpid)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let connect_cp_to_interface sysid tenantid nodeid cpid instanceid face connector =
    MVar.read connector >>= fun connector ->
    let fname = "connect_cp_to_face" in
    let params = [("cp_id",cpid);("instance_id",instanceid);("interface",face)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let disconnect_cp_from_interface sysid tenantid nodeid face instanceid connector =
    MVar.read connector >>= fun connector ->
    let fname = "disconnect_cp_from_face" in
    let params = [("interface",face);("instance_id",instanceid)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))


  let connect_cp_to_network sysid tenantid nodeid cpid netid connector =
    MVar.read connector >>= fun connector ->
    let fname = "add_port_to_network" in
    let params = [("cp_uuid",cpid);("network_uuid",netid)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let disconnect_cp_from_network sysid tenantid nodeid cpid connector =
    MVar.read connector >>= fun connector ->
    let fname = "remove_port_from_network" in
    let params = [("cp_uuid",cpid)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  (* Node Network Eval *)

  let create_network_in_node sysid tenantid nodeid net connector =
    MVar.read connector >>= fun connector ->
    let fname = "create_node_network" in
    let params = [("descriptor",FTypes.string_of_virtual_network net)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let remove_network_from_node sysid tenantid nodeid net_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "remove_node_netwotk" in
    let params = [("net_id",net_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  (* Node Floating Ip eval *)

  let create_floating_ip_in_node sysid tenantid nodeid connector =
    MVar.read connector >>= fun connector ->
    let fname = "create_floating_ip" in
    let s = Yaks.Selector.of_path @@ get_agent_exec_path sysid tenantid nodeid fname in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let delete_floating_ip_from_node sysid tenantid nodeid ip_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "delete_floating_ip" in
    let params = [("ip_id",ip_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let assing_floating_ip_in_node sysid tenantid nodeid ip_id cp_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "assign_floating_ip" in
    let params = [("ip_id",ip_id);("cp_id",cp_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let remove_floating_ip_from_node sysid tenantid nodeid ip_id cp_id connector =
    MVar.read connector >>= fun connector ->
    let fname = "remove_floating_ip" in
    let params = [("ip_id",ip_id);("cp_id",cp_id)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  (* Router Ports Eval *)

  let add_router_port_in_node sysid tenantid nodeid router_id port_type vnet_id ip_address connector =
    MVar.read connector >>= fun connector ->
    let fname = "add_router_port" in
    let parameters = [("router_id", router_id); ("port_type", port_type)] in
    let parameters =
      match vnet_id with
      | Some vid -> parameters @ [("vnet_id",vid)]
      | None -> parameters
    in
    let parameters =
      match ip_address with
      | Some ip -> parameters @ [("ip_address",ip)]
      | None -> parameters
    in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname parameters in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

  let remove_router_port_from_node sysid tenantid nodeid rid vid connector =
    MVar.read connector >>= fun connector ->
    let fname = "remove_router_port" in
    let params = [("router_id", rid); ("vnet_id", vid)] in
    let s = get_agent_exec_path_with_params sysid tenantid nodeid fname params in
    let%lwt res = Yaks.Workspace.get s connector.ws in
    match res with
    | [] ->  Lwt.fail @@ FException (`InternalError (`Msg ("Empty value for agent_eval") ))
    | (_,v)::_ ->
      Lwt.return (Agent_types.eval_result_of_string (Yaks.Value.to_string v))

end


module MakeLAD(P: sig val prefix: string end) = struct

  (* Node *)
  let get_node_info_path nodeid =
    create_path [P.prefix; nodeid; "info"]

  let get_node_configuration_path nodeid =
    create_path [P.prefix; nodeid; "configuration"]

  let get_node_status_path nodeid =
    create_path [P.prefix; nodeid; "status"]

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

  (* Node FDUs *)

  let get_node_runtime_fdus_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  let get_node_fdus_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"; "fdu"; "*"; "instances"; "*"; "info"]

  let get_node_fdu_info_path nodeid pluginid fduid instanceid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "instances"; instanceid; "info"]

  let get_node_fdus_subscriber_selector nodeid =
    create_selector [P.prefix; nodeid;  "runtimes"; "*"; "fdu"; "*"; "instances"; "*"; "info"]

  let get_node_fdu_instances_selector  nodeid fduid =
    create_selector [P.prefix; nodeid;  "runtimes"; "*"; "fdu"; fduid; "instances"; "*"; "info"]

  let get_node_fdu_instance_selector nodeid instanceid =
    create_selector [P.prefix; nodeid;  "runtimes"; "*"; "fdu"; "*"; "instances"; instanceid; "info"]

  (* Mode Images *)

  let get_node_image_info_path nodeid pluginid imgid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "images"; imgid; "info"]

  let get_node_flavor_info_path nodeid pluginid flvid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "flavors"; flvid; "info"]


  (* Mode Networks *)

  let get_node_networks_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "network_managers"; pluginid; "networks"; "*"; "info"]

  (* Node Flavors *)

  let get_node_networks_find_selector nodeid netid =
    create_path [P.prefix; nodeid; "network_managers"; "*"; "networks"; netid; "info"]

  let get_node_network_info_path nodeid pluginid networkid =
    create_path [P.prefix; nodeid; "network_managers"; pluginid;"networks"; networkid; "info"]

  let get_node_network_port_info_path nodeid pluginid portid =
    create_path [P.prefix; nodeid; "network_managers"; pluginid; "ports"; portid; "info"]

  let get_node_network_ports_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "network_managers"; pluginid; "ports"; "*"; "info"]

  let get_node_network_router_info_path nodeid pluginid routerid =
    create_path [P.prefix; nodeid; "network_managers"; pluginid; "routers"; routerid; "info"]

  let get_node_network_routers_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "network_managers"; pluginid; "routers"; "*"; "info"]

  let get_node_network_floating_ip_info_path nodeid pluginid floatingid =
    create_path [P.prefix; nodeid; "network_managers"; pluginid; "floating-ips"; floatingid; "info"]

  let get_node_network_floating_ips_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "network_managers"; pluginid; "floating-ips"; "*"; "info"]

  (* Node Evals *)

  let get_node_os_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "os"; "exec"; func_name]

  let get_node_plugin_eval_path nodeid pluginid func_name =
    create_selector [P.prefix; nodeid; "plugins"; pluginid; "exec"; func_name ]

  let get_node_plugin_eval_path_with_params nodeid pluginid func_name (params: (string * string) list) =
    let rec assoc2args base index list =
      let len = List.length list in
      match index with
      | 0 ->
        let k,v = List.hd list in
        let b = base ^ "(" ^ k ^ "=" ^ v in
        assoc2args b (index+1) list
      | n when n < len ->
        let k,v = List.nth list index in
        let b  = base ^ ";" ^ k ^ "=" ^ v in
        assoc2args b (index+1) list
      | _-> base ^ ")"
    in  let  p = assoc2args "" 0 params in
    let f = func_name ^ "?" ^ p in
    create_selector [P.prefix; nodeid; "plugins"; pluginid; "exec"; f ]

  let get_agent_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "agent"; "exec"; func_name]

  (* NM Evals *)

  let get_node_nw_exec_eval_with_params nodeid nm_id func_name (params: (string * string) list) =
    let rec assoc2args base index list =
      let len = List.length list in
      match index with
      | 0 ->
        let k,v = List.hd list in
        let b = base ^ "(" ^ k ^ "=" ^ v in
        assoc2args b (index+1) list
      | n when n < len ->
        let k,v = List.nth list index in
        let b  = base ^ ";" ^ k ^ "=" ^ v in
        assoc2args b (index+1) list
      | _-> base ^ ")"
    in  let  p = assoc2args "" 0 params in
    let f = func_name ^ "?" ^ p in
    create_selector [P.prefix; nodeid; "network_managers"; nm_id; "exec"; f]

  let get_node_nw_exec_eval nodeid nm_id func_name =
    create_selector [P.prefix; nodeid; "network_managers"; nm_id; "exec"; func_name]


  (* ID Extraction *)

  let extract_nodeid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 2

  let extract_pluginid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_fduid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_fdu_instanceid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 8

  let extract_imageid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_flavorid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_netid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_portid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_floatingid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_routerid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6


  (* Node Evals *)

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
    let p = Yaks.Path.of_string @@  Yaks.Selector.path @@ get_node_plugin_eval_path nodeid pluginid func_name in
    let cb _ props =
      let%lwt r = func props in
      Lwt.return @@ Yaks.Value.StringValue r
    in
    let%lwt _ = Yaks.Workspace.register_eval p cb connector.ws in
    let ls = List.append connector.evals [p] in
    MVar.return Lwt.return_unit {connector with evals = ls}

  let exec_nm_eval nodeid nm_id func_name parametes connector =
    MVar.read connector >>= fun connector ->
    let s = match parametes with
      | [] -> get_node_nw_exec_eval  nodeid nm_id func_name
      | _ -> get_node_nw_exec_eval_with_params  nodeid nm_id func_name parametes
    in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (Agent_types.eval_result_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in exec_nm_eval") ))


  let exec_plugin_eval nodeid pluginid func_name parametes connector =
    MVar.read connector >>= fun connector ->
    let s = match parametes with
      | [] -> get_node_plugin_eval_path nodeid pluginid func_name
      | _ -> get_node_plugin_eval_path_with_params  nodeid pluginid func_name parametes
    in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (Agent_types.eval_result_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in exec_plugin_eval") ))

  (* Node *)

  let observe_node_plugins nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_plugins_subscriber_selector nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.plugin_of_string extract_pluginid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let observe_node_plugin nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path nodeid pluginid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.plugin_of_string extract_pluginid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_info nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_info_path nodeid  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.node_info_of_string extract_nodeid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let get_node_status nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_status_path nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] -> Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_node_status") )) *)
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FTypes.node_status_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_node_status") ))

  let observe_node_status nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_status_path nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.node_status_of_string extract_nodeid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let add_node_status nodeid nodestatus connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_status_path nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_status nodestatus )in
    Yaks.Workspace.put p value connector.ws

  let remove_node_status nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_status_path nodeid in
    Yaks.Workspace.remove p connector.ws

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
    | [] -> Lwt.return []
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plugin received empty data!!") )) *)
    | _ ->  Lwt_list.map_p (fun (k,_ )-> Lwt.return @@ extract_pluginid_from_path k) data

  let remove_node_plugin nodeid pluginid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_plugin_info_path nodeid pluginid in
    Yaks.Workspace.remove p connector.ws

  let add_node_info nodeid nodeinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path  nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_info nodeinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_info nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_info_path nodeid in
    Yaks.Workspace.remove p connector.ws

  let add_node_configuration nodeid nodeconf connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_configuration_path nodeid in
    let value = Yaks.Value.StringValue (FAgentTypes.string_of_configuration nodeconf )in
    Yaks.Workspace.put p value connector.ws

  let remove_node_configuration nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_configuration_path nodeid in
    Yaks.Workspace.remove p connector.ws


  (* Node FDUs *)

  let observe_node_runtime_fdu nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_runtime_fdus_selector nodeid pluginid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb_2ids callback Infra.Descriptors.FDU.record_of_string extract_fduid_from_path extract_fdu_instanceid_from_path)  s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_fdu nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_fdus_selector nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb_2ids callback Infra.Descriptors.FDU.record_of_string extract_fduid_from_path extract_fdu_instanceid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_fdu nodeid pluginid fduid instanceid fduinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid instanceid in
    let value = Yaks.Value.StringValue (Infra.Descriptors.FDU.string_of_record fduinfo) in
    Yaks.Workspace.put p value connector.ws

  let remove_node_fdu nodeid pluginid fduid instanceid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid instanceid in
    Yaks.Workspace.remove p connector.ws


  (* Node Networks *)

  let observe_node_network nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_networks_selector nodeid "*" in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypesRecord.virtual_network_of_string extract_netid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_network nodeid pluginid netid netinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_info_path nodeid pluginid netid in
    let value = Yaks.Value.StringValue (FTypesRecord.string_of_virtual_network netinfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_network nodeid pluginid netid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_network_info_path nodeid pluginid netid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] ->
      Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_node_network received empty data!!") )) *)
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@  Some (FTypesRecord.virtual_network_of_string (Yaks.Value.to_string v))

  let remove_node_network nodeid pluginid netid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_info_path nodeid pluginid netid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_port nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_ports_selector nodeid "*" in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.FDU.connection_point_record_of_string extract_portid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_port nodeid pluginid portid portinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_port_info_path nodeid pluginid portid in
    let value = Yaks.Value.StringValue (Infra.Descriptors.FDU.string_of_connection_point_record portinfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_port nodeid pluginid portid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_network_port_info_path nodeid pluginid portid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_node_port received empty data!!") )) *)
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@  Some (Infra.Descriptors.FDU.connection_point_record_of_string (Yaks.Value.to_string v))

  let remove_node_port nodeid pluginid portid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_port_info_path nodeid pluginid portid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_router nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_routers_selector nodeid "*" in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Router.record_of_string extract_portid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_router nodeid pluginid routerid routerinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_router_info_path nodeid pluginid routerid in
    let value = Yaks.Value.StringValue (Router.string_of_record routerinfo) in
    Yaks.Workspace.put p value connector.ws

  let get_node_router nodeid pluginid routerid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_network_router_info_path nodeid pluginid routerid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_node_port received empty data!!") )) *)
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@  Some (Router.record_of_string (Yaks.Value.to_string v))

  let remove_node_router nodeid pluginid routerid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_router_info_path nodeid pluginid routerid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_floating_ips nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_network_floating_ips_selector nodeid "*" in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.floating_ip_record_of_string extract_portid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_floating_ip nodeid pluginid floatingid ip_info connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_floating_ip_info_path nodeid pluginid floatingid in
    let value = Yaks.Value.StringValue (FTypes.string_of_floating_ip_record ip_info) in
    Yaks.Workspace.put p value connector.ws

  let get_node_floating_ip nodeid pluginid floatingid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_network_floating_ip_info_path nodeid pluginid floatingid in
    let%lwt data = Yaks.Workspace.get s connector.ws in
    match data with
    | [] -> Lwt.return None
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@  Some (FTypes.floating_ip_record_of_string (Yaks.Value.to_string v))

  let remove_node_floating_ip nodeid pluginid floatingid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_network_floating_ip_info_path nodeid pluginid floatingid in
    Yaks.Workspace.remove p connector.ws

end

module MakeCLAD(P: sig val prefix: string end) = struct

  (* Node *)
  let get_node_info_path nodeid =
    create_path [P.prefix; nodeid; "info"]

  let get_node_selector =
    create_selector [P.prefix; "*"; "info"]

  let get_node_configuration_path nodeid =
    create_path [P.prefix; nodeid; "configuration"]

  let get_node_status_path nodeid =
    create_path [P.prefix; nodeid; "status"]

  let get_node_plugins_selector nodeid =
    create_selector [P.prefix; nodeid; "plugins"; "*"; "info"]

  let get_node_plugins_subscriber_selector nodeid =
    create_selector [P.prefix; nodeid; "plugins"; "*"; "info"]

  let get_node_plugin_info_path nodeid pluginid=
    create_path [P.prefix; nodeid; "plugins"; pluginid; "info"]

  let get_node_runtimes_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"]

  (* Node FDUs *)

  let get_node_runtime_fdus_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  let get_node_fdus_selector nodeid =
    create_selector [P.prefix; nodeid; "runtimes"; "*"; "fdu"; "*"; "info"]

  let get_node_fdus_subscriber_selector nodeid pluginid =
    create_selector [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; "*"; "info"]

  let get_node_fdu_info_path nodeid pluginid fduid=
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "fdu"; fduid; "info"]


  (* Node Image *)

  let get_node_image_info_path nodeid pluginid imgid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "images"; imgid; "info"]

  (* Node Flavor *)

  let get_node_flavor_info_path nodeid pluginid flvid =
    create_path [P.prefix; nodeid; "runtimes"; pluginid; "flavors"; flvid; "info"]

  (* Node Evals *)

  let get_node_os_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "os"; "exec"; func_name]

  let get_agent_exec_path nodeid func_name =
    create_path [P.prefix; nodeid; "agent"; "exec"; func_name]

  let get_node_plugin_eval_path nodeid pluginid func_name =
    create_path [P.prefix; nodeid; "plugins"; pluginid; "exec"; func_name ]



  (* ID Extraction *)

  let extract_pluginid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 4

  let extract_nodeid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 2

  let extract_fduid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  (* Node Evak *)

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

  (* Nodes *)

  let observe_nodes callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_selector in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.node_info_of_string extract_nodeid_from_path) s connector.ws in
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

  let get_node_status nodeid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_status_path nodeid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("Empty value list on get_node_status") )) *)
    | _ ->
      let _,v = (List.hd res) in
      try
        Lwt.return @@ Some (FTypes.node_status_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _ ->
        Lwt.fail @@ FException (`InternalError (`Msg ("Value is not well formatted in get_node_status") ))

  let observe_node_status nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_status_path nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.node_status_of_string extract_nodeid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let add_node_status nodeid nodestatus connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_status_path nodeid in
    let value = Yaks.Value.StringValue (FTypes.string_of_node_status nodestatus )in
    Yaks.Workspace.put p value connector.ws

  let remove_node_status nodeid connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_status_path nodeid in
    Yaks.Workspace.remove p connector.ws

  let observe_node_plugins nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_plugins_subscriber_selector nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.plugin_of_string extract_pluginid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}


  let observe_node_plugin nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_plugin_info_path nodeid pluginid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.plugin_of_string extract_pluginid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_info nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_node_info_path nodeid  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback FTypes.node_info_of_string extract_pluginid_from_path) s connector.ws in
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
    | [] ->
      Lwt.return None
    (* Lwt.fail @@ FException (`InternalError (`Msg ("get_node_plugin received empty data!!") )) *)
    | _ ->
      let _,v = List.hd data in
      Lwt.return @@ Some (FTypes.plugin_of_string (Yaks.Value.to_string v))

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

  (* Node FDUs *)

  let observe_node_runtime_fdu nodeid pluginid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_runtime_fdus_selector nodeid pluginid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.FDU.record_of_string extract_fduid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_node_fdu nodeid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_node_fdus_selector nodeid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback Infra.Descriptors.FDU.record_of_string extract_fduid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_node_fdu nodeid pluginid fduid fduinfo connector =
    MVar.read connector >>= fun connector ->
    let p = get_node_fdu_info_path nodeid pluginid fduid in
    let value = Yaks.Value.StringValue (Infra.Descriptors.FDU.string_of_record fduinfo) in
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

