open Lwt.Infix
open Rest_types
open Mec_errors
open Mm5

module MVar = Apero.MVar_lwt

module MEAO = struct

  type state = {
    connector : Yaks_connector.connector;
    mm5_client : Mm5_client.t
  }


  type t = state MVar.t

  let create loc mm5_client =
    let%lwt con = Yaks_connector.get_connector_of_locator loc in
    Lwt.return @@ MVar.create ({connector = con; mm5_client})

  (* MEC Platforms *)

  let add_platform mec_plat self =
    MVar.read self >>= fun self ->
    let plid = mec_plat.platform_id in
    Yaks_connector.Storage.Platform.add_platform plid mec_plat self.connector
    >>= fun _ -> Lwt.return plid

  let get_platform plid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Platform.get_platform plid self.connector


  let get_platforms self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Platform.get_platforms self.connector


  let remove_platform plid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Platform.remove_platform plid self.connector
    >>= fun _ -> Lwt.return plid

  (* ME Apps and Svcs *)

  (* This should add the transports *)
  let add_service (ser_desc: service_info ) self =
    MVar.read self >>= fun self ->
    let serid = Apero.Option.get_or_default ser_desc.ser_instance_id (Apero.Uuid.to_string @@  Apero.Uuid.make ()) in
    let ser_desc = {ser_desc with ser_instance_id = Some serid} in
    Yaks_connector.Storage.ServiceInfo.add_service serid ser_desc self.connector
    >>= fun  _ -> Lwt.return serid

  let get_service_by_uuid ser_uuid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_service ser_uuid self.connector

  let get_services self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_services self.connector

  let get_service_by_name ser_name self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_services self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun e ->
        if e.ser_name = ser_name then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) services
    in
    match services with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let get_service_by_category_id ser_cat_id self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_services self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun e ->
        match e.ser_category with
        | Some sc ->
          if sc.id = ser_cat_id then
            Lwt.return @@ Some e
          else
            Lwt.return None
        | None -> Lwt.return None
      ) services
    in
    match services with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let remove_service ser_uuid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.ServiceInfo.get_service ser_uuid self.connector) with
    | Some _ ->
      Yaks_connector.Storage.ServiceInfo.remove_service ser_uuid self.connector
      >>= fun _ -> Lwt.return ser_uuid
    | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Service with id %s not exist" ser_uuid)))


  (* This should add the traffic rules and dns rules *)
  let add_application (app_desc: Fos_im.MEC_Types.appd_descriptor ) self =
    MVar.read self >>= fun self ->
    let appid = app_desc.id in
    Yaks_connector.Storage.ServiceInfo.add_application appid app_desc self.connector
    >>= fun  _ -> Lwt.return appid

  let get_application_by_uuid app_uuid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_application app_uuid self.connector

  let get_applications self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_applications self.connector

  let get_application_by_name app_name self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_applications self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:Fos_im.MEC_Types.appd_descriptor) ->
        if e.name = app_name then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) services
    in
    match services with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let get_application_by_vendor app_vendor self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_applications self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:Fos_im.MEC_Types.appd_descriptor) ->
        if e.vendor = app_vendor then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) services
    in
    match services with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let remove_application app_uuid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.ServiceInfo.get_application app_uuid self.connector) with
    | Some _ ->
      Yaks_connector.Storage.ServiceInfo.remove_application app_uuid self.connector
      >>= fun _ -> Lwt.return app_uuid
    | None -> Lwt.fail @@ MEException (`ApplicationNotExisting (`Msg (Printf.sprintf "Application with id %s not exist" app_uuid)))


  (* DNS Rules *)

  let get_dns_rules_for_application appid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.DNSRules.get_application_dns_rules appid self.connector

  let get_dns_rule_for_application appid dns_rule_id self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.DNSRules.get_application_dns_rule appid dns_rule_id self.connector

  let add_dns_rule_for_application appid dns_rule self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.DNSRules.add_application_dns_rule appid dns_rule.dns_rule_id dns_rule self.connector
    (* >>= fun _ ->
       DynDNS.add_dns_rule self.dns_client dns_rule.ip_address dns_rule.domain_name *)
    >>= fun _->
    Lwt.return dns_rule.dns_rule_id

  let remove_dns_rule_for_application appid dns_rule_id self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.DNSRules.get_application_dns_rule appid dns_rule_id self.connector) with
    | Some _ ->
      (* DynDNS.remove_dns_rule self.dns_client rule.ip_address rule.domain_name
         >>= fun _ -> *)
      Yaks_connector.Storage.DNSRules.remove_application_dns_rule appid dns_rule_id self.connector
      >>= fun _ -> Lwt.return dns_rule_id
    | None -> Lwt.fail @@ MEException (`DNSRuleNotExisting (`Msg (Printf.sprintf "DNS Rule with id %s not exist in application %s" dns_rule_id appid )))

  (* Traffic Rules *)

  let get_traffic_rules_for_application appid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.TrafficRules.get_application_traffic_rules appid self.connector

  let get_traffic_rule_for_application appid traffic_rule_id self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.TrafficRules.get_application_traffic_rule appid traffic_rule_id self.connector

  let add_traffic_rule_for_application appid traffic_rule self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.TrafficRules.add_application_traffic_rule appid traffic_rule.traffic_rule_id traffic_rule self.connector
    >>= fun _ -> Lwt.return traffic_rule.traffic_rule_id

  let remove_traffic_rule_for_application appid traffic_rule_id self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.TrafficRules.get_application_traffic_rule appid traffic_rule_id self.connector) with
    | Some _ ->
      Yaks_connector.Storage.TrafficRules.remove_application_traffic_rule appid traffic_rule_id self.connector
      >>= fun _ -> Lwt.return traffic_rule_id
    | None -> Lwt.fail @@ MEException (`TrafficRuleNotExising (`Msg (Printf.sprintf "Traffic Rule with id %s not exist in application %s" traffic_rule_id appid )))


  (* Timings *)

  let get_current_time self =
    ignore self;
    (* WIll get time using system time just for PoC *)
    let time = Rest_types.{seconds = 0; nanoseconds = 0; time_source_status= `NONTRACEABLE } in
    Lwt.return time

  let get_timing_caps self =
    ignore self;
    (* PlaceHolder Value *)
    let ts = {seconds = 0; nanoseconds = 0} in
    let tc = {timestamp = Some ts; ntp_servers = []; ptp_masters = []} in
    Lwt.return tc

  (* Transports *)


  let add_tranport (transport_desc:transport_info) self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Transports.add_tranport transport_desc.id transport_desc self.connector
    >>= fun _ -> Lwt.return transport_desc.id

  let get_transports self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Transports.get_transports self.connector

  let get_transport_by_id transportid self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yaks_connector.Storage.Transports.get_transports self.connector in
    let%lwt tranports = Lwt_list.filter_map_p (fun (e:transport_info) ->
        if e.id = transportid then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) tranports
    in
    match tranports with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let get_transport_by_name trans_name self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yaks_connector.Storage.Transports.get_transports self.connector in
    let%lwt tranports = Lwt_list.filter_map_p (fun (e:transport_info) ->
        if e.name = trans_name then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) tranports
    in
    match tranports with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let get_transports_by_type trans_type self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yaks_connector.Storage.Transports.get_transports self.connector in
    Lwt_list.filter_map_p (fun (e:transport_info) ->
        if e.transport_type = trans_type then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) tranports

  let remove_transport transportid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.Transports.get_tranport transportid self.connector) with
    | Some _ ->
      Yaks_connector.Storage.Transports.remove_transport transportid self.connector
      >>= fun _ -> Lwt.return transportid
    | None -> Lwt.fail @@ MEException (`TrafficRuleNotExising (`Msg (Printf.sprintf "Transport with id %s not exist" transportid)))



  (* Subscriptions *)

  let get_application_subscriptions appid self =
    MVar.read self >>= fun self ->
    let%lwt term_subs = Yaks_connector.Storage.Subscriptions.get_application_termination_subscriptions appid self.connector in
    let%lwt avai_subs = Yaks_connector.Storage.Subscriptions.get_service_availability_subscriptions appid self.connector in
    Lwt.return (term_subs, avai_subs)

  let add_application_termination_subscription appid sub self =
    MVar.read self >>= fun self ->
    let subid = (Apero.Uuid.to_string @@  Apero.Uuid.make ()) in
    (* Should verify if this uuid does not exist ? *)
    Yaks_connector.Storage.Subscriptions.add_application_termination_subscription appid subid sub self.connector
    >>= fun _ -> Lwt.return subid


  let get_application_termination_subscription appid subid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Subscriptions.get_application_termination_subscription appid subid self.connector

  let remove_application_termination_subscription appid subid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.Subscriptions.get_application_termination_subscription appid subid self.connector) with
    | Some _ ->
      Yaks_connector.Storage.Subscriptions.remove_application_termination_subscription appid subid self.connector
      >>= fun _ -> Lwt.return subid
    | None -> Lwt.fail @@ MEException (`SubscriptionNotExisting (`Msg (Printf.sprintf "Subscription with id %s not exist in application %s" subid appid)))

  let add_service_availability_subscription appid sub self =
    MVar.read self >>= fun self ->
    let subid = (Apero.Uuid.to_string @@  Apero.Uuid.make ()) in
    (* Should verify if this uuid does not exist ? *)
    Yaks_connector.Storage.Subscriptions.add_service_availability_subscription appid subid sub self.connector
    >>= fun _ -> Lwt.return subid

  let get_service_availability_subscription appid subid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Subscriptions.get_service_availability_subscription appid subid self.connector

  let remove_service_availability_subscription appid subid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.Subscriptions.get_service_availability_subscription appid subid self.connector) with
    | Some _ ->
      Yaks_connector.Storage.Subscriptions.remove_service_availability_subscription appid subid self.connector
      >>= fun _ -> Lwt.return subid
    | None -> Lwt.fail @@ MEException (`SubscriptionNotExisting (`Msg (Printf.sprintf "Subscription with id %s not exist in application %s" subid appid)))



  (* Start and Stop *)
  let start self =
    ignore self;
    let f,_ =  Lwt.wait () in
    f >>= fun _ -> Lwt.return_unit


  let stop self =
    ignore self;
    Lwt.return_unit



end