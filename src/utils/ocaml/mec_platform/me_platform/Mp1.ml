(*********************************************************************************
 * Copyright (c) 2019 ADLINK Technology Inc.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
 * which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 * Contributors: 1
 *   Gabriele Baldoni (gabriele (dot) baldoni (at) adlinktech (dot) com ) -
 *********************************************************************************)

(*
 * This API is compliant with ETSI MEC GS 011
 * https://www.etsi.org/deliver/etsi_gs/MEC/001_099/011/01.01.01_60/gs_mec011v010101p.pdf
 * https://forge.etsi.org/gitlab/mec/gs011-app-enablement-api
 * REST Mp1 Interface
 * ME Platfrom <-> ME App
 *)


open Apero
open Httpaf_lwt_unix
open Httpaf
open Lwt.Infix
open Me_core


module Mp1 = struct

  module Str = Re.Str


  type t =  {
    address : string;
    port : int;
    prefix : string;
    core : MEC_Core.t;
  }


  let query_to_string query =
    List.map (fun (n,v) -> Printf.sprintf "%s=%s" n (String.concat "," v)) query
    |> String.concat "&"

  let get_query_parameter query name =
    List.find_opt (fun (k,_) -> k = name) query


  (* HELPERS and ERRORS *)

  let empty_path reqd =
    let headers = Headers.of_list [ "Connection", "close" ] in
    Reqd.respond_with_string reqd (Response.create ~headers `OK)  "Mp1\n"


  let respond_ok reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `OK) s;
    Logs.debug (fun m -> m "[Mp1] : Replied OK with %s" s)


  let respond_created reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `Created) s;
    Logs.debug (fun m -> m "[Mp1] : Replied OK with %s" s)

  (* let respond_bad_request reqd headers s =
     Reqd.respond_with_string reqd (Response.create ~headers `Bad_request) s *)


  let respond_forbidden reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `Forbidden) s

  let respond_not_found reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `Not_found) s


  let error_handler ?request:_ error start_response =
    let response_body = start_response Headers.empty in
    begin match error with
      | `Exn exn ->
        Body.write_string response_body (Base.Exn.to_string exn);
        Body.write_string response_body "\n";
      | #Status.standard as error ->
        Body.write_string response_body (Status.default_reason_phrase error)
    end;
    Body.close_writer response_body
  (* let internal_error msg =
     Server.respond_error ~status:`Internal_server_error ~body:msg () *)

  (* let ex_to_response ex =
     match ex with
     | ex -> internal_error (Printexc.to_string ex) *)

  (*  *)


  let read_body reqd =
    let body = Reqd.request_body reqd in
    let p,c = Lwt.wait () in
    let fullb = Faraday.create 65535 in
    let rec on_read buffer ~off ~len =
      Faraday.write_bigstring ~off ~len fullb buffer;
      Body.schedule_read body ~on_eof ~on_read;
    and on_eof () =
      Faraday.close fullb;
      Lwt.wakeup c (Faraday.serialize_to_string fullb)
    in
    Body.schedule_read body ~on_eof ~on_read;
    p


  let make_sub_url prefix appid kind id =
    prefix ^ "applications" ^ appid ^ "subscriptions" ^ kind ^ id

  let make_svc_url prefix id =
    prefix ^ "services" ^ id



  let execute_http_request self reqd  =
    (* let open Lwt in *)
    let req = Reqd.request reqd in
    let _ = Reqd.request_body reqd in
    let meth = req.meth in
    let uri = req.target in
    let path = List.hd (String.split_on_char '?' uri)  in

    let query =
      (try
         List.nth (String.split_on_char '?' uri) 1 |> String.split_on_char '&' |> List.map (fun e ->  (List.hd (String.split_on_char '=' e),  (List.nth (String.split_on_char '=' e) 1 |> String.split_on_char ',' )))
       with
         _ -> [])
    in
    let headers = req.headers in
    Logs.debug (fun m -> m "[Mp1] HTTP req: %s %s query %s with headers: %a"
                   (Method.to_string meth) path (query_to_string query)
                   Headers.pp_hum headers);
    (* let%lwt _ = Logs_lwt.debug (fun m -> (Body.write_string body) >>=  m "[Mp1] Body: %s" ) in *)
    try
      if path = self.prefix then
        empty_path reqd
      else
        let pl = String.length self.prefix in
        let ls = String.length path in
        let useful_uri = String.sub path pl (ls-pl) in
        Logs.debug (fun m -> m "[Mp1] HTTP URI %s" useful_uri);
        let splitted_uri = String.split_on_char '/' useful_uri in
        match splitted_uri with
        | "applications" :: app_instance_id :: tl ->
          (match tl with
           | ["dns_rules"] ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mp1] : GET DNS Rules for %s" app_instance_id);
                let rules = MEC_Core.get_dns_rules_for_application app_instance_id self.core in
                let f rules =
                  let res = rules
                            |> List.map (fun e -> Rest_types.{dns_rule = e})
                            |> List.map (fun e -> Yojson.Safe.from_string @@ Rest_types.string_of_dns_rule_response e)
                            |> fun x -> Yojson.Safe.to_string @@ (`List x)
                  in
                  Logs.debug (fun m -> m "[Mp1] : DNS Rules for %s -> %s" app_instance_id res);
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                in
                Lwt.on_success rules f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | "dns_rules" :: dns_rule_id :: _ ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mp1] : GET DNS Rule for %s - Rule %s" app_instance_id dns_rule_id);
                let rule = MEC_Core.get_dns_rule_for_application app_instance_id dns_rule_id self.core in
                let f rule =
                  match rule with
                  | Some dnsrule ->
                    Logs.debug (fun m -> m "[Mp1] : Found DNS Rule %s for %s" dns_rule_id app_instance_id);
                    let dnsrule = Rest_types.string_of_dns_rule_response {dns_rule = dnsrule} in
                    respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) dnsrule
                  | None ->
                    Logs.debug (fun m -> m "[Mp1] : Not found DNS Rule %s for %s" dns_rule_id app_instance_id);
                    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=app_instance_id}} in
                    respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                in
                Lwt.on_success rule f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | `PUT ->
                let rule = read_body reqd
                  >>= fun r -> Lwt.return @@ Rest_types.dns_rule_of_string r
                  >>= fun r ->
                  (match r.ttl with
                   | None -> Lwt.return {r with ttl = Some 300}
                   | Some _ -> Lwt.return r)
                  >>= fun dnsrule -> MEC_Core.add_dns_rule_for_application app_instance_id r self.core
                  >>= fun _ -> Lwt.return dnsrule
                in
                let f (rule:Rest_types.dns_rule) =
                  Logs.debug (fun m -> m "[Mp1] : PUT DNS Rule for %s - Rule %s" app_instance_id rule.dns_rule_id);
                  let rrule = Rest_types.string_of_dns_rule_response {dns_rule = rule} in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) rrule
                in
                Lwt.on_success rule f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri );

              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | ["subscriptions"] ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mp1] : GET Subscriptions for %s" app_instance_id );
                let subs = MEC_Core.get_application_subscriptions app_instance_id self.core in
                let f subs =
                  let tsubs, asubs = subs in
                  let tsubs = List.map (fun (id,(sub:Rest_types.app_termination_notification_subscription)) ->
                      Rest_types.{rel = sub.subscription_type; href = make_sub_url self.prefix app_instance_id sub.subscription_type id}
                    )  tsubs in
                  let asubs = List.map (fun (id,(sub:Rest_types.ser_availability_notification_subscription)) ->
                      Rest_types.{rel = sub.subscription_type; href = make_sub_url self.prefix app_instance_id sub.subscription_type id}
                    )  asubs in
                  let subs = tsubs @ asubs in
                  let res = Rest_types.string_of_mp1_subscription_response  {mp1_sub_link_list = {links = {self = {href = uri}; subscription = subs}}} in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                in
                Lwt.on_success subs f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri );
              | `POST ->
                Logs.debug (fun m -> m "[Mp1] : POST Subscriptions for %s" app_instance_id );
                let sub =
                  read_body reqd
                  >>= fun string_sub -> Lwt.return @@ Yojson.Basic.from_string string_sub
                  >>= fun x ->
                  match Yojson.Basic.to_string (Yojson.Basic.Util.member "subscriptionType" x) with
                  | "AppTerminationNotificationSubscription" ->
                    Lwt.return @@ Rest_types.app_termination_notification_subscription_of_string string_sub
                    >>= fun x -> MEC_Core.add_application_termination_subscription app_instance_id x self.core
                    >>= fun subid -> Lwt.return (subid, string_sub)
                  | "SerAvailabilityNotificationSubscription" ->
                    Lwt.return @@ Rest_types.ser_availability_notification_subscription_of_string string_sub
                    >>= fun x -> MEC_Core.add_service_availability_subscription app_instance_id x self.core
                    >>= fun subid -> Lwt.return (subid, string_sub)
                  | _ ->
                    Logs.err (fun m -> m "[Mp1] : POST Subscriptions of type %s is not recognized"( Yojson.Basic.to_string (Yojson.Basic.Util.member "subscriptionType" x) ) );
                    failwith "Error"
                in
                let f sub =
                  let subid, string_sub = sub in
                  let subkind = Yojson.Basic.to_string (Yojson.Basic.Util.member "subscriptionType"( Yojson.Basic.from_string string_sub)) in
                  let sub_uri = make_sub_url self.prefix app_instance_id subkind subid in
                  let res = match subkind with
                    | "AppTerminationNotificationSubscription" ->
                      Rest_types.string_of_app_term_sub_response {app_term_sub = Rest_types.app_termination_notification_subscription_of_string string_sub}
                    | "SerAvailabilityNotificationSubscription" ->
                      Rest_types.string_of_ser_avail_sub_response {ser_avail_sub = Rest_types.ser_availability_notification_subscription_of_string string_sub}
                    | _ ->
                      Logs.err (fun m -> m "[Mp1] : POST Subscriptions of type %s is not recognized" subkind );
                      ""
                  in
                  match res with
                  | "" ->
                    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="subscriptionType not recognized"; status=0; detail=""; instance=""}} in
                    respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                  | _ -> respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", sub_uri]) res
                  (* Headers:
                     location	The resource URI of the created resource	string
                  *)
                in
                (* Should be Lwt.on_any *)
                Lwt.on_success sub f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | "subscriptions" :: "AppTerminationNotificationSubscription" :: subscriptionid :: _ ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mp1] : GET Subscription %s for %s" subscriptionid app_instance_id );
                let sub = MEC_Core.get_application_termination_subscription app_instance_id subscriptionid self.core in
                let f sub =
                  match sub with
                  | Some s ->
                    let res = Rest_types.string_of_app_term_sub_response {app_term_sub = s} in
                    respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                  | None ->
                    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="subscription not found"; status=0; detail=""; instance=""}} in
                    respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                in
                Lwt.on_success sub f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | `DELETE ->
                Logs.debug (fun m -> m "[Mp1] : DELETE Subscription %s for %s" subscriptionid app_instance_id );
                let subid = MEC_Core.remove_application_termination_subscription app_instance_id subscriptionid self.core in
                let f _ =
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                in
                Lwt.on_success subid f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | "subscriptions" :: "SerAvailabilityNotificationSubscription" :: subscriptionid :: _->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mp1] : GET Subscription %s for %s" subscriptionid app_instance_id );
                let sub = MEC_Core.get_service_availability_subscription app_instance_id subscriptionid self.core in
                let f sub =
                  match sub with
                  | Some s ->
                    let res = Rest_types.string_of_ser_avail_sub_response {ser_avail_sub = s} in
                    respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                  | None ->
                    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="subscription not found"; status=0; detail=""; instance=""}} in
                    respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                in
                Lwt.on_success sub f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | `DELETE ->
                Logs.debug (fun m -> m "[Mp1] : DELETE Subscription %s for %s" subscriptionid app_instance_id );
                let subid = MEC_Core.remove_service_availability_subscription app_instance_id subscriptionid self.core in
                let f _ =
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                in
                Lwt.on_success subid f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | ["traffic_rules"] -> (match meth with
               | `GET ->
                 Logs.debug (fun m -> m "[Mp1] : GET Traffic Rules for %s" app_instance_id);
                 let rules = MEC_Core.get_traffic_rules_for_application app_instance_id self.core in
                 let f rules =
                   let res = rules
                             |> List.map (fun e -> Rest_types.{traffic_rule = e})
                             |> List.map (fun e -> Yojson.Safe.from_string @@ Rest_types.string_of_traffic_rule_response e)
                             |> fun x -> Yojson.Safe.to_string @@ (`List x)
                   in
                   Logs.debug (fun m -> m "[Mp1] : Traffic Rules for %s -> %s" app_instance_id res);
                   respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res;
                 in
                 Lwt.on_success rules f;
                 Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
               | _ ->
                 let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                 respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details )
           | "traffic_rules" :: traffic_rule_id :: _->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mp1] : GET Traffic Rule for %s - Rule %s" app_instance_id traffic_rule_id);
                let rule = MEC_Core.get_traffic_rule_for_application app_instance_id traffic_rule_id self.core in
                let f rule =
                  match rule with
                  | Some trafficrule ->
                    Logs.debug (fun m -> m "[Mp1] : Found DNS Rule %s for %s" traffic_rule_id app_instance_id);
                    let trafficrule = Rest_types.string_of_traffic_rule_response {traffic_rule = trafficrule} in
                    respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) trafficrule
                  | None ->
                    Logs.debug (fun m -> m "[Mp1] : Not found DNS Rule %s for %s" traffic_rule_id app_instance_id);
                    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=app_instance_id}} in
                    respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                in
                Lwt.on_success rule f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
              | `PUT ->
                let rule = read_body reqd
                  >>= fun r -> Lwt.return @@ Rest_types.traffic_rule_of_string r
                  >>= fun trafficrule -> MEC_Core.add_traffic_rule_for_application app_instance_id trafficrule self.core
                  >>= fun _ -> Lwt.return trafficrule
                in
                let f (rule:Rest_types.traffic_rule) =
                  Logs.debug (fun m -> m "[Mp1] : PUT Traffic Rule for %s - Rule %s" app_instance_id rule.traffic_rule_id);
                  let rrule = Rest_types.string_of_traffic_rule_response {traffic_rule = rule} in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) rrule
                in
                Lwt.on_success rule f;
                Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri );
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | _ ->
             let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
             respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
          )
        | ["services"] ->(match meth with
            | `GET ->
              (* supported query for:
                 - ser_instance_id
                 - ser_name
                 - ser_category_id
              *)
              Logs.debug (fun m -> m "[Mp1] : GET Services with query %s" (query_to_string query) );
              let ser_ids = get_query_parameter query "ser_instance_id" in
              let ser_names = get_query_parameter query "ser_name" in
              let ser_categories = get_query_parameter query "ser_category_id" in
              let svcs =
                match ser_ids, ser_names, ser_categories with
                | Some (_,ids), None, None ->
                  Lwt_list.map_p (fun sid ->
                      MEC_Core.get_service_by_uuid sid self.core
                    ) ids
                | None, Some (_,names), None ->
                  Lwt_list.map_p  (fun sid ->
                      MEC_Core.get_service_by_name sid self.core
                    ) names
                | None, None, Some (_,categories) ->
                  Lwt_list.map_p (fun sid ->
                      MEC_Core.get_service_by_category_id sid self.core
                    ) categories
                | _ -> failwith "Forbidden"
              in
              let f svcs =
                let rec filt_map osvcs nsvcs =
                  (match osvcs with
                   | hd::tl ->
                     (match hd with
                      | Some ser -> filt_map tl (ser::nsvcs)
                      | None -> filt_map tl nsvcs)
                   | [] -> nsvcs)
                in
                let svcs = filt_map svcs [] in
                let res = List.map (fun e ->
                    Yojson.Safe.from_string @@ Rest_types.string_of_service_info_response {service_info = e}
                  ) svcs |> fun x -> Yojson.Safe.to_string @@ (`List x)
                in
                respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
              in
              (* Should be Lwt.on_any *)
              Lwt.on_success svcs f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri );

            | `POST ->
              Logs.debug (fun m -> m "[Mp1] : POST Service");
              (* Headers:
                   location	The resource URI of the created resource	string
              *)
              let svc = read_body reqd
                >>= fun string_svc -> Lwt.return @@ Rest_types.service_info_of_string string_svc
                >>= fun tsvc -> MEC_Core.add_service tsvc self.core
                >>= fun svc_id -> Lwt.return (svc_id,tsvc)
              in
              let f svc =
                let ser_id, svc = svc in
                let svc_uri = make_svc_url self.prefix ser_id in
                let res = Rest_types.string_of_service_info_response {service_info = svc} in
                respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", svc_uri]) res
              in
              (* Should be Lwt.on_any *)
              Lwt.on_success svc f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri );
            | _ ->
              let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
              respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
        | "services" :: service_id :: _ -> (match meth with
            | `GET ->
              Logs.debug (fun m -> m "[Mp1] : GET Service %s" service_id);
              let svc = MEC_Core.get_service_by_uuid service_id self.core in
              let f svc =
                match svc with
                | Some ser ->
                  let res = Rest_types.string_of_service_info_response {service_info = ser} in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                | None ->
                  let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="service not found"; status=0; detail=""; instance=""}} in
                  respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
              in
              Lwt.on_success svc f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
            | `PUT ->
              Logs.debug (fun m -> m "[Mp1] : PUT Service with id %s" service_id);
              let svc = read_body reqd
                >>= fun string_svc -> Lwt.return @@ Rest_types.service_info_of_string string_svc
                >>= fun tsvc -> MEC_Core.add_service tsvc self.core
                >>= fun _ -> Lwt.return tsvc
              in
              let f svc =
                let res = Rest_types.string_of_service_info_response {service_info = svc} in
                respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
              in
              (* Should be Lwt.on_any *)
              Lwt.on_success svc f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
            | _ ->
              let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
              respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
        | ["timing"; "current_time"] -> (match meth with
            | `GET ->
              let ct = MEC_Core.get_current_time self.core in
              let f ct =
                let res = Rest_types.string_of_current_time_response {current_time = ct} in
                respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
              in
              Lwt.on_success ct f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
            | _ ->
              let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
              respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details )
        | ["timing"; "timing_caps"] -> (match meth with
            | `GET ->
              let tc = MEC_Core.get_timing_caps self.core in
              let f tc =
                let res = Rest_types.string_of_timing_caps_response {timing_caps = tc} in
                respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
              in
              Lwt.on_success tc f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
            | _ ->
              let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
              respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details )
        | ["transports"] -> (match meth with
            | `GET ->
              let txs = MEC_Core.get_transports self.core in
              let f txs =
                let res =List.map (fun e ->
                    Yojson.Safe.from_string @@ Rest_types.string_of_transport_info_response {transport_info = e}
                  ) txs |> fun x -> Yojson.Safe.to_string @@ (`List x)
                in
                respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
              in
              Lwt.on_success txs f;
              Logs.debug (fun m -> m "[Mp1] : DONE %s" useful_uri )
            | _ ->
              let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
              respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details )
        | _ ->
          let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
          respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
    with
    | exn ->
      Logs.err (fun m -> m "Exception %s raised:\n%s" (Printexc.to_string exn) (Printexc.get_backtrace ()));
      raise exn


  let create address prefix port core =
    Lwt.return {address; prefix; port; core}

  let start self =
    Logs.debug (fun m -> m "[Mp1] REST API starting HTTP server on  %s:%d" self.address self.port);
    let cb = execute_http_request self in

    let request_handler (_ : Unix.sockaddr) = cb in
    let error_handler (_ : Unix.sockaddr) = error_handler in

    let sock = Unix.ADDR_INET(Unix.inet_addr_of_string self.address, self.port) in
    Lwt_io.establish_server_with_client_socket sock (Server.create_connection_handler ~request_handler ~error_handler)

    (* let callback _conn req body = execute_http_request self req body in
       (* let u = Cohttp_lwt_unix.Server.create ~stop:fe.stop  ~mode:(`TCP (`Port fe.cfg.port)) (Cohttp_lwt_unix.Server.make ~callback ()) in u *)
       let s = Server.make ~callback () in
       let tcp = `TCP (`Port self.port) in
       Conduit_lwt_unix.serve ~ctx:Conduit_lwt_unix.default_ctx ~mode:tcp (Server.callback s) *)
    >>= fun _ ->
    let f,_ = Lwt.wait () in
    f >>= fun _ -> Lwt.return_unit


  let stop self =
    ignore self;
    Lwt.return_unit

  let destroy self =
    ignore self;
    Lwt.return_unit



end