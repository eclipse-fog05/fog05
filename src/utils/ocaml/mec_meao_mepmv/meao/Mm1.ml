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
open Fos_im

module Mm1 = struct


  type t =  {
    address : string;
    port : int;
    prefix : string;
    core : MEAO.t;
  }


  let query_to_string query =
    List.map (fun (n,v) -> Printf.sprintf "%s=%s" n (String.concat "," v)) query
    |> String.concat "&"

  let get_query_parameter query name =
    List.find_opt (fun (k,_) -> k = name) query


  (* HELPERS and ERRORS *)

  let empty_path reqd =
    let headers = Headers.of_list [ "Connection", "close" ] in
    Reqd.respond_with_string reqd (Response.create ~headers `OK)  "{\"api\":\"Mm1\"}"


  let respond_ok reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `OK) s;
    Logs.debug (fun m -> m "[Mm1] : Replied OK with %s" s)


  let respond_created reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `Created) s;
    Logs.debug (fun m -> m "[Mm1] : Replied OK with %s" s)

  let respond_bad_request reqd headers s =
    let headers = Headers.add headers "Connection" "close"  in
    Reqd.respond_with_string reqd (Response.create ~headers `Bad_request) s


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


  let on_err reqd (ex:exn) =
    Logs.debug (fun m -> m "[Mm1] : Exception  %s" (Printexc.to_string ex) );
    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "bad_request"; title=(Printexc.to_string ex); status=0; detail=""; instance=""}} in
    respond_bad_request reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
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

  let make_svc_url prefix id =
    prefix ^ "services/" ^ id

  let make_app_url prefix appid =
    prefix ^ "applications/" ^ appid

  let make_plat_url prefix appid =
    prefix ^ "platform/" ^ appid

  let make_dns_rule_url prefix appid dnsruleid=
    prefix ^ "applications/" ^ appid ^ "/dns_rules/" ^ dnsruleid

  let make_traffic_rule_url prefix appid tfcruleid =
    prefix ^ "applications/" ^ appid ^ "/traffic_rules/" ^ tfcruleid



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
    Logs.debug (fun m -> m "[Mm1] HTTP req: %s %s query %s with headers: %a"
                   (Method.to_string meth) path (query_to_string query)
                   Headers.pp_hum headers);
    (* let%lwt _ = Logs_lwt.debug (fun m -> (Body.write_string body) >>=  m "[Mm1] Body: %s" ) in *)
    try
      if path = self.prefix then
        empty_path reqd
      else
        let pl = String.length self.prefix in
        let ls = String.length path in
        let useful_uri = String.sub path pl (ls-pl) in
        Logs.debug (fun m -> m "[Mm1] HTTP URI %s" useful_uri);
        let splitted_uri = String.split_on_char '/' useful_uri in
        match splitted_uri with
        | ["platforms"] ->
          (match meth with
           | `GET ->
             Logs.debug (fun m -> m "[Mm1] : GET Platforms");
             let plats = MEAO.get_platforms self.core in
             let f plats =
               let res = Rest_types.string_of_platform_info_list_response {platform_info = plats} in
               respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
             in
             Lwt.on_any plats f (on_err reqd);
             Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
           | `POST ->
             Logs.debug (fun m -> m "[Mm1]: POST Platform");
             let platd = read_body reqd
               >>= fun string_platd -> Lwt.return @@ Rest_types.platform_of_string string_platd
               >>= fun platd -> MEAO.add_platform platd self.core
               >>= fun plid -> Lwt.return (plid, platd)
             in
             let f plat =
               let plid, platd = plat in
               let plat_uri = make_plat_url self.prefix plid in
               let res = Rest_types.string_of_platform_info_response {platform_info = platd} in
               respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", plat_uri]) res
             in
             Lwt.on_any platd f (on_err reqd);
             Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
           | _ ->
             let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
             respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
        | "platforms" :: platform_id :: tl ->
          (match tl with
           | [] ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mm1] : GET Platorm %s" platform_id);
                let plat = MEAO.get_platform platform_id self.core in
                let f plat =
                  (match plat with
                   | Some pl ->
                     let res = Rest_types.string_of_platform_info_response (Rest_types.create_platform_info_response ~platform_info:pl ()) in
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                   | None ->
                     Logs.debug (fun m -> m "[Mm1] : Not found platform %s" platform_id);
                     let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=platform_id}} in
                     respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
                in
                Lwt.on_any plat f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
              | `PUT ->
                Logs.debug (fun m -> m "[Mm1] : PUT Platform %s" platform_id);
                let platd = read_body reqd
                  >>= fun string_platd -> Lwt.return @@ Rest_types.platform_of_string string_platd
                  >>= fun platd -> MEAO.add_platform platd self.core
                  >>= fun plid -> Lwt.return (plid, platd)
                in
                let f plat =
                  let plid, platd = plat in
                  let plat_uri = make_plat_url self.prefix plid in
                  let res = Rest_types.string_of_platform_info_response {platform_info = platd} in
                  respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", plat_uri]) res
                in
                Lwt.on_any platd f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
              | `DELETE ->
                Logs.debug (fun m -> m "[Mm1] : DELETE Platorm %s" platform_id);
                let subid = MEAO.remove_platform platform_id self.core in
                let f _ =
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                in
                Lwt.on_any subid f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
              | _->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)


           | ["applications"] ->

             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mm1] : GET Applications");
                let apps = MEAO.get_applications platform_id self.core in
                let f apps =
                  let res = List.map (fun e -> Yojson.Safe.from_string @@ Rest_types.string_of_app_info e) apps |> fun x -> Yojson.Safe.to_string @@ (`List x) in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                in
                Lwt.on_any apps f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | `POST ->
                Logs.debug (fun m -> m "[Mm1] : POST Application");
                (* Headers:
                     location	The resource URI of the created resource	string
                *)
                let app = read_body reqd
                  >>= fun string_appd -> Lwt.return @@ MEC_Types.appd_descriptor_of_string string_appd
                  >>= fun appd -> MEAO.add_application platform_id appd self.core
                  >>= fun appid -> Lwt.return (appid,appd)
                in
                let f app =
                  let appid, appd = app in
                  let app_uri = make_app_url self.prefix appid in
                  let res = MEC_Types.string_of_appd_descriptor appd in
                  respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", app_uri]) res
                in
                (* Should be Lwt.on_any *)
                Lwt.on_any app f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | "applications" :: app_instance_id :: tl ->
             (match tl with
              | [] ->
                (match meth with
                 | `GET ->
                   Logs.debug (fun m -> m "[Mm1] : GET Application %s" app_instance_id);
                   let app = MEAO.get_application_by_uuid platform_id app_instance_id self.core in
                   let f app =
                     (match app with
                      | Some app -> let res = Rest_types.string_of_app_info app in
                        respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                      | None ->
                        Logs.debug (fun m -> m "[Mm1] : Not found application %s" app_instance_id);
                        let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=app_instance_id}} in
                        respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
                   in
                   Lwt.on_any app f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `PUT ->
                   Logs.debug (fun m -> m "[Mm1] : PUT Application %s" app_instance_id);
                   let app = read_body reqd
                     >>= fun string_appd -> Lwt.return @@ MEC_Types.appd_descriptor_of_string string_appd
                     >>= fun appd -> MEAO.add_application platform_id appd self.core
                     >>= fun _ -> Lwt.return appd
                   in
                   let f app =
                     let res = MEC_Types.string_of_appd_descriptor app in
                     respond_created reqd (Headers.of_list ["Content-Type", "application/json"]) res
                   in
                   (* Should be Lwt.on_any *)
                   Lwt.on_any app f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `DELETE ->
                   Logs.debug (fun m -> m "[Mm1] : DELETE Applicaiton %s"  app_instance_id );
                   let subid = MEAO.remove_application platform_id app_instance_id self.core in
                   let f _ =
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                   in
                   Lwt.on_any subid f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | _ -> let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                   respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
              | ["dns_rules"] ->
                (match meth with
                 | `GET ->
                   Logs.debug (fun m -> m "[Mm1] : GET DNS Rules for %s" app_instance_id);
                   let rules = MEAO.get_dns_rules_for_application platform_id app_instance_id self.core in
                   let f rules =
                     let res = rules
                               |> List.map (fun e -> Rest_types.create_dns_rule_response ~dns_rule:e ())
                               |> List.map (fun e -> Yojson.Safe.from_string @@ Rest_types.string_of_dns_rule_response e)
                               |> fun x -> Yojson.Safe.to_string @@ (`List x)
                     in
                     Logs.debug (fun m -> m "[Mm1] : DNS Rules for %s -> %s" app_instance_id res);
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                   in
                   Lwt.on_any rules f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `POST ->
                   Logs.debug (fun m -> m "[Mm1] : POST DNS Rule for %s" app_instance_id);
                   (* Headers:
                        location	The resource URI of the created resource	string
                   *)
                   let dns_rule = read_body reqd
                     >>= fun string_dnsr -> Lwt.return @@ Rest_types.dns_rule_of_string string_dnsr
                     >>= fun dnsr -> MEAO.add_dns_rule_for_application platform_id app_instance_id dnsr self.core
                     >>= fun dnsid -> Lwt.return (dnsid,dnsr)
                   in
                   let f dns_rule =
                     let dnsid, dns_rule = dns_rule in
                     let dnsr_uri = make_dns_rule_url self.prefix app_instance_id dnsid in
                     let res = Rest_types.string_of_dns_rule_response {dns_rule =  dns_rule}  in
                     respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", dnsr_uri]) res
                   in
                   (* Should be Lwt.on_any *)
                   Lwt.on_any dns_rule f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
                 | _ ->
                   let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                   respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
              | "dns_rules" :: dns_rule_id :: _ ->
                (match meth with
                 | `GET ->
                   Logs.debug (fun m -> m "[Mm1] : GET DNS Rule for %s - Rule %s" app_instance_id dns_rule_id);
                   let rule = MEAO.get_dns_rule_for_application platform_id app_instance_id dns_rule_id self.core in
                   let f rule =
                     match rule with
                     | Some dnsrule ->
                       Logs.debug (fun m -> m "[Mm1] : Found DNS Rule %s for %s" dns_rule_id app_instance_id);
                       let dnsrule = Rest_types.string_of_dns_rule_response {dns_rule = dnsrule} in
                       respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) dnsrule
                     | None ->
                       Logs.debug (fun m -> m "[Mm1] : Not found DNS Rule %s for %s" dns_rule_id app_instance_id);
                       let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=app_instance_id}} in
                       respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                   in
                   Lwt.on_any rule f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `PUT ->
                   let rule = read_body reqd
                     >>= fun r -> Lwt.return @@ Rest_types.dns_rule_of_string r
                     >>= fun r ->
                     (match r.ttl with
                      | None -> Lwt.return {r with ttl = Some 300}
                      | Some _ -> Lwt.return r)
                     >>= fun dnsrule -> MEAO.add_dns_rule_for_application platform_id app_instance_id r self.core
                     >>= fun _ -> Lwt.return dnsrule
                   in
                   let f (rule:Rest_types.dns_rule) =
                     Logs.debug (fun m -> m "[Mm1] : PUT DNS Rule for %s - Rule %s" app_instance_id rule.dns_rule_id);
                     let rrule = Rest_types.string_of_dns_rule_response {dns_rule = rule} in
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) rrule
                   in
                   Lwt.on_any rule f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `DELETE ->
                   Logs.debug (fun m -> m "[Mm1] : DELETE DNS Rule %s for %s"  dns_rule_id app_instance_id );
                   let subid = MEAO.remove_dns_rule_for_application platform_id app_instance_id dns_rule_id self.core in
                   let f _ =
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                   in
                   Lwt.on_any subid f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | _ ->
                   let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                   respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
              | ["traffic_rules"] ->
                (match meth with
                 | `GET ->
                   Logs.debug (fun m -> m "[Mm1] : GET Traffic Rules for %s" app_instance_id);
                   let rules = MEAO.get_traffic_rules_for_application platform_id app_instance_id self.core in
                   let f rules =
                     let res = rules
                               |> List.map (fun e -> Rest_types.create_traffic_rule_response ~traffic_rule:e ())
                               |> List.map (fun e -> Yojson.Safe.from_string @@ Rest_types.string_of_traffic_rule_response e)
                               |> fun x -> Yojson.Safe.to_string @@ (`List x)
                     in
                     Logs.debug (fun m -> m "[Mm1] : Traffic Rules for %s -> %s" app_instance_id res);
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res;
                   in
                   Lwt.on_any rules f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `POST ->
                   Logs.debug (fun m -> m "[Mm1] : POST Traffic Rule for %s" app_instance_id);
                   (* Headers:
                        location	The resource URI of the created resource	string
                   *)
                   let tfc_rule = read_body reqd
                     >>= fun string_tfcr ->
                     Logs.debug (fun m -> m "### Traffic Rule %s" string_tfcr);
                     Lwt.return @@ Rest_types.traffic_rule_of_string string_tfcr
                     >>= fun tfcr ->
                     Logs.debug (fun m -> m "### Traffic Rule converted");
                     MEAO.add_traffic_rule_for_application platform_id app_instance_id tfcr self.core
                     >>= fun tfcid ->
                     Logs.debug (fun m -> m "### Put on YAKS done");
                     Lwt.return (tfcid,tfcr)
                   in
                   let f tfc_rule =
                     let tfcid, tfc_rule = tfc_rule in
                     let tfcr_uri = make_traffic_rule_url self.prefix app_instance_id tfcid in
                     let res = Rest_types.string_of_traffic_rule_response {traffic_rule =  tfc_rule}  in
                     respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", tfcr_uri]) res
                   in
                   Lwt.on_any tfc_rule f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
                 | _ ->
                   let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                   respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details )
              | "traffic_rules" :: traffic_rule_id :: _->
                (match meth with
                 | `GET ->
                   Logs.debug (fun m -> m "[Mm1] : GET Traffic Rule for %s - Rule %s" app_instance_id traffic_rule_id);
                   let rule = MEAO.get_traffic_rule_for_application platform_id app_instance_id traffic_rule_id self.core in
                   let f rule =
                     match rule with
                     | Some trafficrule ->
                       Logs.debug (fun m -> m "[Mm1] : Found DNS Rule %s for %s" traffic_rule_id app_instance_id);
                       let trafficrule = Rest_types.string_of_traffic_rule_response {traffic_rule = trafficrule} in
                       respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) trafficrule
                     | None ->
                       Logs.debug (fun m -> m "[Mm1] : Not found DNS Rule %s for %s" traffic_rule_id app_instance_id);
                       let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=app_instance_id}} in
                       respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                   in
                   Lwt.on_any rule f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | `PUT ->
                   let rule = read_body reqd
                     >>= fun r -> Lwt.return @@ Rest_types.traffic_rule_of_string r
                     >>= fun trafficrule -> MEAO.add_traffic_rule_for_application platform_id app_instance_id trafficrule self.core
                     >>= fun _ -> Lwt.return trafficrule
                   in
                   let f (rule:Rest_types.traffic_rule) =
                     Logs.debug (fun m -> m "[Mm1] : PUT Traffic Rule for %s - Rule %s" app_instance_id rule.traffic_rule_id);
                     let rrule = Rest_types.string_of_traffic_rule_response {traffic_rule = rule} in
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) rrule
                   in
                   Lwt.on_any rule f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
                 | `DELETE ->
                   Logs.debug (fun m -> m "[Mm1] : DELETE Traffic Rule %s for %s"  traffic_rule_id app_instance_id );
                   let subid = MEAO.remove_traffic_rule_for_application platform_id app_instance_id traffic_rule_id self.core in
                   let f _ =
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                   in
                   Lwt.on_any subid f (on_err reqd);
                   Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
                 | _ ->
                   let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                   respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | ["services"] ->
             (match meth with
              | `GET ->
                (* supported query for:
                   - ser_instance_id
                   - ser_name
                   - ser_category_id
                *)
                Logs.debug (fun m -> m "[Mm1] : GET Services with query %s" (query_to_string query) );
                let ser_ids = get_query_parameter query "ser_instance_id" in
                let ser_names = get_query_parameter query "ser_name" in
                let ser_categories = get_query_parameter query "ser_category_id" in
                let svcs =
                  match ser_ids, ser_names, ser_categories with
                  | Some (_,ids), None, None ->
                    Lwt_list.map_p (fun sid ->
                        MEAO.get_service_by_uuid platform_id sid self.core
                      ) ids
                  | None, Some (_,names), None ->
                    Lwt_list.map_p  (fun sid ->
                        MEAO.get_service_by_name platform_id sid self.core
                      ) names
                  | None, None, Some (_,categories) ->
                    Lwt_list.map_p (fun sid ->
                        MEAO.get_service_by_category_id platform_id sid self.core
                      ) categories
                  | None, None, None ->
                    MEAO.get_services platform_id self.core >>=
                    Lwt_list.map_p (fun s ->
                        Lwt.return (Some s)
                      )
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
                Lwt.on_any svcs f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | `POST ->
                Logs.debug (fun m -> m "[Mm1] : POST Service");
                (* Headers:
                     location	The resource URI of the created resource	string
                *)
                let svc = read_body reqd
                  >>= fun string_svc -> Lwt.return @@ Rest_types.service_info_of_string string_svc
                  >>= fun tsvc -> MEAO.add_service platform_id tsvc self.core
                  >>= fun svc_id -> Lwt.return (svc_id,tsvc)
                in
                let f svc =
                  let ser_id, svc = svc in
                  let svc_uri = make_svc_url self.prefix ser_id in
                  let res = Rest_types.string_of_service_info_response {service_info = svc} in
                  respond_created reqd (Headers.of_list ["Content-Type", "application/json"; "location", svc_uri]) res
                in
                (* Should be Lwt.on_any *)
                Lwt.on_any svc f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | "services" :: service_id :: _ -> (match meth with
               | `GET ->
                 Logs.debug (fun m -> m "[Mm1] : GET Service %s" service_id);
                 let svc = MEAO.get_service_by_uuid platform_id service_id self.core in
                 let f svc =
                   match svc with
                   | Some ser ->
                     let res = Rest_types.string_of_service_info_response {service_info = ser} in
                     respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                   | None ->
                     let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="service not found"; status=0; detail=""; instance=""}} in
                     respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                 in
                 Lwt.on_any svc f (on_err reqd);
                 Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
               | `PUT ->
                 Logs.debug (fun m -> m "[Mm1] : PUT Service with id %s" service_id);
                 let svc = read_body reqd
                   >>= fun string_svc -> Lwt.return @@ Rest_types.service_info_of_string string_svc
                   >>= fun tsvc -> MEAO.add_service platform_id tsvc self.core
                   >>= fun _ -> Lwt.return tsvc
                 in
                 let f svc =
                   let res = Rest_types.string_of_service_info_response {service_info = svc} in
                   respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                 in
                 (* Should be Lwt.on_any *)
                 Lwt.on_any svc f (on_err reqd);
                 Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
               | `DELETE ->
                 Logs.debug (fun m -> m "[Mm1] : DELETE Service %s "  service_id );
                 let subid = MEAO.remove_service platform_id service_id self.core in
                 let f _ =
                   respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                 in
                 Lwt.on_any subid f (on_err reqd);
                 Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
               | _ ->
                 let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                 respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | ["transports"] ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mm1] : GET Transports");
                let txs = MEAO.get_transports platform_id self.core in
                let f txs =
                  let res =List.map (fun e ->
                      Yojson.Safe.from_string @@ Rest_types.string_of_transport_info_response {transport_info = e}
                    ) txs |> fun x -> Yojson.Safe.to_string @@ (`List x)
                  in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                in
                Lwt.on_any txs f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | `POST ->
                Logs.debug (fun m -> m "[Mm1] : POST Transport");
                (* Headers:
                     location	The resource URI of the created resource	string
                *)
                let tx = read_body reqd
                  >>= fun string_tx -> Lwt.return @@ Rest_types.transport_info_of_string string_tx
                  >>= fun txr -> MEAO.add_tranport platform_id txr self.core
                  >>= fun _ -> Lwt.return txr
                in
                let f tx =
                  let res = Rest_types.string_of_transport_info_response {transport_info =  tx}  in
                  respond_created reqd (Headers.of_list ["Content-Type", "application/json"]) res
                in
                (* Should be Lwt.on_any *)
                Lwt.on_any tx f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri );
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | "transports" :: transport_id :: _ ->
             (match meth with
              | `GET ->
                Logs.debug (fun m -> m "[Mm1] : GET Transport %s" transport_id);
                let tx = MEAO.get_transport_by_id platform_id transport_id self.core in
                let f tx =
                  match tx with
                  | Some tx ->
                    let res = Rest_types.string_of_transport_info_response {transport_info = tx} in
                    respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                  | None ->
                    let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="service not found"; status=0; detail=""; instance=""}} in
                    respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
                in
                Lwt.on_any tx f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | `PUT ->
                Logs.debug (fun m -> m "[Mm1] : PUT Transport with id %s" transport_id);
                let tx = read_body reqd
                  >>= fun string_tx -> Lwt.return @@ Rest_types.transport_info_of_string string_tx
                  >>= fun txt -> MEAO.add_tranport platform_id txt self.core
                  >>= fun _ -> Lwt.return txt
                in
                let f tx =
                  let res = Rest_types.string_of_transport_info_response {transport_info = tx} in
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) res
                in
                (* Should be Lwt.on_any *)
                Lwt.on_any tx f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | `DELETE ->
                Logs.debug (fun m -> m "[Mm1] : DELETE Transport %s "  transport_id );
                let subid = MEAO.remove_transport platform_id transport_id self.core in
                let f _ =
                  respond_ok reqd (Headers.of_list ["Content-Type", "application/json"]) ""
                in
                Lwt.on_any subid f (on_err reqd);
                Logs.debug (fun m -> m "[Mm1] : DONE %s" useful_uri )
              | _ ->
                let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "forbidden"; title="forbidden"; status=0; detail=""; instance=""}} in
                respond_forbidden reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
           | _ ->
             let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=""}} in
             respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details)
        | _ ->
          let problem_details = Rest_types.string_of_error_response @@ {problem_details = { err_type = "not found"; title="not found"; status=0; detail=""; instance=""}} in
          respond_not_found reqd (Headers.of_list ["Content-Type", "application/json"]) problem_details
    with
    | exn ->
      Logs.err (fun m -> m "Exception %s raised:\n%s" (Printexc.to_string exn) (Printexc.get_backtrace ()));
      raise exn


  let create address prefix port core =
    Lwt.return {address; prefix; port; core}

  let start self =
    Logs.debug (fun m -> m "[Mm1] REST API starting HTTP server on  %s:%d" self.address self.port);
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