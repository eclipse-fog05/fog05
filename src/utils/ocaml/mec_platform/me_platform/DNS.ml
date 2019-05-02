open Httpaf
open Httpaf_lwt_unix
open Lwt.Infix



module DynDNS = struct

  type t = {
    address : string;
    port : int;
    base_uri : string;
  }



  let read_body body =
    (* let p,c = Lwt.wait () in *)
    let fullb = Faraday.create 65535 in
    let rec on_read buffer ~off ~len =
      Faraday.write_bigstring ~off ~len fullb buffer;
      Body.schedule_read body ~on_eof ~on_read;
    and on_eof () =
      Faraday.close fullb;
      (* Lwt.wakeup c () *)
    in
    Body.schedule_read body ~on_eof ~on_read;
    while Faraday.is_closed fullb == false do
      ()
    done;
    Faraday.serialize_to_string fullb

  let do_request uri meth header body self =

    let p,c = Lwt.wait () in
    let error_handler _ = Logs.err (fun m ->  m "This is and DNS client error") in
    let response_handler _ resp_body =
      let body = read_body resp_body  in
      Logs.debug (fun m -> m "Body is %s" body);
      Lwt.wakeup c (body);
    in
    let%lwt address = Lwt_unix.getaddrinfo self.address (string_of_int self.port) [Unix.(AI_FAMILY PF_INET)] >>= fun al -> Lwt.return @@ List.hd al in
    let socket = Lwt_unix.socket Unix.PF_INET Unix.SOCK_STREAM 0 in
    let%lwt _ = Lwt_unix.connect socket address.Unix.ai_addr in
    let headers = Headers.of_list ([
        "content-lenght", (string_of_int (String.length body));
        "connection", "clone";
      ] @ header)
    in
    let request_body = Client.request ~error_handler ~response_handler socket (Request.create ~headers meth uri) in
    Body.write_string request_body body;
    Body.close_writer request_body;
    p

  let get_dns_rules self =
    let uri = self.base_uri ^ "/record" in
    let%lwt resp = do_request uri `GET [] "" self in
    let r = Dns_types.get_response_of_string resp in
    Lwt.return r.result

  let add_dns_rule self ip name =
    let uri = self.base_uri ^ "/record" in
    let body =  Dns_types.string_of_dns_record {ip; name} in
    let%lwt resp = do_request uri `POST [] body self in
    let _ = Dns_types.add_remove_response_of_string resp in
    Lwt.return_unit

  let remove_dns_rule self ip name =
    let uri = self.base_uri ^ "/record" in
    let body =  Dns_types.string_of_dns_record {ip; name} in
    let%lwt resp = do_request uri `DELETE [] body self in
    let _ = Dns_types.add_remove_response_of_string resp in
    Lwt.return_unit

  let create address port base_uri =
    Lwt.return {address; port; base_uri}

  let destroy  _ =
    Lwt.return_unit

end