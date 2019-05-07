open Lwt.Infix
open Rest_types
open Mec_errors
open Mm5
open Fos_im

module MVar = Apero.MVar_lwt


module Mm5Map = Map.Make(String)

module MEAO = struct

  type state = {
    connector : Yaks_connector.connector;
    mm5_clients : Mm5_client.t Mm5Map.t
  }


  type t = state MVar.t

  let create loc =
    let%lwt con = Yaks_connector.get_connector_of_locator loc in
    Lwt.return @@ MVar.create ({connector = con; mm5_clients = Mm5Map.empty})


  (* Start and Stop *)
  let start self =
    ignore self;
    let f,_ =  Lwt.wait () in
    f >>= fun _ -> Lwt.return_unit


  let stop self =
    ignore self;
    Lwt.return_unit

  (* Utils *)


  let service_info_of_descriptor (svcd:MEC_Types.service_descriptor) serializer transpor_info transport_id =
    let ser_instance_id = Apero.Uuid.to_string @@ Apero.Uuid.make () in
    let version = svcd.version in
    let ser_name = svcd.ser_name in
    let ser_category =
      match svcd.ser_category with
      | Some cat ->
        Some (Rest_types.create_category_ref ~href:cat.href ~id:cat.id ~name:cat.name ~version:cat.version ())
      | None -> None
    in
    let state = `ACTIVE in
    let svc = Rest_types.create_service_info ~ser_instance_id ~version ~ser_name ~state ~serializer ~transport_id ~transpor_info () in
    {svc with ser_category = ser_category}

  let app_info_of_descriptor (appd:MEC_Types.appd_descriptor) =
    let appd_id = appd.id in
    let app_instance_id = Apero.Uuid.to_string @@ Apero.Uuid.make () in
    let vendor = appd.vendor in
    let soft_verision = appd.soft_version in
    let state = `ACTIVE  in
    let name = appd.name in
    let traffic_rules = List.map (fun t -> MEC_Types.string_of_traffic_rule_descriptor t |> Rest_types.traffic_rule_of_string |> fun r -> {r with state = `ACTIVE}) appd.traffic_rules in
    let dns_rules = List.map (fun d -> MEC_Types.string_of_dns_rule_descriptor d |> Rest_types.dns_rule_of_string |> fun r -> {r with state = `ACTIVE}) appd.dns_rules in
    Rest_types.create_app_info ~appd_id ~app_instance_id ~vendor ~soft_verision ~state ~name ~service_produced:[] ~traffic_rules ~dns_rules ()




  (* MEC Platforms *)

  let add_platform mec_plat self =
    MVar.guarded self @@ fun self ->
    let plid = mec_plat.platform_id in
    match Mm5Map.mem plid self.mm5_clients with
    | true ->
      Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s already exist" plid)))
    | false ->
      let addr = List.hd mec_plat.endpoint.addresses in
      let url = List.hd mec_plat.endpoint.uris in
      let%lwt client = Mm5_client.create addr.host addr.port url in
      Yaks_connector.Storage.Platform.add_platform plid mec_plat self.connector
      >>= fun _ -> MVar.return plid {self with mm5_clients = Mm5Map.add plid client self.mm5_clients}

  let get_platform plid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Platform.get_platform plid self.connector


  let get_platforms self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Platform.get_platforms self.connector


  let remove_platform plid self =
    MVar.guarded self @@ fun self ->
    Yaks_connector.Storage.Platform.remove_platform plid self.connector
    >>= fun _ -> MVar.return plid {self with mm5_clients = Mm5Map.remove plid self.mm5_clients}

  (* ME Svcs *)

  (* This should add the transports *)
  let add_service plid (ser_desc: service_info ) self =
    MVar.read self >>= fun self ->
    let serid = Apero.Option.get_or_default ser_desc.ser_instance_id (Apero.Uuid.to_string @@  Apero.Uuid.make ()) in
    let ser_desc = {ser_desc with ser_instance_id = Some serid} in
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.Services.add ser_desc client
      >>= fun _ -> Yaks_connector.Storage.ServiceInfo.add_service plid serid ser_desc self.connector
      >>= fun _ -> Lwt.return serid
    | None ->
      Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))


  let get_service_by_uuid plid ser_uuid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_service plid ser_uuid self.connector

  let get_services plid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_services plid self.connector

  let get_service_by_name plid ser_name self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_services plid self.connector in
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

  let get_service_by_category_id plid ser_cat_id self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_services plid self.connector in
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

  let remove_service plid ser_uuid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.ServiceInfo.get_service plid ser_uuid self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.Services.remove ser_uuid client
         >>= fun _ -> Yaks_connector.Storage.ServiceInfo.remove_service plid ser_uuid self.connector
         >>= fun _ ->  Lwt.return ser_uuid
       | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Service with id %s not exist" ser_uuid)))



  (* DNS Rules *)

  let get_dns_rules_for_application plid appid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.DNSRules.get_application_dns_rules plid appid self.connector

  let get_dns_rule_for_application plid appid dns_rule_id self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.DNSRules.get_application_dns_rule plid appid dns_rule_id self.connector

  let add_dns_rule_for_application plid appid dns_rule self =
    MVar.read self >>= fun self ->

    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.DnsRules.add appid dns_rule client
      >>= fun _ -> Yaks_connector.Storage.DNSRules.add_application_dns_rule plid appid dns_rule.dns_rule_id dns_rule self.connector
      >>= fun _-> Lwt.return dns_rule.dns_rule_id
    | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))



  let remove_dns_rule_for_application plid appid dns_rule_id self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.DNSRules.get_application_dns_rule plid appid dns_rule_id self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.DnsRules.remove appid dns_rule_id client
         >>= fun _ -> Yaks_connector.Storage.DNSRules.remove_application_dns_rule plid appid dns_rule_id self.connector
         >>= fun _ -> Lwt.return dns_rule_id
       | None ->  Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`DNSRuleNotExisting (`Msg (Printf.sprintf "DNS Rule with id %s not exist in application %s" dns_rule_id appid )))

  (* Traffic Rules *)

  let get_traffic_rules_for_application plid appid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.TrafficRules.get_application_traffic_rules plid appid self.connector

  let get_traffic_rule_for_application plid appid traffic_rule_id self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.TrafficRules.get_application_traffic_rule plid appid traffic_rule_id self.connector

  let add_traffic_rule_for_application plid appid traffic_rule self =
    MVar.read self >>= fun self ->
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.TrafficRules.add appid traffic_rule client
      >>= fun _ -> Yaks_connector.Storage.TrafficRules.add_application_traffic_rule plid appid traffic_rule.traffic_rule_id traffic_rule self.connector
      >>= fun _ -> Lwt.return traffic_rule.traffic_rule_id
    | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))

  let remove_traffic_rule_for_application plid appid traffic_rule_id self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.TrafficRules.get_application_traffic_rule appid plid traffic_rule_id self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.TrafficRules.remove appid traffic_rule_id client
         >>= fun _ -> Yaks_connector.Storage.TrafficRules.remove_application_traffic_rule plid appid traffic_rule_id self.connector
         >>= fun _ -> Lwt.return traffic_rule_id
       | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`TrafficRuleNotExising (`Msg (Printf.sprintf "Traffic Rule with id %s not exist in application %s" traffic_rule_id appid )))



  (* Transports *)


  let add_tranport plid (transport_desc:transport_info) self =
    MVar.read self >>= fun self ->
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.Transports.add transport_desc client
      >>= fun _ -> Yaks_connector.Storage.Transports.add_tranport plid transport_desc.id transport_desc self.connector
      >>= fun _ -> Lwt.return transport_desc.id
    |None ->
      Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))

  let get_transports plid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.Transports.get_transports plid self.connector

  let get_transport_by_id plid transportid self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yaks_connector.Storage.Transports.get_transports plid self.connector in
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

  let get_transport_by_name plid trans_name self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yaks_connector.Storage.Transports.get_transports plid self.connector in
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

  let get_transports_by_type plid trans_type self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yaks_connector.Storage.Transports.get_transports plid self.connector in
    Lwt_list.filter_map_p (fun (e:transport_info) ->
        if e.transport_type = trans_type then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) tranports

  let remove_transport plid transportid self =
    MVar.read self >>= fun self ->
    match%lwt (Yaks_connector.Storage.Transports.get_tranport plid transportid self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.Transports.remove transportid client
         >>= fun _ -> Yaks_connector.Storage.Transports.remove_transport plid transportid self.connector
         >>= fun _ -> Lwt.return transportid
       | None ->
         Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`TrafficRuleNotExising (`Msg (Printf.sprintf "Transport with id %s not exist" transportid)))



  (* Utils *)

  let rec filter_tx_dep (tx:Rest_types.transport_info) (rtxs:MEC_Types.transport_dependency list) =
    match rtxs with
    | [] -> false
    | hd::tl ->
      (match hd.transport.protocol = tx.protocol with
       | true -> true
       | false -> filter_tx_dep tx tl
      )

  let find_matching_transports plat_txs req_txs =
    (* let filter_protocol req_tx plat_tx  =
       plat_tx.protocol = req_tx.transport.protocol
       in *)
    (* let ffun = List.map (fun rtx -> filter_protocol rtx) req_txs in *)
    List.filter (
      fun ptx ->
        filter_tx_dep ptx req_txs
    ) plat_txs

  let rec filter_tx (tx:Rest_types.transport_info) (rtxs:MEC_Types.transport_descriptor list) =
    match rtxs with
    | [] -> false
    | hd::tl ->
      (match hd.protocol = tx.protocol with
       | true -> true
       | false -> filter_tx tx tl
      )


  (* ME App *)
  (* This add service, rules*)
  let add_application plid (app_desc: Fos_im.MEC_Types.appd_descriptor ) state =
    MVar.read state >>= fun self ->
    let appid = app_desc.id in
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->

      let app_info = app_info_of_descriptor app_desc in
      let app_inst_id = Apero.Option.get app_info.app_instance_id in
      let%lwt txs = get_transports plid state in
      let rtxs = app_desc.transport_dependencies in
      let mtxs = find_matching_transports txs rtxs in
      let svcs =
        List.map ( fun (s:MEC_Types.service_descriptor) ->
            let rtxs = List.map ( fun (t,_) -> t ) s.transport_supported  in
            let txs = List.filter (fun ptx -> filter_tx ptx rtxs ) mtxs in
            match txs with
            | [] -> raise @@ MEException (`TransportNotExisting (`Msg (Printf.sprintf "No required transport found")))
            | hd:: _ ->
              service_info_of_descriptor s `JSON hd hd.id
          ) app_desc.service_produces in
      let app_info = {app_info with service_produced = svcs} in
      Mm5_client.Applications.add app_info client
      >>= fun _ ->
      Yaks_connector.Storage.ServiceInfo.add_application plid appid app_info self.connector
      >>= fun  _ ->
      Lwt_list.iter_p (fun ser ->
          add_service plid ser state >>= fun _ -> Lwt.return_unit
        ) app_info.service_produced
      >>= fun _ ->
      Lwt_list.iter_p (fun t ->
          add_traffic_rule_for_application plid app_inst_id t state >>= fun _ -> Lwt.return_unit
        ) app_info.traffic_rules
      >>= fun _ ->
      Lwt_list.iter_p (fun d ->
          add_dns_rule_for_application plid app_inst_id d state >>= fun _ -> Lwt.return_unit
        ) app_info.dns_rules
      >>= fun _ ->
      Lwt.return app_inst_id
    | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))

  let get_application_by_uuid plid app_uuid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_application plid app_uuid self.connector

  let get_applications plid self =
    MVar.read self >>= fun self ->
    Yaks_connector.Storage.ServiceInfo.get_applications plid self.connector

  let get_application_by_name plid app_name self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_applications plid self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:Rest_types.app_info) ->
        if e.name = app_name then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) services
    in
    match services with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let get_application_by_vendor plid app_vendor self =
    MVar.read self >>= fun self ->
    let%lwt services = Yaks_connector.Storage.ServiceInfo.get_applications plid self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:Rest_types.app_info) ->
        if e.vendor = app_vendor then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) services
    in
    match services with
    | [] -> Lwt.return None
    | hd::_ -> Lwt.return @@ Some hd

  let remove_application plid app_uuid state =
    MVar.read state >>= fun self ->
    match%lwt (Yaks_connector.Storage.ServiceInfo.get_application plid app_uuid self.connector) with
    | Some appi ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.Applications.remove app_uuid client
         >>= fun  _ ->
         Lwt_list.iter_p (fun ser ->
             remove_service plid (Apero.Option.get ser.ser_instance_id) state >>= fun _ -> Lwt.return_unit
           ) appi.service_produced
         >>= fun _ ->
         Lwt_list.iter_p (fun t ->
             remove_traffic_rule_for_application plid app_uuid t.traffic_rule_id state >>= fun _ -> Lwt.return_unit
           ) appi.traffic_rules
         >>= fun _ ->
         Lwt_list.iter_p (fun d ->
             remove_dns_rule_for_application plid app_uuid d.dns_rule_id state >>= fun _ -> Lwt.return_unit
           ) appi.dns_rules
         >>= fun _ -> Yaks_connector.Storage.ServiceInfo.remove_application plid app_uuid self.connector
         >>= fun _ -> Lwt.return app_uuid
       | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`ApplicationNotExisting (`Msg (Printf.sprintf "Application with id %s not exist" app_uuid)))

end