type error_info = [`NoMsg | `Msg of string | `Code of int | `Pos of (string * int * int * int) | `Loc of string | `MsgCode of (string * int)] [@@deriving show]

type ferror = [
  | `InternalError of error_info
  | `InformationModelError of error_info
  | `NotFound of error_info
  | `NotAuthorized of error_info
  | `PluginNotFound of error_info
  | `NoCompatibleNodes of error_info
] [@@deriving show]


exception FException of ferror [@@deriving show]

let () = Printexc.register_printer @@ function | FException(e) -> Some ("FException: "^(show_ferror e)) | _ -> None



type merror = [
  | `InternalError of error_info
  | `ServiceNotExisting of error_info
  | `ApplicationNotExisting of error_info
  | `DNSRuleNotExisting of error_info
  | `TrafficRuleNotExising of error_info
  | `TransportNotExisting of error_info
  | `SubscriptionNotExisting of error_info
  | `PlatformNotExisting of error_info
  | `DuplicatedResource of error_info
] [@@deriving show]


exception MEException of merror [@@deriving show]


let () = Printexc.register_printer @@ function | MEException(e) -> Some ("MException: "^(show_merror e)) | _ -> None