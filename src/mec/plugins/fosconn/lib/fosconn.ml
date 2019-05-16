open Fos_fim_api
(* open Fos_im.Errors *)
(* open Lwt.Infix *)
open FIMPlugin

module FOSConn(C : FIM.Conf) : FIM.FIMConn = struct

  type t = {
    client : Fos_fim_api.api
  }


  let self = ref None


  let connect () =
    let%lwt x = FIMAPI.connect ~locator:(Apero.Option.get (Apero_net.Locator.of_string C.url)) ~sysid:"0" ~tenantid:"0" () in
    self := Some {client  = x };
    Lwt.return_unit

  let check_connectivity () =
    Logs.debug (fun m -> m "[FOSConn] - Check connectivity");
    Lwt.return_unit
  (* self >>= fun self -> *)
  (* let self = !self in *)
  (* match%lwt Node.list self.client with
     | [] -> raise @@ FException (`InternalError (`Msg ("Unable to reach the FIM")))
     | _ -> Lwt.return_unit *)

  let new_network net_name net_type ip_profile shared vlan =
    ignore ip_profile;
    ignore shared;
    ignore vlan;
    (* net_type = | BRIDGE | DATA | PTP *)
    Logs.debug (fun m -> m "[FOSConn] - New network %s : %s " net_name net_type);
    let net_id = Apero.Uuid.make () |> Apero.Uuid.to_string in
    Lwt.return net_id

  let get_network_list () =
    Logs.debug (fun m -> m "[FOSConn] - Network list");
    Lwt.return []

  let get_network net_id =
    Logs.debug (fun m -> m "[FOSConn] - Get network %s" net_id);
    ignore net_id;
    Lwt.return @@ Fos_im.JSON.create_empty ()

  let delete_network net_id =
    Logs.debug (fun m -> m "[FOSConn] - Delete network %s" net_id);
    Lwt.return net_id

  let refresh_nets_status net_list =
    Logs.debug (fun m -> m "[FOSConn] - Refresh nets");
    ignore net_list;
    Lwt.return []

  let get_flavor flv_id =
    Logs.debug (fun m -> m "[FOSConn] - Get flavor %s" flv_id);
    Lwt.return flv_id

  let new_flavor flavor_data =
    Logs.debug (fun m -> m "[FOSConn] - New flavor");
    ignore flavor_data;
    let flv_id = Apero.Uuid.make () |> Apero.Uuid.to_string in
    Lwt.return flv_id

  let delete_flavor flv_id =
    Logs.debug (fun m -> m "[FOSConn] - Delete flavor %s" flv_id);
    Lwt.return flv_id

  let new_image image_data =
    ignore image_data;
    Logs.debug (fun m -> m "[FOSConn] - Add image");
    let img_id = Apero.Uuid.make () |> Apero.Uuid.to_string in
    Lwt.return img_id

  let get_image_list () =
    Logs.debug (fun m -> m "[FOSConn] - Get image list");
    Lwt.return []

  let new_fdu_instance name description start image_id flavor_id net_list cloud_config =
    Logs.debug ( fun m -> m "[FOSConn] - New FDU instance");
    ignore name;
    ignore description;
    ignore start;
    ignore image_id;
    ignore flavor_id;
    ignore net_list;
    ignore cloud_config;
    Lwt.return ("", Fos_im.JSON.create_empty ())

  let get_fdu_instance fdu_instance_id =
    Logs.debug (fun m -> m "[FOSConn] - Get FDU instance %s" fdu_instance_id);
    ignore fdu_instance_id;
    Lwt.return @@ Fos_im.JSON.create_empty ()

  let delete_fdu_instance fdu_instance_id =
    Logs.debug (fun m -> m"[FOSConn] - Delete FDU instance %s" fdu_instance_id);
    Lwt.return  fdu_instance_id

  let action_fdu_instance fdu_instance_id created_items action =
    Logs.debug (fun m -> m "[FOSConn] - Actiont to FDU instance %s -> %s" fdu_instance_id action);
    ignore created_items;
    ignore action;
    Lwt.return (fdu_instance_id, created_items)

  let get_fim_status () =
    Logs.debug (fun m -> m "[FOSConn] - Get FIM Status");

    Lwt.return @@ Fos_im.JSON.create_empty ()

end


module M:FIMPlugin =
struct

  let make url user password conf =
    (module  (FOSConn(struct
                let url = url
                let user = user
                let password = password
                let configuration = conf
              end)) : FIM.FIMConn)
end


let () =
  p := Some (module M:FIMPlugin)

(* Check *)

(* http://zderadicka.eu/plugins-in-ocaml-with-dynlink-library/ *)