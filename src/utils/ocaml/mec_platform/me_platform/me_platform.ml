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
open Mp1
open Mm5
(* open Lwt.Infix *)
(* open Fos_im *)



module MVar = Apero.MVar_lwt


let listen_address = Unix.inet_addr_any
let backlog = 10
let max_buf_len = 64 * 1024

let mep_id = Arg.(value & opt string "" & info ["i"; "mec-id"] ~docv:"UUID|STRING"
                    ~doc:("If set, use this string to generate the MECmPlaform unique identifier. If the string has UUID format, just uses it as identifier. "^
                          "Otherwise,  uses this string to generate an UUID in a determinstic way (i.e. a same string always generates the same UUID.
                                   If this option is not set, generates a random UUID."))


let configuration_path = Arg.(value & opt string "/etc/fos/mec_platfrom.json" & info ["c"; "conf"] ~docv:"Path to configuration"
                                ~doc:"Absolute path to configuration file")


let setup_log style_renderer level =
  Fmt_tty.setup_std_outputs ?style_renderer ();
  Logs.set_level level;
  Logs.set_reporter (Logs_fmt.reporter ());
  ()


let run_platform mep_id configuration_path =
  try%lwt
    ignore mep_id; ignore configuration_path;
    let%lwt core = MEC_Core.create (Apero.Option.get @@ Apero_net.Locator.of_string "tcp/127.0.0.1:7887") in
    let%lwt mm5 = Mm5.create "127.0.0.1" "/exampleAPI/mm5/v1/" 8091 core in
    let%lwt mp1 = Mp1.create "127.0.0.1" "/exampleAPI/mp1/v1/" 8081 core in
    Lwt.join [MEC_Core.start core; Mp1.start mp1; Mm5.start mm5]
  with
  (* | YException e  ->
     Logs_lwt.err (fun m -> m "Exception %s raised:\n%s" (show_yerror e) (Printexc.get_backtrace ())) >> Lwt.return_unit *)
  | exn ->
    let%lwt _ = Logs_lwt.err (fun m -> m "Exception %s raised:\n%s" (Printexc.to_string exn) (Printexc.get_backtrace ()))
    in Lwt.return_unit


let run mep_id configuration_path style_renderer level =
  setup_log style_renderer level;
  (* Note: by default the Lwt.async_exception_hook do "exit 2" when an exception is raised in a canceled Lwt task.
     We rather force it to log and ignore the exception to avoid crashes (as it occurs randomly within cohttp at connection closure).  *)
  Lwt.async_exception_hook := (fun exn ->
      ignore @@ Logs.debug (fun m -> m "Exception caught in Lwt.async_exception_hook: %s\n%s" (Printexc.to_string exn) (Printexc.get_backtrace ())));
  Lwt_main.run @@ run_platform mep_id configuration_path


let () =
  Printexc.record_backtrace true;
  Lwt_engine.set (new Lwt_engine.libev ());
  let env = Arg.env_var "YAKSD_VERBOSITY" in
  let _ = Term.(eval (const run $ mep_id $ configuration_path $ Fmt_cli.style_renderer () $ Logs_cli.level ~env (), Term.info "Yaks daemon")) in  ()
