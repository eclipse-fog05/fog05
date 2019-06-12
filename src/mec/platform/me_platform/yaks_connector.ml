open Yaks_ocaml
open Lwt.Infix
open Fos_im
open Fos_im.Errors


module MVar = Apero.MVar_lwt


let prefix = "/mec_platfrom"

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

let get_connector_of_locator loc =
  let%lwt yclient = Yaks.login loc Apero.Properties.empty in
  let%lwt admin = Yaks.admin yclient in
  let%lwt ws = Yaks.workspace (create_path [prefix; ""]) yclient in
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
  | [] -> Lwt.fail @@ MEException (`InternalError (`Msg ("Listener received empty data!!") ))
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
  | [] -> Lwt.fail @@ MEException (`InternalError (`Msg ("Listener received empty data!!") ))
  | _ ->
    let p,c = List.hd data in
    ( match c with
      | Put tv | Update tv ->
        let v = tv.value in
        callback (Some (of_string (Yaks.Value.to_string v))) false None None
      | Remove _ ->
        callback None true (Some (extract_uuid1 p)) (Some (extract_uuid2 p))
    )

let sub_cb_3ids callback of_string extract_uuid1 extract_uuid2 extract_uuid3 (data:(Yaks.Path.t * Yaks.change) list)  =
  match data with
  | [] -> Lwt.fail @@ MEException (`InternalError (`Msg ("Listener received empty data!!") ))
  | _ ->
    let p,c = List.hd data in
    ( match c with
      | Put tv | Update tv ->
        let v = tv.value in
        callback (Some (of_string (Yaks.Value.to_string v))) false None None None
      | Remove _ ->
        callback None true (Some (extract_uuid1 p)) (Some (extract_uuid2 p)) (Some (extract_uuid3 p))
    )

module MakeServiceRegistry(P: sig val prefix: string end) = struct

  (* Following same Mp1 URI structure of APIs
   * Only For services and applications
  *)

  let get_application_path appid =
    create_path [P.prefix; "applications"; appid]

  let get_applications_selector =
    create_selector [P.prefix; "applications"; "*"]

  let get_service_path serviceid =
    create_path [P.prefix; "services"; serviceid]

  let get_services_selector  =
    create_selector [P.prefix; "services"; "*"]

  let extract_serviceid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 3

  let extract_appid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 3

  let get_application appid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_path appid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | hd::_ ->
      let _,v = hd in
      try
        Lwt.return @@ Some (MEC_Interfaces.app_info_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let get_applications connector =
    MVar.read connector >>= fun connector ->
    let s = get_applications_selector in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (_,v) -> Lwt.return @@ MEC_Interfaces.app_info_of_string (Yaks.Value.to_string v)) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_applications") ))
      | exn -> Lwt.fail exn

  let observe_applications callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_applications_selector in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.app_info_of_string extract_appid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_application applicationid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_path applicationid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.app_info_of_string extract_appid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_application applicationid appd connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_path applicationid in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_app_info appd) in
    Yaks.Workspace.put p value connector.ws

  let remove_application applicationid connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_path applicationid in
    Yaks.Workspace.remove p connector.ws

  let get_service serviceid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_service_path serviceid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | hd::_ ->
      let _,v = hd in
      try
        Lwt.return @@ Some (MEC_Interfaces.service_info_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let get_services connector =
    MVar.read connector >>= fun connector ->
    let s = get_services_selector in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (_,v) -> Lwt.return @@ MEC_Interfaces.service_info_of_string (Yaks.Value.to_string v)) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_applications") ))
      | exn -> Lwt.fail exn

  let observe_services callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_services_selector in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.service_info_of_string extract_serviceid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_service serviceid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_service_path serviceid in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.service_info_of_string extract_serviceid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_service serviceid serd connector =
    MVar.read connector >>= fun connector ->
    let p = get_service_path serviceid in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_service_info serd) in
    Yaks.Workspace.put p value connector.ws

  let remove_service serviceid connector =
    MVar.read connector >>= fun connector ->
    let p = get_service_path serviceid in
    Yaks.Workspace.remove p connector.ws


end


