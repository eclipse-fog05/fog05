open Fos_im


module Mm5_client : sig

  type t
  type client

  val create : string -> int -> string -> t Lwt.t

  val destroy : t -> unit Lwt.t


  module Applications : sig

    val list : t -> (MEC_Interfaces.app_info list )Lwt.t

    val add : MEC_Interfaces.app_info -> t -> string Lwt.t

    val get : string -> t -> MEC_Interfaces.app_info Lwt.t

    val remove : string -> t -> string Lwt.t

    val update :  string -> MEC_Interfaces.app_info -> t -> string Lwt.t

  end

  module DnsRules : sig

    val list : string -> t -> (MEC_Interfaces.dns_rule list) Lwt.t

    val add : string -> MEC_Interfaces.dns_rule -> t -> string Lwt.t

    val get : string -> string -> t -> MEC_Interfaces.dns_rule Lwt.t

    val remove : string -> string -> t -> string Lwt.t

    val update :  string -> string -> MEC_Interfaces.dns_rule -> t -> string Lwt.t

  end

  module TrafficRules : sig

    val list : string -> t -> (MEC_Interfaces.traffic_rule list) Lwt.t

    val add : string -> MEC_Interfaces.traffic_rule -> t -> string Lwt.t

    val get : string -> string -> t -> MEC_Interfaces.traffic_rule Lwt.t

    val remove : string -> string -> t -> string Lwt.t

    val update :  string -> string -> MEC_Interfaces.traffic_rule -> t -> string Lwt.t

  end


  module Services : sig

    val list : client -> (MEC_Interfaces.service_info list )Lwt.t

    val add : MEC_Interfaces.service_info -> t -> string Lwt.t

    val get : string -> t -> MEC_Interfaces.service_info Lwt.t

    val remove : string -> t -> string Lwt.t

    val update :  string -> MEC_Interfaces.service_info -> t -> string Lwt.t
  end

  module Transports : sig

    val list : t -> (MEC_Interfaces.transport_info list) Lwt.t

    val add : MEC_Interfaces.transport_info -> t -> string Lwt.t

    val get : string -> t -> MEC_Interfaces.transport_info Lwt.t

    val remove : string -> t -> string Lwt.t

    val update :  string -> MEC_Interfaces.transport_info -> t -> string Lwt.t

  end

end