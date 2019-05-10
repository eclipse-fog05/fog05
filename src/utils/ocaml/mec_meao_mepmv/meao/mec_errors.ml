type error_info = [`NoMsg | `Msg of string | `Code of int | `Pos of (string * int * int * int) | `Loc of string] [@@deriving show]

type ferror = [
  | `InternalError of error_info
  | `ServiceNotExisting of error_info
  | `ApplicationNotExisting of error_info
  | `DNSRuleNotExisting of error_info
  | `TrafficRuleNotExising of error_info
  | `TransportNotExisting of error_info
  | `SubscriptionNotExisting of error_info
] [@@deriving show]


exception MEException of ferror [@@deriving show]


let () = Printexc.register_printer @@ function | MEException(e) -> Some ("MException: "^(show_ferror e)) | _ -> None