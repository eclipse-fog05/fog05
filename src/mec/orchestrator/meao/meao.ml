(*********************************************************************************
 * Copyright (c) 2018 ADLINK Technology Inc.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Apache Software License 2.0
 * which is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
 * Contributors: 1
 *   Gabriele Baldoni (gabriele (dot) baldoni (at) adlinktech (dot) com )
 *********************************************************************************)

open Cmdliner
open Me_core
open Mm1
(* open Mm5 *)
(* open Lwt.Infix *)
(* open Fos_im *)
open FIMPlugin
open Lwt.Infix


module MVar = Apero.MVar_lwt


let listen_address = Unix.inet_addr_any
let backlog = 10
let max_buf_len = 64 * 1024

let configuration_path = Arg.(value & opt string "/etc/fos/mec_platfrom.json" & info ["c"; "conf"] ~docv:"Path to configuration"
                                ~doc:"Absolute path to configuration file")

let fim_plugin = Arg.(value & opt string "" & info ["p"; "plugin"] ~docv:"Path to fim plugin"
                        ~doc:"Absolute path to plugin file")


let setup_log style_renderer level =
  Fmt_tty.setup_std_outputs ?style_renderer ();
  Logs.set_level level;
  Logs.set_reporter (Logs_fmt.reporter ());
  ()


let get_yaks_locator () =
  let host =
    try
      Unix.getenv "YAKS_HOST" |> Unix.gethostbyname
      |> fun x -> Array.get x.h_addr_list 0 |>
                  Unix.string_of_inet_addr
    with Not_found -> "127.0.0.1"
  in
  let port =
    try
      Unix.getenv "YAKS_PORT"
    with Not_found -> "7887"
  in
  Logs.debug (fun m -> m "YAKS AT %s:%s" host port);
  let strloc = Printf.sprintf "tcp/%s:%s" host port in
  Apero_net.Locator.of_string strloc |> Apero.Option.get

let run_platform configuration_path fim_plugin =
  ignore configuration_path;
  ignore fim_plugin;
  Logs.debug (fun m -> m "Started!\n" );
  let load_plugin fname =
    let fname = Dynlink.adapt_filename fname in
    match Sys.file_exists fname with
    | true ->
      (try
         Dynlink.loadfile fname;
         true
       with
       | Dynlink.Error err ->
         Logs.err (fun m -> m "[MEAO] error while loading FIM Plugin %s" (Dynlink.error_message err));
         false)
    | false ->
      Logs.err (fun m -> m "[MEAO] Plugin file does not esist");
      false
  in

  try%lwt

    Findlib.init ();

    let%lwt core = MEAO.create (get_yaks_locator ()) in
    let%lwt ro = RO.create (get_yaks_locator ())  core in
    (* let%lwt _ = RO.add_fim_conn "fos" fos_conn ro in *)
    let%lwt mm1 = Mm1.create "0.0.0.0" "/exampleAPI/mm1/v1/" 8071 core in

    (match fim_plugin with
     | "" -> Lwt.return_unit
     | _ ->
       (* dynamic loading packages needed by plugin *)
       Fl_dynload.load_packages ["fos-fim-api"];
       let r = load_plugin fim_plugin in
       (match r with
        | true ->
          let module M = (val FIMPlugin.get_plugin () : FIMPlugin) in
          let fos_conn = M.make "tcp/127.0.0.1:7887" "" "" (Fos_im.JSON.create_empty ()) in
          let%lwt _ = RO.add_fim_conn "fos" fos_conn ro in
          Logs.debug (fun m -> m "FIM Plugin Loaded!" );
          Lwt.return_unit
        | false -> Lwt.return_unit))
    >>= fun  _ ->
    Lwt.join [MEAO.start core; Mm1.start mm1; RO.start ro]
  (*
     let%lwt mp1 = Mp1.create "127.0.0.1" "/exampleAPI/mp1/v1/" 8081 core in
     Lwt.join [MEC_Core.start core; Mp1.start mp1; Mm5.start mm5] *)
  with
  (* | YException e  ->
     Logs_lwt.err (fun m -> m "Exception %s raised:\n%s" (show_yerror e) (Printexc.get_backtrace ())) >> Lwt.return_unit *)
  | exn ->
    let%lwt _ = Logs_lwt.err (fun m -> m "Exception %s raised:\n%s" (Printexc.to_string exn) (Printexc.get_backtrace ()))
    in Lwt.return_unit


let run configuration_path fim_plugin style_renderer level =
  setup_log style_renderer level;
  (* Note: by default the Lwt.async_exception_hook do "exit 2" when an exception is raised in a canceled Lwt task.
     We rather force it to log and ignore the exception to avoid crashes (as it occurs randomly within cohttp at connection closure).  *)
  Lwt.async_exception_hook := (fun exn ->
      Logs.debug (fun m -> m "Exception caught in Lwt.async_exception_hook: %s\n%s" (Printexc.to_string exn) (Printexc.get_backtrace ())));
  Lwt_main.run @@ run_platform configuration_path fim_plugin


let () =
  Printexc.record_backtrace true;
  Lwt_engine.set (new Lwt_engine.libev ());
  let env = Arg.env_var "MEAO_VERBOSITY" in
  let _ = Term.(eval (const run $ configuration_path $ fim_plugin $ Fmt_cli.style_renderer () $ Logs_cli.level ~env (), Term.info "Yaks daemon")) in  ()