module MakeDNSRules(P: sig val prefix: string end) = struct

  (* Following same Mp1 URI structure of APIs
   * Only For DNS Rules
  *)

  let get_application_dns_rule_path appid dns_rule_id =
    create_path [P.prefix; "applications"; appid; "dns_rules"; dns_rule_id]

  let get_applications_dns_rules_selector appid =
    create_selector [P.prefix; "applications"; appid; "dns_rules"; "*"]

  let extract_appid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 3

  let extract_dns_rule_id_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 5

  let get_application_dns_rule appid dns_rule_id connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_dns_rule_path appid  dns_rule_id in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (MEC_Interfaces.dns_rule_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let get_application_dns_rules appid connector =
    MVar.read connector >>= fun connector ->
    let s = get_applications_dns_rules_selector appid  in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (_,v) -> Lwt.return (MEC_Interfaces.dns_rule_of_string (Yaks.Value.to_string v))) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let observe_application_dns_rules appid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_applications_dns_rules_selector appid  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.dns_rule_of_string extract_dns_rule_id_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_application_dns_rule applicationid dns_rule_id callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_dns_rule_path applicationid dns_rule_id in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.dns_rule_of_string extract_dns_rule_id_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_application_dns_rule applicationid dns_rule_id dns_rule connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_dns_rule_path applicationid dns_rule_id in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_dns_rule dns_rule) in
    Yaks.Workspace.put p value connector.ws

  let remove_application_dns_rule applicationid dns_rule_id connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_dns_rule_path applicationid dns_rule_id in
    Yaks.Workspace.remove p connector.ws
end

module MakeTrafficRules(P: sig val prefix: string end) = struct

  (* Following same Mp1 URI structure of APIs
   * Only For Traffic Rules
  *)

  let get_application_traffic_rule_path appid traffic_rule_id =
    create_path [P.prefix; "applications"; appid; "traffic_rules"; traffic_rule_id]

  let get_applications_traffic_rules_selector appid =
    create_selector [P.prefix; "applications"; appid; "traffic_rules"; "*"]

  let extract_appid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 3

  let extract_traffic_rule_id_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 5

  let get_application_traffic_rule appid traffic_rule_id connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_traffic_rule_path appid  traffic_rule_id in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (MEC_Interfaces.traffic_rule_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let get_application_traffic_rules appid connector =
    MVar.read connector >>= fun connector ->
    let s = get_applications_traffic_rules_selector appid  in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (_,v) -> Lwt.return (MEC_Interfaces.traffic_rule_of_string (Yaks.Value.to_string v))) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let observe_application_traffic_rules appid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_applications_traffic_rules_selector appid  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.traffic_rule_of_string extract_traffic_rule_id_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let observe_application_traffic_rule applicationid traffic_rule_id callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_traffic_rule_path applicationid traffic_rule_id in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.traffic_rule_of_string extract_traffic_rule_id_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_application_traffic_rule applicationid traffic_rule_id traffic_rule connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_traffic_rule_path applicationid traffic_rule_id in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_traffic_rule traffic_rule) in
    Yaks.Workspace.put p value connector.ws

  let remove_application_traffic_rule applicationid traffic_rule_id connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_traffic_rule_path applicationid traffic_rule_id in
    Yaks.Workspace.remove p connector.ws
end


module MakeSubscriptions (P: sig val prefix: string end) = struct

  (* Following same Mp1 URI structure of APIs
   * Only For Traffic Rules
  *)

  let get_application_termination_subscription_path appid subscriptionid =
    create_path [P.prefix; "applications"; appid; "subscriptions"; "AppTerminationNotificationSubscription"; subscriptionid]

  let get_applications_termination_subscription_selector appid =
    create_selector [P.prefix; "applications"; appid; "subscriptions"; "AppTerminationNotificationSubscription"; "*"]

  let get_service_availaility_subscription_path appid subscriptionid =
    create_path [P.prefix; "applications"; appid; "subscriptions"; "SerAvailabilityNotificationSubscription"; subscriptionid]

  let get_service_availaility_subscription_selector appid =
    create_selector [P.prefix; "applications"; appid; "subscriptions"; "SerAvailabilityNotificationSubscription"; "*"]

  let get_application_subscriptions_selector appid =
    create_path [P.prefix; "applications"; appid; "subscriptions"; "**"]

  let extract_appid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 6

  let extract_sub_type_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 5

  let extract_subscriptionid_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 3

  let get_application_termination_subscription appid subscriptionid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_application_termination_subscription_path appid  subscriptionid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (MEC_Interfaces.app_termination_notification_subscription_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let get_application_termination_subscriptions appid connector =
    MVar.read connector >>= fun connector ->
    let s = get_applications_termination_subscription_selector appid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (k,v) -> Lwt.return (extract_subscriptionid_from_path k, (MEC_Interfaces.app_termination_notification_subscription_of_string (Yaks.Value.to_string v)))) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_transports") ))
      | exn -> Lwt.fail exn

  let observe_application_termination_subscriptions appid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_applications_termination_subscription_selector appid  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.app_termination_notification_of_string extract_subscriptionid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_application_termination_subscription applicationid subscriptionid sub connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_termination_subscription_path applicationid subscriptionid in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_app_termination_notification_subscription sub) in
    Yaks.Workspace.put p value connector.ws

  let remove_application_termination_subscription applicationid subscriptionid connector =
    MVar.read connector >>= fun connector ->
    let p = get_application_termination_subscription_path applicationid subscriptionid in
    Yaks.Workspace.remove p connector.ws

  let get_service_availability_subscription appid subscriptionid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_service_availaility_subscription_path appid  subscriptionid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (MEC_Interfaces.ser_availability_notification_subscription_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_application") ))
      | exn -> Lwt.fail exn

  let get_service_availability_subscriptions appid connector =
    MVar.read connector >>= fun connector ->
    let s = get_service_availaility_subscription_selector appid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (k,v) -> Lwt.return (extract_subscriptionid_from_path k, (MEC_Interfaces.ser_availability_notification_subscription_of_string (Yaks.Value.to_string v)))) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_transports") ))
      | exn -> Lwt.fail exn

  let observe_service_availability_subscriptions appid callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_service_availaility_subscription_selector appid  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.ser_availability_notification_subscription_of_string extract_subscriptionid_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let add_service_availability_subscription applicationid subscriptionid sub connector =
    MVar.read connector >>= fun connector ->
    let p = get_service_availaility_subscription_path applicationid subscriptionid in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_ser_availability_notification_subscription sub) in
    Yaks.Workspace.put p value connector.ws

  let remove_service_availability_subscription applicationid subscriptionid connector =
    MVar.read connector >>= fun connector ->
    let p = get_service_availaility_subscription_path applicationid subscriptionid in
    Yaks.Workspace.remove p connector.ws

