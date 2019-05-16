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

val write_ram_status :
  Bi_outbuf.t -> ram_status -> unit
  (** Output a JSON value of type {!ram_status}. *)

val string_of_ram_status :
  ?len:int -> ram_status -> string
  (** Serialize a value of type {!ram_status}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_ram_status :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> ram_status
  (** Input JSON data of type {!ram_status}. *)

val ram_status_of_string :
  string -> ram_status
  (** Deserialize JSON data of type {!ram_status}. *)

val create_ram_status :
  total: float ->
  free: float ->
  unit -> ram_status
  (** Create a record of type {!ram_status}. *)


val write_neighbor_peer_info :
  Bi_outbuf.t -> neighbor_peer_info -> unit
  (** Output a JSON value of type {!neighbor_peer_info}. *)

val string_of_neighbor_peer_info :
  ?len:int -> neighbor_peer_info -> string
  (** Serialize a value of type {!neighbor_peer_info}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_neighbor_peer_info :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> neighbor_peer_info
  (** Input JSON data of type {!neighbor_peer_info}. *)

val neighbor_peer_info_of_string :
  string -> neighbor_peer_info
  (** Deserialize JSON data of type {!neighbor_peer_info}. *)

val create_neighbor_peer_info :
  name: string ->
  id: string ->
  unit -> neighbor_peer_info
  (** Create a record of type {!neighbor_peer_info}. *)


val write_neighbor_info :
  Bi_outbuf.t -> neighbor_info -> unit
  (** Output a JSON value of type {!neighbor_info}. *)

val string_of_neighbor_info :
  ?len:int -> neighbor_info -> string
  (** Serialize a value of type {!neighbor_info}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_neighbor_info :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> neighbor_info
  (** Input JSON data of type {!neighbor_info}. *)

val neighbor_info_of_string :
  string -> neighbor_info
  (** Deserialize JSON data of type {!neighbor_info}. *)

val create_neighbor_info :
  node: neighbor_peer_info ->
  port: neighbor_peer_info ->
  unit -> neighbor_info
  (** Create a record of type {!neighbor_info}. *)


val write_neighbor :
  Bi_outbuf.t -> neighbor -> unit
  (** Output a JSON value of type {!neighbor}. *)

val string_of_neighbor :
  ?len:int -> neighbor -> string
  (** Serialize a value of type {!neighbor}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_neighbor :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> neighbor
  (** Input JSON data of type {!neighbor}. *)

val neighbor_of_string :
  string -> neighbor
  (** Deserialize JSON data of type {!neighbor}. *)

val create_neighbor :
  src: neighbor_info ->
  dst: neighbor_info ->
  unit -> neighbor
  (** Create a record of type {!neighbor}. *)


val write_disk_status :
  Bi_outbuf.t -> disk_status -> unit
  (** Output a JSON value of type {!disk_status}. *)

val string_of_disk_status :
  ?len:int -> disk_status -> string
  (** Serialize a value of type {!disk_status}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_disk_status :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> disk_status
  (** Input JSON data of type {!disk_status}. *)

val disk_status_of_string :
  string -> disk_status
  (** Deserialize JSON data of type {!disk_status}. *)

val create_disk_status :
  mount_point: string ->
  total: float ->
  free: float ->
  unit -> disk_status
  (** Create a record of type {!disk_status}. *)


val write_node_status :
  Bi_outbuf.t -> node_status -> unit
  (** Output a JSON value of type {!node_status}. *)

val string_of_node_status :
  ?len:int -> node_status -> string
  (** Serialize a value of type {!node_status}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_node_status :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> node_status
  (** Input JSON data of type {!node_status}. *)

val node_status_of_string :
  string -> node_status
  (** Deserialize JSON data of type {!node_status}. *)

val create_node_status :
  uuid: string ->
  ram: ram_status ->
  disk: disk_status list ->
  neighbors: neighbor list ->
  unit -> node_status
  (** Create a record of type {!node_status}. *)


val write_json :
  Bi_outbuf.t -> json -> unit
  (** Output a JSON value of type {!json}. *)

val string_of_json :
  ?len:int -> json -> string
  (** Serialize a value of type {!json}
      into a JSON string.
      @param len specifies the initial length
                 of the buffer used internally.
                 Default: 1024. *)

val read_json :
  Yojson.Safe.lexer_state -> Lexing.lexbuf -> json
  (** Input JSON data of type {!json}. *)

val json_of_string :
  string -> json
  (** Deserialize JSON data of type {!json}. *)


