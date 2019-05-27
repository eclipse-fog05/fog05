open Yojson.Safe

(*    (modules_without_implementation Placement) *)

module type Conf = sig
  val url : string
  val user : string
  val password : string
  val configuration : json
end

(* Plugin for Placement algorithms *)
module type PlacementConn = sig


  val init : unit -> unit Lwt.t
  (* node status list -> cpu count -> ram -> disk -> cpu_arch -> hypervisor -> os -> string -> list of node uuids *)
  val get_elegible_nodes : Pl_types.node_status list -> int -> int -> int -> string -> string -> string list Lwt.t
  val get_optimal_node : json -> string Lwt.t


end