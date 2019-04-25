


module Mm5 : sig

  type t

  val create : string -> string -> int -> Me_core.MEC_Core.t ->t Lwt.t

  val start : t -> unit Lwt.t

  val stop : t -> unit Lwt.t

  val destroy : t -> unit Lwt.t

end