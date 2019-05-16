(* Auto-generated from "types.atd" *)
[@@@ocaml.warning "-27-32-35-39"]

type ram_status = { total: float; free: float }

type neighbor_peer_info = { name: string; id: string }

type neighbor_info = { node: neighbor_peer_info; port: neighbor_peer_info }

type neighbor = { src: neighbor_info; dst: neighbor_info }

type disk_status = { mount_point: string; total: float; free: float }

type node_status = {
  uuid: string;
  ram: ram_status;
  disk: disk_status list;
  neighbors: neighbor list
}

type json = Yojson.Safe.json

let write_ram_status : _ -> ram_status -> _ = (
  fun ob x ->
    Bi_outbuf.add_char ob '{';
    let is_first = ref true in
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"total\":";
    (
      Yojson.Safe.write_std_float
    )
      ob x.total;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"free\":";
    (
      Yojson.Safe.write_std_float
    )
      ob x.free;
    Bi_outbuf.add_char ob '}';
)
let string_of_ram_status ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_ram_status ob x;
  Bi_outbuf.contents ob
let read_ram_status = (
  fun p lb ->
    Yojson.Safe.read_space p lb;
    Yojson.Safe.read_lcurl p lb;
    let field_total = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_free = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let bits0 = ref 0 in
    try
      Yojson.Safe.read_space p lb;
      Yojson.Safe.read_object_end lb;
      Yojson.Safe.read_space p lb;
      let f =
        fun s pos len ->
          if pos < 0 || len < 0 || pos + len > String.length s then
            invalid_arg "out-of-bounds substring position or length";
          match len with
            | 4 -> (
                if String.unsafe_get s pos = 'f' && String.unsafe_get s (pos+1) = 'r' && String.unsafe_get s (pos+2) = 'e' && String.unsafe_get s (pos+3) = 'e' then (
                  1
                )
                else (
                  -1
                )
              )
            | 5 -> (
                if String.unsafe_get s pos = 't' && String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 't' && String.unsafe_get s (pos+3) = 'a' && String.unsafe_get s (pos+4) = 'l' then (
                  0
                )
                else (
                  -1
                )
              )
            | _ -> (
                -1
              )
      in
      let i = Yojson.Safe.map_ident p f lb in
      Atdgen_runtime.Oj_run.read_until_field_value p lb;
      (
        match i with
          | 0 ->
            field_total := (
              (
                Atdgen_runtime.Oj_run.read_number
              ) p lb
            );
            bits0 := !bits0 lor 0x1;
          | 1 ->
            field_free := (
              (
                Atdgen_runtime.Oj_run.read_number
              ) p lb
            );
            bits0 := !bits0 lor 0x2;
          | _ -> (
              Yojson.Safe.skip_json p lb
            )
      );
      while true do
        Yojson.Safe.read_space p lb;
        Yojson.Safe.read_object_sep p lb;
        Yojson.Safe.read_space p lb;
        let f =
          fun s pos len ->
            if pos < 0 || len < 0 || pos + len > String.length s then
              invalid_arg "out-of-bounds substring position or length";
            match len with
              | 4 -> (
                  if String.unsafe_get s pos = 'f' && String.unsafe_get s (pos+1) = 'r' && String.unsafe_get s (pos+2) = 'e' && String.unsafe_get s (pos+3) = 'e' then (
                    1
                  )
                  else (
                    -1
                  )
                )
              | 5 -> (
                  if String.unsafe_get s pos = 't' && String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 't' && String.unsafe_get s (pos+3) = 'a' && String.unsafe_get s (pos+4) = 'l' then (
                    0
                  )
                  else (
                    -1
                  )
                )
              | _ -> (
                  -1
                )
        in
        let i = Yojson.Safe.map_ident p f lb in
        Atdgen_runtime.Oj_run.read_until_field_value p lb;
        (
          match i with
            | 0 ->
              field_total := (
                (
                  Atdgen_runtime.Oj_run.read_number
                ) p lb
              );
              bits0 := !bits0 lor 0x1;
            | 1 ->
              field_free := (
                (
                  Atdgen_runtime.Oj_run.read_number
                ) p lb
              );
              bits0 := !bits0 lor 0x2;
            | _ -> (
                Yojson.Safe.skip_json p lb
              )
        );
      done;
      assert false;
    with Yojson.End_of_object -> (
        if !bits0 <> 0x3 then Atdgen_runtime.Oj_run.missing_fields p [| !bits0 |] [| "total"; "free" |];
        (
          {
            total = !field_total;
            free = !field_free;
          }
         : ram_status)
      )
)
let ram_status_of_string s =
  read_ram_status (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write_neighbor_peer_info : _ -> neighbor_peer_info -> _ = (
  fun ob x ->
    Bi_outbuf.add_char ob '{';
    let is_first = ref true in
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"name\":";
    (
      Yojson.Safe.write_string
    )
      ob x.name;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"id\":";
    (
      Yojson.Safe.write_string
    )
      ob x.id;
    Bi_outbuf.add_char ob '}';
)
let string_of_neighbor_peer_info ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_neighbor_peer_info ob x;
  Bi_outbuf.contents ob
let read_neighbor_peer_info = (
  fun p lb ->
    Yojson.Safe.read_space p lb;
    Yojson.Safe.read_lcurl p lb;
    let field_name = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_id = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let bits0 = ref 0 in
    try
      Yojson.Safe.read_space p lb;
      Yojson.Safe.read_object_end lb;
      Yojson.Safe.read_space p lb;
      let f =
        fun s pos len ->
          if pos < 0 || len < 0 || pos + len > String.length s then
            invalid_arg "out-of-bounds substring position or length";
          match len with
            | 2 -> (
                if String.unsafe_get s pos = 'i' && String.unsafe_get s (pos+1) = 'd' then (
                  1
                )
                else (
                  -1
                )
              )
            | 4 -> (
                if String.unsafe_get s pos = 'n' && String.unsafe_get s (pos+1) = 'a' && String.unsafe_get s (pos+2) = 'm' && String.unsafe_get s (pos+3) = 'e' then (
                  0
                )
                else (
                  -1
                )
              )
            | _ -> (
                -1
              )
      in
      let i = Yojson.Safe.map_ident p f lb in
      Atdgen_runtime.Oj_run.read_until_field_value p lb;
      (
        match i with
          | 0 ->
            field_name := (
              (
                Atdgen_runtime.Oj_run.read_string
              ) p lb
            );
            bits0 := !bits0 lor 0x1;
          | 1 ->
            field_id := (
              (
                Atdgen_runtime.Oj_run.read_string
              ) p lb
            );
            bits0 := !bits0 lor 0x2;
          | _ -> (
              Yojson.Safe.skip_json p lb
            )
      );
      while true do
        Yojson.Safe.read_space p lb;
        Yojson.Safe.read_object_sep p lb;
        Yojson.Safe.read_space p lb;
        let f =
          fun s pos len ->
            if pos < 0 || len < 0 || pos + len > String.length s then
              invalid_arg "out-of-bounds substring position or length";
            match len with
              | 2 -> (
                  if String.unsafe_get s pos = 'i' && String.unsafe_get s (pos+1) = 'd' then (
                    1
                  )
                  else (
                    -1
                  )
                )
              | 4 -> (
                  if String.unsafe_get s pos = 'n' && String.unsafe_get s (pos+1) = 'a' && String.unsafe_get s (pos+2) = 'm' && String.unsafe_get s (pos+3) = 'e' then (
                    0
                  )
                  else (
                    -1
                  )
                )
              | _ -> (
                  -1
                )
        in
        let i = Yojson.Safe.map_ident p f lb in
        Atdgen_runtime.Oj_run.read_until_field_value p lb;
        (
          match i with
            | 0 ->
              field_name := (
                (
                  Atdgen_runtime.Oj_run.read_string
                ) p lb
              );
              bits0 := !bits0 lor 0x1;
            | 1 ->
              field_id := (
                (
                  Atdgen_runtime.Oj_run.read_string
                ) p lb
              );
              bits0 := !bits0 lor 0x2;
            | _ -> (
                Yojson.Safe.skip_json p lb
              )
        );
      done;
      assert false;
    with Yojson.End_of_object -> (
        if !bits0 <> 0x3 then Atdgen_runtime.Oj_run.missing_fields p [| !bits0 |] [| "name"; "id" |];
        (
          {
            name = !field_name;
            id = !field_id;
          }
         : neighbor_peer_info)
      )
)
let neighbor_peer_info_of_string s =
  read_neighbor_peer_info (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write_neighbor_info : _ -> neighbor_info -> _ = (
  fun ob x ->
    Bi_outbuf.add_char ob '{';
    let is_first = ref true in
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"node\":";
    (
      write_neighbor_peer_info
    )
      ob x.node;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"port\":";
    (
      write_neighbor_peer_info
    )
      ob x.port;
    Bi_outbuf.add_char ob '}';
)
let string_of_neighbor_info ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_neighbor_info ob x;
  Bi_outbuf.contents ob
let read_neighbor_info = (
  fun p lb ->
    Yojson.Safe.read_space p lb;
    Yojson.Safe.read_lcurl p lb;
    let field_node = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_port = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let bits0 = ref 0 in
    try
      Yojson.Safe.read_space p lb;
      Yojson.Safe.read_object_end lb;
      Yojson.Safe.read_space p lb;
      let f =
        fun s pos len ->
          if pos < 0 || len < 0 || pos + len > String.length s then
            invalid_arg "out-of-bounds substring position or length";
          if len = 4 then (
            match String.unsafe_get s pos with
              | 'n' -> (
                  if String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 'd' && String.unsafe_get s (pos+3) = 'e' then (
                    0
                  )
                  else (
                    -1
                  )
                )
              | 'p' -> (
                  if String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 'r' && String.unsafe_get s (pos+3) = 't' then (
                    1
                  )
                  else (
                    -1
                  )
                )
              | _ -> (
                  -1
                )
          )
          else (
            -1
          )
      in
      let i = Yojson.Safe.map_ident p f lb in
      Atdgen_runtime.Oj_run.read_until_field_value p lb;
      (
        match i with
          | 0 ->
            field_node := (
              (
                read_neighbor_peer_info
              ) p lb
            );
            bits0 := !bits0 lor 0x1;
          | 1 ->
            field_port := (
              (
                read_neighbor_peer_info
              ) p lb
            );
            bits0 := !bits0 lor 0x2;
          | _ -> (
              Yojson.Safe.skip_json p lb
            )
      );
      while true do
        Yojson.Safe.read_space p lb;
        Yojson.Safe.read_object_sep p lb;
        Yojson.Safe.read_space p lb;
        let f =
          fun s pos len ->
            if pos < 0 || len < 0 || pos + len > String.length s then
              invalid_arg "out-of-bounds substring position or length";
            if len = 4 then (
              match String.unsafe_get s pos with
                | 'n' -> (
                    if String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 'd' && String.unsafe_get s (pos+3) = 'e' then (
                      0
                    )
                    else (
                      -1
                    )
                  )
                | 'p' -> (
                    if String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 'r' && String.unsafe_get s (pos+3) = 't' then (
                      1
                    )
                    else (
                      -1
                    )
                  )
                | _ -> (
                    -1
                  )
            )
            else (
              -1
            )
        in
        let i = Yojson.Safe.map_ident p f lb in
        Atdgen_runtime.Oj_run.read_until_field_value p lb;
        (
          match i with
            | 0 ->
              field_node := (
                (
                  read_neighbor_peer_info
                ) p lb
              );
              bits0 := !bits0 lor 0x1;
            | 1 ->
              field_port := (
                (
                  read_neighbor_peer_info
                ) p lb
              );
              bits0 := !bits0 lor 0x2;
            | _ -> (
                Yojson.Safe.skip_json p lb
              )
        );
      done;
      assert false;
    with Yojson.End_of_object -> (
        if !bits0 <> 0x3 then Atdgen_runtime.Oj_run.missing_fields p [| !bits0 |] [| "node"; "port" |];
        (
          {
            node = !field_node;
            port = !field_port;
          }
         : neighbor_info)
      )
)
let neighbor_info_of_string s =
  read_neighbor_info (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write_neighbor : _ -> neighbor -> _ = (
  fun ob x ->
    Bi_outbuf.add_char ob '{';
    let is_first = ref true in
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"src\":";
    (
      write_neighbor_info
    )
      ob x.src;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"dst\":";
    (
      write_neighbor_info
    )
      ob x.dst;
    Bi_outbuf.add_char ob '}';
)
let string_of_neighbor ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_neighbor ob x;
  Bi_outbuf.contents ob
let read_neighbor = (
  fun p lb ->
    Yojson.Safe.read_space p lb;
    Yojson.Safe.read_lcurl p lb;
    let field_src = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_dst = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let bits0 = ref 0 in
    try
      Yojson.Safe.read_space p lb;
      Yojson.Safe.read_object_end lb;
      Yojson.Safe.read_space p lb;
      let f =
        fun s pos len ->
          if pos < 0 || len < 0 || pos + len > String.length s then
            invalid_arg "out-of-bounds substring position or length";
          if len = 3 then (
            match String.unsafe_get s pos with
              | 'd' -> (
                  if String.unsafe_get s (pos+1) = 's' && String.unsafe_get s (pos+2) = 't' then (
                    1
                  )
                  else (
                    -1
                  )
                )
              | 's' -> (
                  if String.unsafe_get s (pos+1) = 'r' && String.unsafe_get s (pos+2) = 'c' then (
                    0
                  )
                  else (
                    -1
                  )
                )
              | _ -> (
                  -1
                )
          )
          else (
            -1
          )
      in
      let i = Yojson.Safe.map_ident p f lb in
      Atdgen_runtime.Oj_run.read_until_field_value p lb;
      (
        match i with
          | 0 ->
            field_src := (
              (
                read_neighbor_info
              ) p lb
            );
            bits0 := !bits0 lor 0x1;
          | 1 ->
            field_dst := (
              (
                read_neighbor_info
              ) p lb
            );
            bits0 := !bits0 lor 0x2;
          | _ -> (
              Yojson.Safe.skip_json p lb
            )
      );
      while true do
        Yojson.Safe.read_space p lb;
        Yojson.Safe.read_object_sep p lb;
        Yojson.Safe.read_space p lb;
        let f =
          fun s pos len ->
            if pos < 0 || len < 0 || pos + len > String.length s then
              invalid_arg "out-of-bounds substring position or length";
            if len = 3 then (
              match String.unsafe_get s pos with
                | 'd' -> (
                    if String.unsafe_get s (pos+1) = 's' && String.unsafe_get s (pos+2) = 't' then (
                      1
                    )
                    else (
                      -1
                    )
                  )
                | 's' -> (
                    if String.unsafe_get s (pos+1) = 'r' && String.unsafe_get s (pos+2) = 'c' then (
                      0
                    )
                    else (
                      -1
                    )
                  )
                | _ -> (
                    -1
                  )
            )
            else (
              -1
            )
        in
        let i = Yojson.Safe.map_ident p f lb in
        Atdgen_runtime.Oj_run.read_until_field_value p lb;
        (
          match i with
            | 0 ->
              field_src := (
                (
                  read_neighbor_info
                ) p lb
              );
              bits0 := !bits0 lor 0x1;
            | 1 ->
              field_dst := (
                (
                  read_neighbor_info
                ) p lb
              );
              bits0 := !bits0 lor 0x2;
            | _ -> (
                Yojson.Safe.skip_json p lb
              )
        );
      done;
      assert false;
    with Yojson.End_of_object -> (
        if !bits0 <> 0x3 then Atdgen_runtime.Oj_run.missing_fields p [| !bits0 |] [| "src"; "dst" |];
        (
          {
            src = !field_src;
            dst = !field_dst;
          }
         : neighbor)
      )
)
let neighbor_of_string s =
  read_neighbor (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write_disk_status : _ -> disk_status -> _ = (
  fun ob x ->
    Bi_outbuf.add_char ob '{';
    let is_first = ref true in
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"mount_point\":";
    (
      Yojson.Safe.write_string
    )
      ob x.mount_point;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"total\":";
    (
      Yojson.Safe.write_std_float
    )
      ob x.total;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"free\":";
    (
      Yojson.Safe.write_std_float
    )
      ob x.free;
    Bi_outbuf.add_char ob '}';
)
let string_of_disk_status ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_disk_status ob x;
  Bi_outbuf.contents ob
let read_disk_status = (
  fun p lb ->
    Yojson.Safe.read_space p lb;
    Yojson.Safe.read_lcurl p lb;
    let field_mount_point = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_total = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_free = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let bits0 = ref 0 in
    try
      Yojson.Safe.read_space p lb;
      Yojson.Safe.read_object_end lb;
      Yojson.Safe.read_space p lb;
      let f =
        fun s pos len ->
          if pos < 0 || len < 0 || pos + len > String.length s then
            invalid_arg "out-of-bounds substring position or length";
          match len with
            | 4 -> (
                if String.unsafe_get s pos = 'f' && String.unsafe_get s (pos+1) = 'r' && String.unsafe_get s (pos+2) = 'e' && String.unsafe_get s (pos+3) = 'e' then (
                  2
                )
                else (
                  -1
                )
              )
            | 5 -> (
                if String.unsafe_get s pos = 't' && String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 't' && String.unsafe_get s (pos+3) = 'a' && String.unsafe_get s (pos+4) = 'l' then (
                  1
                )
                else (
                  -1
                )
              )
            | 11 -> (
                if String.unsafe_get s pos = 'm' && String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 'u' && String.unsafe_get s (pos+3) = 'n' && String.unsafe_get s (pos+4) = 't' && String.unsafe_get s (pos+5) = '_' && String.unsafe_get s (pos+6) = 'p' && String.unsafe_get s (pos+7) = 'o' && String.unsafe_get s (pos+8) = 'i' && String.unsafe_get s (pos+9) = 'n' && String.unsafe_get s (pos+10) = 't' then (
                  0
                )
                else (
                  -1
                )
              )
            | _ -> (
                -1
              )
      in
      let i = Yojson.Safe.map_ident p f lb in
      Atdgen_runtime.Oj_run.read_until_field_value p lb;
      (
        match i with
          | 0 ->
            field_mount_point := (
              (
                Atdgen_runtime.Oj_run.read_string
              ) p lb
            );
            bits0 := !bits0 lor 0x1;
          | 1 ->
            field_total := (
              (
                Atdgen_runtime.Oj_run.read_number
              ) p lb
            );
            bits0 := !bits0 lor 0x2;
          | 2 ->
            field_free := (
              (
                Atdgen_runtime.Oj_run.read_number
              ) p lb
            );
            bits0 := !bits0 lor 0x4;
          | _ -> (
              Yojson.Safe.skip_json p lb
            )
      );
      while true do
        Yojson.Safe.read_space p lb;
        Yojson.Safe.read_object_sep p lb;
        Yojson.Safe.read_space p lb;
        let f =
          fun s pos len ->
            if pos < 0 || len < 0 || pos + len > String.length s then
              invalid_arg "out-of-bounds substring position or length";
            match len with
              | 4 -> (
                  if String.unsafe_get s pos = 'f' && String.unsafe_get s (pos+1) = 'r' && String.unsafe_get s (pos+2) = 'e' && String.unsafe_get s (pos+3) = 'e' then (
                    2
                  )
                  else (
                    -1
                  )
                )
              | 5 -> (
                  if String.unsafe_get s pos = 't' && String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 't' && String.unsafe_get s (pos+3) = 'a' && String.unsafe_get s (pos+4) = 'l' then (
                    1
                  )
                  else (
                    -1
                  )
                )
              | 11 -> (
                  if String.unsafe_get s pos = 'm' && String.unsafe_get s (pos+1) = 'o' && String.unsafe_get s (pos+2) = 'u' && String.unsafe_get s (pos+3) = 'n' && String.unsafe_get s (pos+4) = 't' && String.unsafe_get s (pos+5) = '_' && String.unsafe_get s (pos+6) = 'p' && String.unsafe_get s (pos+7) = 'o' && String.unsafe_get s (pos+8) = 'i' && String.unsafe_get s (pos+9) = 'n' && String.unsafe_get s (pos+10) = 't' then (
                    0
                  )
                  else (
                    -1
                  )
                )
              | _ -> (
                  -1
                )
        in
        let i = Yojson.Safe.map_ident p f lb in
        Atdgen_runtime.Oj_run.read_until_field_value p lb;
        (
          match i with
            | 0 ->
              field_mount_point := (
                (
                  Atdgen_runtime.Oj_run.read_string
                ) p lb
              );
              bits0 := !bits0 lor 0x1;
            | 1 ->
              field_total := (
                (
                  Atdgen_runtime.Oj_run.read_number
                ) p lb
              );
              bits0 := !bits0 lor 0x2;
            | 2 ->
              field_free := (
                (
                  Atdgen_runtime.Oj_run.read_number
                ) p lb
              );
              bits0 := !bits0 lor 0x4;
            | _ -> (
                Yojson.Safe.skip_json p lb
              )
        );
      done;
      assert false;
    with Yojson.End_of_object -> (
        if !bits0 <> 0x7 then Atdgen_runtime.Oj_run.missing_fields p [| !bits0 |] [| "mount_point"; "total"; "free" |];
        (
          {
            mount_point = !field_mount_point;
            total = !field_total;
            free = !field_free;
          }
         : disk_status)
      )
)
let disk_status_of_string s =
  read_disk_status (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write__2 = (
  Atdgen_runtime.Oj_run.write_list (
    write_neighbor
  )
)
let string_of__2 ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write__2 ob x;
  Bi_outbuf.contents ob
let read__2 = (
  Atdgen_runtime.Oj_run.read_list (
    read_neighbor
  )
)
let _2_of_string s =
  read__2 (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write__1 = (
  Atdgen_runtime.Oj_run.write_list (
    write_disk_status
  )
)
let string_of__1 ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write__1 ob x;
  Bi_outbuf.contents ob
let read__1 = (
  Atdgen_runtime.Oj_run.read_list (
    read_disk_status
  )
)
let _1_of_string s =
  read__1 (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write_node_status : _ -> node_status -> _ = (
  fun ob x ->
    Bi_outbuf.add_char ob '{';
    let is_first = ref true in
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"uuid\":";
    (
      Yojson.Safe.write_string
    )
      ob x.uuid;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"ram\":";
    (
      write_ram_status
    )
      ob x.ram;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"disk\":";
    (
      write__1
    )
      ob x.disk;
    if !is_first then
      is_first := false
    else
      Bi_outbuf.add_char ob ',';
    Bi_outbuf.add_string ob "\"neighbors\":";
    (
      write__2
    )
      ob x.neighbors;
    Bi_outbuf.add_char ob '}';
)
let string_of_node_status ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_node_status ob x;
  Bi_outbuf.contents ob
let read_node_status = (
  fun p lb ->
    Yojson.Safe.read_space p lb;
    Yojson.Safe.read_lcurl p lb;
    let field_uuid = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_ram = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_disk = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let field_neighbors = ref (Obj.magic (Sys.opaque_identity 0.0)) in
    let bits0 = ref 0 in
    try
      Yojson.Safe.read_space p lb;
      Yojson.Safe.read_object_end lb;
      Yojson.Safe.read_space p lb;
      let f =
        fun s pos len ->
          if pos < 0 || len < 0 || pos + len > String.length s then
            invalid_arg "out-of-bounds substring position or length";
          match len with
            | 3 -> (
                if String.unsafe_get s pos = 'r' && String.unsafe_get s (pos+1) = 'a' && String.unsafe_get s (pos+2) = 'm' then (
                  1
                )
                else (
                  -1
                )
              )
            | 4 -> (
                match String.unsafe_get s pos with
                  | 'd' -> (
                      if String.unsafe_get s (pos+1) = 'i' && String.unsafe_get s (pos+2) = 's' && String.unsafe_get s (pos+3) = 'k' then (
                        2
                      )
                      else (
                        -1
                      )
                    )
                  | 'u' -> (
                      if String.unsafe_get s (pos+1) = 'u' && String.unsafe_get s (pos+2) = 'i' && String.unsafe_get s (pos+3) = 'd' then (
                        0
                      )
                      else (
                        -1
                      )
                    )
                  | _ -> (
                      -1
                    )
              )
            | 9 -> (
                if String.unsafe_get s pos = 'n' && String.unsafe_get s (pos+1) = 'e' && String.unsafe_get s (pos+2) = 'i' && String.unsafe_get s (pos+3) = 'g' && String.unsafe_get s (pos+4) = 'h' && String.unsafe_get s (pos+5) = 'b' && String.unsafe_get s (pos+6) = 'o' && String.unsafe_get s (pos+7) = 'r' && String.unsafe_get s (pos+8) = 's' then (
                  3
                )
                else (
                  -1
                )
              )
            | _ -> (
                -1
              )
      in
      let i = Yojson.Safe.map_ident p f lb in
      Atdgen_runtime.Oj_run.read_until_field_value p lb;
      (
        match i with
          | 0 ->
            field_uuid := (
              (
                Atdgen_runtime.Oj_run.read_string
              ) p lb
            );
            bits0 := !bits0 lor 0x1;
          | 1 ->
            field_ram := (
              (
                read_ram_status
              ) p lb
            );
            bits0 := !bits0 lor 0x2;
          | 2 ->
            field_disk := (
              (
                read__1
              ) p lb
            );
            bits0 := !bits0 lor 0x4;
          | 3 ->
            field_neighbors := (
              (
                read__2
              ) p lb
            );
            bits0 := !bits0 lor 0x8;
          | _ -> (
              Yojson.Safe.skip_json p lb
            )
      );
      while true do
        Yojson.Safe.read_space p lb;
        Yojson.Safe.read_object_sep p lb;
        Yojson.Safe.read_space p lb;
        let f =
          fun s pos len ->
            if pos < 0 || len < 0 || pos + len > String.length s then
              invalid_arg "out-of-bounds substring position or length";
            match len with
              | 3 -> (
                  if String.unsafe_get s pos = 'r' && String.unsafe_get s (pos+1) = 'a' && String.unsafe_get s (pos+2) = 'm' then (
                    1
                  )
                  else (
                    -1
                  )
                )
              | 4 -> (
                  match String.unsafe_get s pos with
                    | 'd' -> (
                        if String.unsafe_get s (pos+1) = 'i' && String.unsafe_get s (pos+2) = 's' && String.unsafe_get s (pos+3) = 'k' then (
                          2
                        )
                        else (
                          -1
                        )
                      )
                    | 'u' -> (
                        if String.unsafe_get s (pos+1) = 'u' && String.unsafe_get s (pos+2) = 'i' && String.unsafe_get s (pos+3) = 'd' then (
                          0
                        )
                        else (
                          -1
                        )
                      )
                    | _ -> (
                        -1
                      )
                )
              | 9 -> (
                  if String.unsafe_get s pos = 'n' && String.unsafe_get s (pos+1) = 'e' && String.unsafe_get s (pos+2) = 'i' && String.unsafe_get s (pos+3) = 'g' && String.unsafe_get s (pos+4) = 'h' && String.unsafe_get s (pos+5) = 'b' && String.unsafe_get s (pos+6) = 'o' && String.unsafe_get s (pos+7) = 'r' && String.unsafe_get s (pos+8) = 's' then (
                    3
                  )
                  else (
                    -1
                  )
                )
              | _ -> (
                  -1
                )
        in
        let i = Yojson.Safe.map_ident p f lb in
        Atdgen_runtime.Oj_run.read_until_field_value p lb;
        (
          match i with
            | 0 ->
              field_uuid := (
                (
                  Atdgen_runtime.Oj_run.read_string
                ) p lb
              );
              bits0 := !bits0 lor 0x1;
            | 1 ->
              field_ram := (
                (
                  read_ram_status
                ) p lb
              );
              bits0 := !bits0 lor 0x2;
            | 2 ->
              field_disk := (
                (
                  read__1
                ) p lb
              );
              bits0 := !bits0 lor 0x4;
            | 3 ->
              field_neighbors := (
                (
                  read__2
                ) p lb
              );
              bits0 := !bits0 lor 0x8;
            | _ -> (
                Yojson.Safe.skip_json p lb
              )
        );
      done;
      assert false;
    with Yojson.End_of_object -> (
        if !bits0 <> 0xf then Atdgen_runtime.Oj_run.missing_fields p [| !bits0 |] [| "uuid"; "ram"; "disk"; "neighbors" |];
        (
          {
            uuid = !field_uuid;
            ram = !field_ram;
            disk = !field_disk;
            neighbors = !field_neighbors;
          }
         : node_status)
      )
)
let node_status_of_string s =
  read_node_status (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let write_json = (
  Yojson.Safe.write_json
)
let string_of_json ?(len = 1024) x =
  let ob = Bi_outbuf.create len in
  write_json ob x;
  Bi_outbuf.contents ob
let read_json = (
  Yojson.Safe.read_json
)
let json_of_string s =
  read_json (Yojson.Safe.init_lexer ()) (Lexing.from_string s)
let create_ram_status 
  ~total
  ~free
  () : ram_status =
  {
    total = total;
    free = free;
  }
let create_neighbor_peer_info 
  ~name
  ~id
  () : neighbor_peer_info =
  {
    name = name;
    id = id;
  }
let create_neighbor_info 
  ~node
  ~port
  () : neighbor_info =
  {
    node = node;
    port = port;
  }
let create_neighbor 
  ~src
  ~dst
  () : neighbor =
  {
    src = src;
    dst = dst;
  }
let create_disk_status 
  ~mount_point
  ~total
  ~free
  () : disk_status =
  {
    mount_point = mount_point;
    total = total;
    free = free;
  }
let create_node_status 
  ~uuid
  ~ram
  ~disk
  ~neighbors
  () : node_status =
  {
    uuid = uuid;
    ram = ram;
    disk = disk;
    neighbors = neighbors;
  }
