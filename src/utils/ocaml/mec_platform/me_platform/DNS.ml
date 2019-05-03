open Httpaf
open Httpaf_lwt_unix
open Lwt.Infix



module DynDNS = struct

  type t = {
    address : string;
    port : int;
    base_uri : string;
    (* sock : Lwt_unix.file_descr; *)
    addr_info : Unix.addr_info;
  }



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

  let get_dns_rules self =
    let uri = self.base_uri ^ "/record" in
    let%lwt resp = do_request uri `GET [] "" self in
    let r = Dns_types.get_response_of_string resp in
    Lwt.return r.result

  let add_dns_rule self ip name =
    let uri = self.base_uri ^ "/record" in
    let body =  (Dns_types.string_of_dns_record {ip; name}) ^ "\n" in
    let%lwt resp = do_request uri `PUT [] body self in
    let _ = Dns_types.add_remove_response_of_string resp in
    Lwt.return_unit

  let remove_dns_rule self ip name =
    let uri = self.base_uri ^ "/record" in
    let body =  Dns_types.string_of_dns_record {ip; name} in
    let%lwt resp = do_request uri `DELETE [] body self in
    let _ = Dns_types.add_remove_response_of_string resp in
    Lwt.return_unit

  let create address port base_uri =
    let%lwt addr_info = Lwt_unix.getaddrinfo address (string_of_int port) [Unix.(AI_FAMILY PF_INET)] >>= fun al -> Lwt.return @@ List.hd al in
    Lwt.return {address; port; base_uri; addr_info}

  let destroy  _ =
    Lwt.return_unit

end