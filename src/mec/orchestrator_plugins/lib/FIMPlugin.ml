open Yojson.Safe

module type FIMPlugin =
sig
  val make : string -> string -> string -> json -> (module FIM.FIMConn)
end

let p = ref None
let get_plugin () : (module FIMPlugin) =
  match !p with
  | Some s -> s
  | None -> failwith "No plugin loaded"