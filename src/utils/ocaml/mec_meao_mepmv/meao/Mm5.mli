


module Mm5_client : sig

  type t
  type client

  val create : string -> int -> string -> t Lwt.t

  val destroy : t -> unit Lwt.t


  module Applications : sig

    val list : t -> (Rest_types.app_info list )Lwt.t

    val add : Rest_types.app_info -> t -> string Lwt.t

    val get : string -> t -> Rest_types.app_info Lwt.t

    val remove : string -> t -> string Lwt.t

    val update :  string -> Rest_types.app_info -> t -> string Lwt.t

  end

  module DnsRules : sig

    val list : string -> t -> (Rest_types.dns_rule list) Lwt.t

    val add : string -> Rest_types.dns_rule -> t -> string Lwt.t

    val get : string -> string -> t -> Rest_types.dns_rule Lwt.t

    val remove : string -> string -> t -> string Lwt.t

    val update :  string -> string -> Rest_types.dns_rule -> t -> string Lwt.t

  end

  module TrafficRules : sig

    val list : string -> t -> (Rest_types.traffic_rule list) Lwt.t

    val add : string -> Rest_types.traffic_rule -> t -> string Lwt.t

    val get : string -> string -> t -> Rest_types.traffic_rule Lwt.t

    val remove : string -> string -> t -> string Lwt.t

    val update :  string -> string -> Rest_types.traffic_rule -> t -> string Lwt.t

  end


  module Services : sig

    val list : client -> (Rest_types.service_info list )Lwt.t

    val add : Rest_types.service_info -> t -> string Lwt.t

    val get : string -> t -> Rest_types.service_info Lwt.t

    val remove : string -> t -> string Lwt.t

    val update :  string -> Rest_types.service_info -> t -> string Lwt.t
  end

  module Transports : sig

    val list : t -> (Rest_types.transport_info list) Lwt.t

    val add : Rest_types.transport_info -> t -> string Lwt.t

    val get : string -> t -> Rest_types.transport_info Lwt.t

    val remove : string -> t -> string Lwt.t

    val update :  string -> Rest_types.transport_info -> t -> string Lwt.t

  end

end