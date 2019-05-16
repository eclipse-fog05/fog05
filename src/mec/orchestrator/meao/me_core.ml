open Lwt.Infix
open Fos_im
open Fos_im.Errors
open Mm5


module MVar = Apero.MVar_lwt


module Mm5Map = Map.Make(String)
module FIMMap = Map.Make(String)


module MEAO = struct

  type state = {
    connector : Yconnector.connector;
    mm5_clients : Mm5_client.t Mm5Map.t;
    fim_conns : (module FIM.FIMConn) FIMMap.t
  }


  type t = state MVar.t

  let create loc =
    let%lwt con = Yconnector.get_connector_of_locator loc in
    Lwt.return @@ MVar.create ({connector = con; mm5_clients = Mm5Map.empty; fim_conns= FIMMap.empty})


  (* Start and Stop *)
  let start self =
    ignore self;
    let f,_ =  Lwt.wait () in
    f >>= fun _ -> Lwt.return_unit


  let stop self =
    ignore self;
    Lwt.return_unit

  (* Utils *)


  let service_info_of_descriptor (svcd:MEC.service_descriptor) serializer transpor_info transport_id =
    let ser_instance_id = Apero.Uuid.to_string @@ Apero.Uuid.make () in
    let version = svcd.version in
    let ser_name = svcd.ser_name in
    let ser_category =
      match svcd.ser_category with
      | Some cat ->
        Some (MEC_Interfaces.create_category_ref ~href:cat.href ~id:cat.id ~name:cat.name ~version:cat.version ())
      | None -> None
    in
    let state = `ACTIVE in
    let svc = MEC_Interfaces.create_service_info ~ser_instance_id ~version ~ser_name ~state ~serializer ~transport_id ~transpor_info () in
    {svc with ser_category = ser_category}

  let app_info_of_descriptor (appd:MEC.appd_descriptor) =
    let appd_id = appd.id in
    let app_instance_id = Apero.Uuid.to_string @@ Apero.Uuid.make () in
    let vendor = appd.vendor in
    let soft_verision = appd.soft_version in
    let state = `ACTIVE  in
    let name = appd.name in
    let traffic_rules = List.map (fun t -> MEC.string_of_traffic_rule_descriptor t |> MEC_Interfaces.traffic_rule_of_string |> fun r -> {r with state = `ACTIVE}) appd.traffic_rules in
    let dns_rules = List.map (fun d -> MEC.string_of_dns_rule_descriptor d |> MEC_Interfaces.dns_rule_of_string |> fun r -> {r with state = `ACTIVE}) appd.dns_rules in
    MEC_Interfaces.create_app_info ~appd_id ~app_instance_id ~vendor ~soft_verision ~state ~name ~service_produced:[] ~traffic_rules ~dns_rules ()

  let transport_info_of_descriptor (txd:MEC.transport_descriptor) =
    let id = Apero.Uuid.to_string @@ Apero.Uuid.make () in
    let transport_type = MEC_Interfaces.transport_types_of_string (MEC.string_of_transport_types txd.transport_type) in
    let version = txd.version in
    let security =  MEC_Interfaces.security_info_of_string (MEC.string_of_security_info txd.security) in
    let protocol = txd.protocol in
    let name = id ^ protocol in
    let endpoint =  MEC_Interfaces.{uris=[]; alternative = Fos_im.JSON.create_empty (); addresses =[] } in
    MEC_Interfaces.create_transport_info ~id ~transport_type ~version ~security ~protocol ~name ~endpoint ()


  (* MEC Platforms *)

  let add_platform (mec_plat: MEC_Interfaces.platform) self =
    MVar.guarded self @@ fun self ->
    let plid = mec_plat.platform_id in
    match Mm5Map.mem plid self.mm5_clients with
    | true ->
      Lwt.fail @@ MEException (`DuplicatedResource (`Msg (Printf.sprintf "Platform with id %s already exist" plid)))
    | false ->
      let addr = List.hd mec_plat.endpoint.addresses in
      let url = List.hd mec_plat.endpoint.uris in
      let%lwt client = Mm5_client.create addr.host addr.port url in
      Yconnector.Storage.Platform.add_platform plid mec_plat self.connector
      >>= fun _ -> MVar.return plid {self with mm5_clients = Mm5Map.add plid client self.mm5_clients}

  let get_platform plid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.Platform.get_platform plid self.connector


  let get_platforms self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.Platform.get_platforms self.connector


  let remove_platform plid self =
    MVar.guarded self @@ fun self ->
    Yconnector.Storage.Platform.remove_platform plid self.connector
    >>= fun _ -> MVar.return plid {self with mm5_clients = Mm5Map.remove plid self.mm5_clients}

  (* ME Svcs *)

  (* This should add the transports *)
  let add_service plid (ser_desc:  MEC_Interfaces.service_info ) self =
    MVar.read self >>= fun self ->
    let serid = Apero.Option.get_or_default ser_desc.ser_instance_id (Apero.Uuid.to_string @@  Apero.Uuid.make ()) in
    let ser_desc = {ser_desc with ser_instance_id = Some serid} in
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.Services.add ser_desc client
      >>= fun _ -> Yconnector.Storage.ServiceInfo.add_service plid serid ser_desc self.connector
      >>= fun _ -> Lwt.return serid
    | None ->
      Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))


  let get_service_by_uuid plid ser_uuid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.ServiceInfo.get_service plid ser_uuid self.connector

  let get_services plid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.ServiceInfo.get_services plid self.connector

  let get_service_by_name plid ser_name self =
    MVar.read self >>= fun self ->
    let%lwt services = Yconnector.Storage.ServiceInfo.get_services plid self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:MEC_Interfaces.service_info) ->
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
    let%lwt services = Yconnector.Storage.ServiceInfo.get_services plid self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:MEC_Interfaces.service_info) ->
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
    match%lwt (Yconnector.Storage.ServiceInfo.get_service plid ser_uuid self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.Services.remove ser_uuid client
         >>= fun _ -> Yconnector.Storage.ServiceInfo.remove_service plid ser_uuid self.connector
         >>= fun _ ->  Lwt.return ser_uuid
       | None -> Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`ServiceNotExisting (`Msg (Printf.sprintf "Service with id %s not exist" ser_uuid)))



  (* DNS Rules *)

  let get_dns_rules_for_application plid appid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.DNSRules.get_application_dns_rules plid appid self.connector

  let get_dns_rule_for_application plid appid dns_rule_id self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.DNSRules.get_application_dns_rule plid appid dns_rule_id self.connector

  let add_dns_rule_for_application plid appid dns_rule self =
    MVar.read self >>= fun self ->

    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.DnsRules.add appid dns_rule client
      >>= fun _ -> Yconnector.Storage.DNSRules.add_application_dns_rule plid appid dns_rule.dns_rule_id dns_rule self.connector
      >>= fun _-> Lwt.return dns_rule.dns_rule_id
    | None -> Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))



  let remove_dns_rule_for_application plid appid dns_rule_id self =
    MVar.read self >>= fun self ->
    match%lwt (Yconnector.Storage.DNSRules.get_application_dns_rule plid appid dns_rule_id self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.DnsRules.remove appid dns_rule_id client
         >>= fun _ -> Yconnector.Storage.DNSRules.remove_application_dns_rule plid appid dns_rule_id self.connector
         >>= fun _ -> Lwt.return dns_rule_id
       | None ->  Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`DNSRuleNotExisting (`Msg (Printf.sprintf "DNS Rule with id %s not exist in application %s" dns_rule_id appid )))

  (* Traffic Rules *)

  let get_traffic_rules_for_application plid appid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.TrafficRules.get_application_traffic_rules plid appid self.connector

  let get_traffic_rule_for_application plid appid traffic_rule_id self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.TrafficRules.get_application_traffic_rule plid appid traffic_rule_id self.connector

  let add_traffic_rule_for_application plid appid traffic_rule self =
    MVar.read self >>= fun self ->
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.TrafficRules.add appid traffic_rule client
      >>= fun _ -> Yconnector.Storage.TrafficRules.add_application_traffic_rule plid appid traffic_rule.traffic_rule_id traffic_rule self.connector
      >>= fun _ -> Lwt.return traffic_rule.traffic_rule_id
    | None -> Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))

  let remove_traffic_rule_for_application plid appid traffic_rule_id self =
    MVar.read self >>= fun self ->
    match%lwt (Yconnector.Storage.TrafficRules.get_application_traffic_rule plid appid  traffic_rule_id self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.TrafficRules.remove appid traffic_rule_id client
         >>= fun _ -> Yconnector.Storage.TrafficRules.remove_application_traffic_rule plid appid traffic_rule_id self.connector
         >>= fun _ -> Lwt.return traffic_rule_id
       | None -> Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`TrafficRuleNotExising (`Msg (Printf.sprintf "Traffic Rule with id %s not exist in application %s" traffic_rule_id appid )))



  (* Transports *)


  let add_tranport plid (transport_desc: MEC_Interfaces.transport_info) self =
    MVar.read self >>= fun self ->
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->
      Mm5_client.Transports.add transport_desc client
      >>= fun _ -> Yconnector.Storage.Transports.add_tranport plid transport_desc.id transport_desc self.connector
      >>= fun _ -> Lwt.return transport_desc.id
    |None ->
      Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))

  let get_transports plid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.Transports.get_transports plid self.connector

  let get_transport_by_id plid transportid self =
    MVar.read self >>= fun self ->
    let%lwt tranports = Yconnector.Storage.Transports.get_transports plid self.connector in
    let%lwt tranports = Lwt_list.filter_map_p (fun (e: MEC_Interfaces.transport_info) ->
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
    let%lwt tranports = Yconnector.Storage.Transports.get_transports plid self.connector in
    let%lwt tranports = Lwt_list.filter_map_p (fun (e: MEC_Interfaces.transport_info) ->
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
    let%lwt tranports = Yconnector.Storage.Transports.get_transports plid self.connector in
    Lwt_list.filter_map_p (fun (e:MEC_Interfaces.transport_info) ->
        if e.transport_type = trans_type then
          Lwt.return @@ Some e
        else
          Lwt.return None
      ) tranports

  let remove_transport plid transportid self =
    MVar.read self >>= fun self ->
    match%lwt (Yconnector.Storage.Transports.get_tranport plid transportid self.connector) with
    | Some _ ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.Transports.remove transportid client
         >>= fun _ -> Yconnector.Storage.Transports.remove_transport plid transportid self.connector
         >>= fun _ -> Lwt.return transportid
       | None ->
         Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`TrafficRuleNotExising (`Msg (Printf.sprintf "Transport with id %s not exist" transportid)))



  (* Utils *)

  let rec filter_tx_dep (tx:MEC_Interfaces.transport_info) (rtxs:MEC.transport_dependency list) =
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

  let rec filter_tx (tx:MEC_Interfaces.transport_info) (rtxs:MEC.transport_descriptor list) =
    match rtxs with
    | [] -> false
    | hd::tl ->
      (match hd.protocol = tx.protocol with
       | true -> true
       | false -> filter_tx tx tl
      )


  (* ME App *)
  (* This add service, rules*)
  let add_application plid (app_desc: Fos_im.MEC.appd_descriptor ) state =
    MVar.read state >>= fun self ->
    (* let appid = app_desc.id in *)
    match Mm5Map.find_opt plid self.mm5_clients with
    | Some client ->

      let app_info = app_info_of_descriptor app_desc in
      let app_inst_id = Apero.Option.get app_info.app_instance_id in
      (* let%lwt txs = get_transports plid state in *)
      (* let rtxs = app_desc.transport_dependencies in *)
      (* let mtxs = find_matching_transports txs rtxs in *)
      let svcs =
        List.map ( fun (s:MEC.service_descriptor) ->
            let rtxs = List.map ( fun (t,_) -> t ) s.transport_supported  |> List.hd |> transport_info_of_descriptor in
            service_info_of_descriptor s `JSON rtxs rtxs.id
          ) app_desc.service_produces in
      let app_info = {app_info with service_produced = svcs} in
      Mm5_client.Applications.add app_info client
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
      Yconnector.Storage.ServiceInfo.add_application plid app_inst_id app_info self.connector
      >>= fun _ ->
      Lwt.return app_info
    | None -> Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid)))

  let get_application_by_uuid plid app_uuid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.ServiceInfo.get_application plid app_uuid self.connector

  let get_applications plid self =
    MVar.read self >>= fun self ->
    Yconnector.Storage.ServiceInfo.get_applications plid self.connector

  let get_application_by_name plid app_name self =
    MVar.read self >>= fun self ->
    let%lwt services = Yconnector.Storage.ServiceInfo.get_applications plid self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:MEC_Interfaces.app_info) ->
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
    let%lwt services = Yconnector.Storage.ServiceInfo.get_applications plid self.connector in
    let%lwt services = Lwt_list.filter_map_p (fun (e:MEC_Interfaces.app_info) ->
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
    match%lwt (Yconnector.Storage.ServiceInfo.get_application plid app_uuid self.connector) with
    | Some appi ->
      (match Mm5Map.find_opt plid self.mm5_clients with
       | Some client ->
         Mm5_client.Applications.remove app_uuid client
         >>= fun  _ ->
         Lwt_list.iter_p (fun (ser:MEC_Interfaces.service_info) ->
             remove_service plid (Apero.Option.get ser.ser_instance_id) state >>= fun _ -> Lwt.return_unit
           ) appi.service_produced
         >>= fun _ ->
         Lwt_list.iter_p (fun (t:MEC_Interfaces.traffic_rule) ->
             remove_traffic_rule_for_application plid app_uuid t.traffic_rule_id state >>= fun _ -> Lwt.return_unit
           ) appi.traffic_rules
         >>= fun _ ->
         Lwt_list.iter_p (fun (d:MEC_Interfaces.dns_rule) ->
             remove_dns_rule_for_application plid app_uuid d.dns_rule_id state >>= fun _ -> Lwt.return_unit
           ) appi.dns_rules
         >>= fun _ -> Yconnector.Storage.ServiceInfo.remove_application plid app_uuid self.connector
         >>= fun _ -> Lwt.return app_uuid
       | None -> Lwt.fail @@ MEException (`PlatformNotExisting (`Msg (Printf.sprintf "Platform with id %s not found " plid))))
    | None -> Lwt.fail @@ MEException (`ApplicationNotExisting (`Msg (Printf.sprintf "Application with id %s not exist" app_uuid)))

end



module RO = struct

  type state = {
    connector : Yconnector.connector;
    meao : MEAO.t;
    fim_conns : (module FIM.FIMConn) FIMMap.t;
    completer : unit Lwt.u;
    promise : unit Lwt.t
  }


  type t = state MVar.t

  let create loc meao =
    let f, c =  Lwt.wait () in
    let%lwt con = Yconnector.get_connector_of_locator loc in
    Lwt.return @@ MVar.create ({connector = con; meao = meao; fim_conns= FIMMap.empty; completer = c; promise = f})

  (* Start and Stop *)
  let start self =
    Logs.debug (fun m -> m "[RO] Started...");
    MVar.read self >>= fun self ->
    self.promise >>= Lwt.return
  (* let f,c =  Lwt.wait () in
     MVar.guarded self @@ fun self ->
     MVar.return_lwt f {self with completer = Some c} *)



  let stop self =
    Lwt.wakeup_later self.completer () |> Lwt.return

  let add_fim_conn fim_id connector self =
    Logs.debug (fun m -> m "[RO] Adding FIMConn: %s" fim_id);
    MVar.guarded self @@ fun self ->
    MVar.return () {self with fim_conns = FIMMap.add fim_id connector self.fim_conns}


end