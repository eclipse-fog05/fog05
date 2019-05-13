


module DynDNS : sig

  type t

  val create : string -> int -> string -> t Lwt.t

  val get_dns_rules : t -> Dns_types.dns_record list Lwt.t

  val add_dns_rule: t -> string -> string -> unit Lwt.t

  val remove_dns_rule: t -> string -> string -> unit Lwt.t

  val destroy : t -> unit Lwt.t

end