open Fos_im.JSON

module type PlacementPlugin =
sig
  val make : string -> string -> string -> json -> (module Placement.PlacementConn)
end

let p = ref None
let get_plugin () : (module PlacementPlugin) =
  match !p with
  | Some s -> s
  | None -> failwith "No plugin loaded"