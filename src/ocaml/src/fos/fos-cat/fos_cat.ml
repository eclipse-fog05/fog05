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
 *   Gabriele Baldoni (gabriele (dot) baldoni (at) adlinktech (dot) com ) - OCaml implementation
 *********************************************************************************)

open Yaks_ocaml
open Lwt.Infix

let usage () = ignore( print_endline "USAGE:\n\t fos-cat <yaks_address> <yaks_port>\n" )

let register_handlers completer () =
  Lwt_unix.on_signal Sys.sigint (
    fun _ -> Lwt.wakeup_later completer ())


let observer data = 
  Lwt_list.iter_p (fun (k,v) -> 
      Lwt_io.printf ">>>> [FOS-CAT] K %s - V: %s\n"  (Yaks_types.Path.to_string k) (Yaks_types.Value.to_string v) 
    ) data



let main argv = 
  let addr = Array.get argv 1 in
  let port = Array.get argv 2 in 
  let locator = Apero.Option.get @@ Apero_net.Locator.of_string @@ Printf.sprintf "tcp/%s:%s" addr port in
  let%lwt api = Yaks.login locator Apero.Properties.empty in
  ignore @@ Lwt_io.printf "<<<< [FOS-CAT] Creating access on %s\n"  "/afos";
  Yaks.workspace (Yaks_types.Path.of_string "/afos") api
  >>= fun access -> 
  ignore @@ Lwt_io.printf "<<<< [FOS-CAT] Subscribing to %s\n"  "/afos/**";
  Yaks.Workspace.subscribe ~listener:observer (Yaks_types.Selector.of_string "/afos/**") access
  >>= fun _ -> 
  ignore @@ Lwt_io.printf "<<<< [FOS-CAT] Creating access on %s\n"  "/dfos";
  Yaks.workspace (Yaks_types.Path.of_string "/dfos") api
  >>= fun daccess -> 
  ignore @@ Lwt_io.printf "<<<< [FOS-CAT] Subscribing to %s\n"  "/dfos/**";
  Yaks.Workspace.subscribe ~listener:observer (Yaks_types.Selector.of_string "/dfos/**") daccess
  >>= fun _ ->
  let prom,c = Lwt.wait () in 
  let _ = register_handlers c () in
  Lwt.join [prom] 
  (* >>= fun _ -> Yaks.dispose_access access api 
     >>= fun _ -> Yaks.dispose_access daccess api *)
  >>= fun _ -> Yaks.logout api
  >>= fun _ -> Lwt_io.printf "Bye!\n"


let _ =
  let argv = Sys.argv in
  let level = Apero.Result.get @@ Logs.level_of_string "error" in
  Logs.set_level level;
  Logs.set_reporter (Logs_fmt.reporter ());
  Lwt_main.run (main argv)