end

module MakeTransports (P: sig val prefix: string end) = struct

  (* Following same Mp1 URI structure of APIs
   * Only For Traffic Rules
  *)

  let get_transport_path transportid =
    create_path [P.prefix; "transport"; transportid]

  let get_transport_selector =
    create_selector [P.prefix; "transport"; "*"]

  let extract_transport_id_from_path path =
    let ps = Yaks.Path.to_string path in
    List.nth (String.split_on_char '/' ps) 3

  let add_tranport transportid transport_desc connector =
    MVar.read connector >>= fun connector ->
    let p = get_transport_path transportid in
    let value = Yaks.Value.StringValue (MEC_Interfaces.string_of_transport_info transport_desc) in
    Yaks.Workspace.put p value connector.ws

  let get_tranport transportid connector =
    MVar.read connector >>= fun connector ->
    let s = Yaks.Selector.of_path @@ get_transport_path  transportid in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return None
    | (_,v)::_ ->
      try
        Lwt.return @@ Some (MEC_Interfaces.transport_info_of_string (Yaks.Value.to_string v))
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg (Printf.sprintf "Value is not well formatted in transportid: %s" (Yaks.Value.to_string v)) ))
      | exn -> Lwt.fail exn


  let get_transports connector =
    MVar.read connector >>= fun connector ->
    let s = get_transport_selector in
    Yaks.Workspace.get s connector.ws
    >>= fun res ->
    match res with
    | [] ->
      Lwt.return []
    | _ ->
      try
        Lwt_list.map_p (fun (_,v) -> Lwt.return (MEC_Interfaces.transport_info_of_string (Yaks.Value.to_string v))) res
      with
      | Atdgen_runtime.Oj_run.Error _ | Yojson.Json_error _  ->
        Lwt.fail @@ MEException (`InternalError (`Msg ("Value is not well formatted in get_transports") ))
      | exn -> Lwt.fail exn

  let observe_transports callback connector =
    MVar.guarded connector @@ fun connector ->
    let s = get_transport_selector  in
    let%lwt subid = Yaks.Workspace.subscribe ~listener:(sub_cb callback MEC_Interfaces.transport_info_of_string extract_transport_id_from_path) s connector.ws in
    let ls = List.append connector.listeners [subid] in
    MVar.return subid {connector with listeners = ls}

  let remove_transport transportid connector =
    MVar.read connector >>= fun connector ->
    let p = get_transport_path transportid in
    Yaks.Workspace.remove p connector.ws

end


module Storage = struct

  module ServiceInfo = MakeServiceRegistry(struct let prefix = prefix end)
  module DNSRules = MakeDNSRules(struct let prefix = prefix end)
  module TrafficRules = MakeTrafficRules(struct let prefix = prefix end)
  module Subscriptions = MakeSubscriptions(struct let prefix = prefix end)
  module Transports = MakeTransports(struct let prefix = prefix end)

end
