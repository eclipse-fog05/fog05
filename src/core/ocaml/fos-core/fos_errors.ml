type error_info = [`NoMsg | `Msg of string | `Code of int | `Pos of (string * int * int * int) | `Loc of string] [@@deriving show]  

type ferror = [
  | `InternalError of error_info
] [@@deriving show]


exception FException of ferror [@@deriving show]

let () = Printexc.register_printer @@ function | FException(e) -> Some ("YException: "^(show_ferror e)) | _ -> None
