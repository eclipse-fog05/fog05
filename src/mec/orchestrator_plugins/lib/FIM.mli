open Fos_im.JSON

(*    (modules_without_implementation FIM) *)

module type Conf = sig
  val url : string
  val user : string
  val password : string
  val configuration : json
end

(* Inspired from ETSI OSM vimconn  *)
module type FIMConn = sig

  (* val create : string -> string -> string -> json -> unit Lwt.t *)

  val connect : unit -> unit Lwt.t

  val check_connectivity : unit -> unit Lwt.t

  val new_network : net_name:string -> net_type:string -> ip_profile:json option-> shared:bool -> vlan:int option -> string Lwt.t

  val get_network_list : unit -> string list Lwt.t

  val get_network : string  -> json Lwt.t

  val delete_network : string  -> string Lwt.t

  val refresh_nets_status : string list  -> json list Lwt.t

  val get_flavor : string  -> string Lwt.t

  val new_flavor : json  -> string Lwt.t

  val delete_flavor : string  -> string Lwt.t

  val new_image : json  -> string Lwt.t

  val get_image_list : unit -> string list Lwt.t

  val new_fdu_instance : name:string -> description:string -> start:bool -> image_id:string -> flavor_id:string -> net_list:string list -> cloud_config:json ->  nodeid:string-> (string * json) Lwt.t

  val get_fdu_instance : string  -> json Lwt.t

  val delete_fdu_instance : string  -> string Lwt.t

  val action_fdu_instance : string -> json -> string  -> (string * json) Lwt.t

  val get_fim_status : unit -> Pl_types.node_status list Lwt.t

end
