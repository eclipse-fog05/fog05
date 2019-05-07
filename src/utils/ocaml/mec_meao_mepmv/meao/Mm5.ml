open Httpaf
open Httpaf_lwt_unix
open Lwt.Infix



module Mm5_client = struct

  type client = {
    address : string;
    port : int;
    base_uri : string;
    (* sock : Lwt_unix.file_descr; *)
    addr_info : Unix.addr_info;
  }


  type t = client


  let read_body body =
    let p,c = Lwt.wait () in
    let fullb = Faraday.create 65535 in
    let rec on_read buffer ~off ~len =
      if len > 0 then
        begin
          Faraday.write_bigstring ~off ~len fullb buffer;
          Body.schedule_read body ~on_eof ~on_read;
        end
      else
        on_eof ();
    and on_eof () =
      Faraday.close fullb;
      Lwt.wakeup_later c (Faraday.serialize_to_string fullb);
    in
    Body.schedule_read body ~on_eof ~on_read;
    p


  let do_request uri meth header body self =
    let sock = Lwt_unix.socket Unix.PF_INET Unix.SOCK_STREAM 0 in
    let p,c = Lwt.wait () in
    let error_handler _ =
      Logs.err (fun m ->  m "This is a DNS client error");
      Lwt.wakeup c ""
    in
    let response_handler _ resp_body =
      let _ = (read_body resp_body >>= fun body ->
               Logs.debug (fun m -> m "Body is %s" body);
               Lwt.wakeup_later c (body);
               Lwt_unix.close sock)
      in ()
      (* Create only one sck *)
    in
    let%lwt _ = Lwt_unix.connect sock self.addr_info.Unix.ai_addr in
    let headers = Headers.of_list ([
        "Content-Length", (string_of_int (String.length body));
        "Connection", "keep-alive";
      ] @ header)
    in
    let request_body = Client.request ~error_handler ~response_handler sock (Request.create ~headers meth uri) in
    Body.write_string request_body body;
    Body.close_writer request_body;
    let%lwt res = p in
    Lwt.return res

  let create address port base_uri =
    let%lwt addr_info = Lwt_unix.getaddrinfo address (string_of_int port) [Unix.(AI_FAMILY PF_INET)] >>= fun al -> Lwt.return @@ List.hd al in
    Lwt.return {address; port; base_uri; addr_info}

  let destroy  _ =
    Lwt.return_unit


  module Applications = struct

    let list client =
      let uri = client.base_uri ^ "/applications" in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.application_info_list_response_of_string resp in
      Lwt.return r.application_info

    let add appd client =
      let uri =  client.base_uri ^  "/applications" in
      let%lwt resp = do_request uri `POST [] (Rest_types.string_of_app_info appd) client in
      let _ = Rest_types.application_info_response_of_string resp in
      Lwt.return @@ Apero.Option.get appd.app_instance_id


    let get appid client =
      let uri = client.base_uri ^ "/applications/"  ^ appid in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.application_info_response_of_string resp in
      Lwt.return r.application_info

    let remove appid client =
      let uri = client.base_uri ^ "/applications/"  ^ appid in
      let%lwt _ = do_request uri `DELETE [] "" client in
      Lwt.return appid


    let update appid appd client =
      let uri = client.base_uri ^ "/applications/"  ^ appid in
      let%lwt resp = do_request uri `PUT [] (Rest_types.string_of_app_info appd) client in
      let _ = Rest_types.application_info_response_of_string resp in
      Lwt.return @@ Apero.Option.get appd.app_instance_id

  end

  module DnsRules = struct

    let list appid client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "dns_rules" in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.dns_rule_list_response_of_string resp in
      Lwt.return r.dns_rule

    let add appid dnsrule client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "dns_rules" in
      let%lwt resp = do_request uri `POST [] (Rest_types.string_of_dns_rule dnsrule) client in
      let r = Rest_types.dns_rule_response_of_string resp in
      Lwt.return @@ r.dns_rule.dns_rule_id


    let get appid dns_rule_id client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "dns_rules/" ^ dns_rule_id in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.dns_rule_response_of_string resp in
      Lwt.return @@ r.dns_rule

    let remove appid dns_rule_id client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "dns_rules/" ^ dns_rule_id in
      let%lwt _ = do_request uri `DELETE [] "" client in
      Lwt.return dns_rule_id


    let update appid dns_rule_id dnsrule client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "dns_rules/" ^ dns_rule_id in
      let%lwt resp = do_request uri `PUT [] (Rest_types.string_of_dns_rule dnsrule) client in
      let r = Rest_types.dns_rule_response_of_string resp in
      Lwt.return @@ r.dns_rule.dns_rule_id

  end

  module TrafficRules = struct

    let list appid client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "traffic_rules" in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.traffic_rule_list_response_of_string resp in
      Lwt.return r.traffic_rule

    let add appid tfcrule client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "traffic_rules" in
      let%lwt resp = do_request uri `POST [] (Rest_types.string_of_traffic_rule tfcrule) client in
      let r = Rest_types.traffic_rule_response_of_string resp in
      Lwt.return @@ r.traffic_rule.traffic_rule_id


    let get appid dns_rule_id client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "traffic_rules/" ^ dns_rule_id in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.traffic_rule_response_of_string resp in
      Lwt.return @@ r.traffic_rule

    let remove appid dns_rule_id client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "traffic_rules/" ^ dns_rule_id in
      let%lwt _ = do_request uri `DELETE [] "" client in
      Lwt.return dns_rule_id


    let update appid dns_rule_id tfcrule client =
      let uri = client.base_uri ^ "/applications/" ^ appid ^ "traffic_rules/" ^ dns_rule_id in
      let%lwt resp = do_request uri `PUT [] (Rest_types.string_of_traffic_rule tfcrule) client in
      let r = Rest_types.traffic_rule_response_of_string resp in
      Lwt.return @@ r.traffic_rule.traffic_rule_id

  end


  module Services = struct

    let list client =
      let uri = client.base_uri ^ "/services" in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.service_info_list_response_of_string resp in
      Lwt.return r.service_info

    let add svcd client =
      let uri =  client.base_uri ^  "/services" in
      let%lwt resp = do_request uri `POST [] (Rest_types.string_of_service_info svcd) client in
      let _ = Rest_types.service_info_response_of_string resp in
      Lwt.return @@ Apero.Option.get (svcd.ser_instance_id)


    let get svcid client =
      let uri = client.base_uri ^ "/services/"  ^ svcid in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.service_info_response_of_string resp in
      Lwt.return r.service_info

    let remove svcid client =
      let uri = client.base_uri ^ "/services/"  ^ svcid in
      let%lwt _ = do_request uri `DELETE [] "" client in
      Lwt.return svcid


    let update svcid svcd client =
      let uri = client.base_uri ^ "/services/"  ^ svcid in
      let%lwt resp = do_request uri `PUT [] (Rest_types.string_of_service_info svcd) client in
      let r = Rest_types.service_info_response_of_string resp in
      Lwt.return @@ Apero.Option.get (r.service_info.ser_instance_id)
  end

  module Transports = struct

    let list client =
      let uri = client.base_uri ^ "/transports" in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.transport_info_list_response_of_string resp in
      Lwt.return r.transport_info

    let add txd client =
      let uri =  client.base_uri ^  "/transports" in
      let%lwt resp = do_request uri `POST [] (Rest_types.string_of_transport_info txd) client in
      let _ = Rest_types.transport_info_response_of_string resp in
      Lwt.return @@ txd.id


    let get txid client =
      let uri = client.base_uri ^ "/transports/"  ^ txid in
      let%lwt resp = do_request uri `GET [] "" client in
      let r = Rest_types.transport_info_response_of_string resp in
      Lwt.return @@ r.transport_info

    let remove txid client =
      let uri = client.base_uri ^ "/transports/"  ^ txid in
      let%lwt _ = do_request uri `DELETE [] "" client in
      Lwt.return txid


    let update txid txd client =
      let uri = client.base_uri ^ "/transports/"  ^ txid in
      let%lwt resp = do_request uri `PUT [] (Rest_types.string_of_transport_info txd) client in
      let r = Rest_types.transport_info_response_of_string resp in
      Lwt.return @@ (r.transport_info.id)

  end

end