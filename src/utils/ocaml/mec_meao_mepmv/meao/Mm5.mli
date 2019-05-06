


module Mm5_client : sig

  type t
  type client

  val create : string -> int -> string -> t Lwt.t

  val destroy : t -> unit Lwt.t


  module Applications : sig

    val list : client -> (Fos_im.MEC_Types.appd_descriptor list )Lwt.t

    val add : Fos_im.MEC_Types.appd_descriptor -> client -> string Lwt.t

    val get : string -> client -> Fos_im.MEC_Types.appd_descriptor Lwt.t

    val remove : string -> client -> string Lwt.t

    val update :  string -> Fos_im.MEC_Types.appd_descriptor -> client -> string Lwt.t

  end

  module DnsRules : sig

    val list : string -> client -> (Rest_types.dns_rule list) Lwt.t

    val add : string -> Rest_types.dns_rule -> client -> string Lwt.t

    val get : string -> string -> client -> Rest_types.dns_rule Lwt.t

    val remove : string -> string -> client -> string Lwt.t

    val update :  string -> string -> Rest_types.dns_rule -> client -> string Lwt.t

  end

  module TrafficRules : sig

    val list : string -> client -> (Rest_types.traffic_rule list) Lwt.t

    val add : string -> Rest_types.traffic_rule -> client -> string Lwt.t

    val get : string -> string -> client -> Rest_types.traffic_rule Lwt.t

    val remove : string -> string -> client -> string Lwt.t

    val update :  string -> string -> Rest_types.traffic_rule -> client -> string Lwt.t

  end


  module Services : sig

    val list : client -> (Rest_types.service_info list )Lwt.t

    val add : Rest_types.service_info -> t -> string Lwt.t

    val get : string -> client -> Rest_types.service_info Lwt.t

    val remove : string -> client -> string Lwt.t

    val update :  string -> Rest_types.service_info -> client -> string Lwt.t
  end

  module Transports : sig

    val list : client -> (Rest_types.transport_info list) Lwt.t

    val add : Rest_types.transport_info -> t -> string Lwt.t

    val get : string -> client -> Rest_types.transport_info Lwt.t

    val remove : string -> client -> string Lwt.t

    val update :  string -> Rest_types.transport_info -> client -> string Lwt.t

  end

end