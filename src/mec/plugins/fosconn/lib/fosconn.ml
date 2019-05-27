open Fos_fim_api
(* open Fos_im.Errors *)
open Lwt.Infix
open FIMPlugin
open Fos_im.Errors
open Fos_im

module FOSConn(C : FIM.Conf) : FIM.FIMConn = struct

  type t = {
    client : Fos_fim_api.api;
    conf : Fosconn_types.configuration
  }


  let self = ref None


  (* constants *)

  let max_vlan_range = 0,4096
  (* let max_vxlan_range = 0,16777215 *)

  (* utils *)



  let l_diff l1 l2 =
    List.filter (fun x -> not (List.mem x l2)) l1

  let rec gen_ids low up l =
    match low>up with
    | true -> l
    | false -> gen_ids (low+1) up l @ [low]

  let get_vlan_id () =
    let self = Apero.Option.get !self in
    let%lwt nets = Network.list_networks self.client in
    let%lwt used_ids = Lwt_list.filter_map_p (fun (e:FTypes.virtual_network) -> Lwt.return e.vlan_id) nets in
    let conf_ids = Apero.Option.get_or_default self.conf.vlan_range max_vlan_range |> fun (f,l) ->  gen_ids f l [] in
    let ids = l_diff conf_ids used_ids in
    Lwt.return @@ List.hd ids



  (*  *)


  let connect () =
    let%lwt x = FIMAPI.connect ~locator:(Apero.Option.get (Apero_net.Locator.of_string C.url)) ~sysid:"0" ~tenantid:"0" () in
    Random.self_init ();
    self := Some {client  = x; conf = Fosconn_types.configuration_of_string @@ Yojson.Safe.to_string C.configuration};
    Lwt.return_unit

  let check_connectivity () =
    Logs.debug (fun m -> m "[FOSConn] - Check connectivity");
    let self = Apero.Option.get !self in
    match%lwt Node.list self.client with
    | [] -> Lwt.fail @@ MEException (`InternalError (`Msg ("Unable to reach the FIM")))
    | _ -> Lwt.return_unit

  let new_network ~net_name ~net_type ~ip_profile ~shared ~vlan =
    let self = Apero.Option.get !self in
    let ip_profile = match ip_profile with
      | Some ipp -> Yojson.Safe.to_string ipp |> Fos_im.FTypes.address_information_of_string |> fun x -> Some x
      | None -> None
    in
    ignore shared;
    (* net_type = | BRIDGE | DATA | PTP *)
    let net_id = Apero.Uuid.make () |> Apero.Uuid.to_string in
    let%lwt desc = (match net_type with
        | "data" ->
          let%lwt vlan_id = (match vlan with
              | Some vlanid ->
                Lwt.return vlanid
              | None ->
                get_vlan_id ())
          in
          Logs.debug (fun m -> m "[FOSConn] - New network has VLAN ID: %d" vlan_id);
          let desc = FTypes.{uuid = net_id; name=net_name; net_type=`ELAN; is_mgmt=false; ip_configuration=ip_profile; overlay= Some false; vlan_id = Some vlan_id; vni= None; face=None; mcast_addr=None} in
          Lwt.return desc
        | "bridge" ->
          Logs.debug (fun m -> m "[FOSConn] - New network is an overlay network");
          let desc = FTypes.{uuid = net_id; name=net_name; net_type=`ELAN; is_mgmt=false; ip_configuration=ip_profile; overlay= Some true; vlan_id = None; vni= None; face=None; mcast_addr=None} in
          Lwt.return desc
        | "ptp" ->
          (* PTP can be used for SFC *)
          Logs.err (fun m -> m "[FOSConn] - Network type implemented %s" net_type);
          Lwt.fail @@ MEException (`InternalError (`Msg ("Network type not recognized")))
        | _ ->
          Logs.err (fun m -> m "[FOSConn] - Network type not recognized %s" net_type);
          Lwt.fail @@ MEException (`InternalError (`Msg ("Network type not recognized"))))
    in
    Logs.debug (fun m -> m "[FOSConn] - New network %s : %s " net_name net_type);
    match%lwt Network.add_network desc self.client with
    | true  -> Lwt.return net_id
    | false -> Lwt.fail @@ MEException (`InternalError (`Msg ("Unable to create network")))


  let get_network_list () =
    Logs.debug (fun m -> m "[FOSConn] - Network list");
    let self = Apero.Option.get !self in
    let%lwt ids = Network.list_networks self.client >>= Lwt_list.map_p (fun (e:FTypes.virtual_network) -> Lwt.return e.uuid) in
    Lwt.return ids

  let get_network net_id =
    Logs.debug (fun m -> m "[FOSConn] - Get network %s" net_id);
    let self = Apero.Option.get !self in
    let%lwt ninfo = Network.list_networks self.client >>= Lwt_list.filter_p (fun( x:FTypes.virtual_network) -> Lwt.return @@ (x.uuid = net_id)) >>= fun x -> Lwt.return @@ List.hd x in
    Lwt.return (FTypes.string_of_virtual_network ninfo |> Yojson.Safe.from_string)

  let delete_network net_id =
    Logs.debug (fun m -> m "[FOSConn] - Delete network %s" net_id);
    let self = Apero.Option.get !self in
    match%lwt Network.remove_network net_id self.client with
    | true -> Lwt.return net_id
    | false -> Lwt.fail @@ MEException (`InternalError (`Msg ("Unable to remove network")))

  let refresh_nets_status net_list =
    Logs.debug (fun m -> m "[FOSConn] - Refresh nets");
    Lwt_list.map_p (fun x -> get_network x) net_list

  let get_flavor flv_id =
    let self = Apero.Option.get !self in
    Logs.debug (fun m -> m "[FOSConn] - Get flavor %s" flv_id);
    let%lwt finfo = Flavor.list self.client >>= Lwt_list.filter_p (fun( x:FDU.computational_requirements) -> Lwt.return @@ ((Apero.Option.get x.uuid) = flv_id)) >>= fun x -> Lwt.return @@ List.hd x in
    Lwt.return (FDU.string_of_computational_requirements finfo)

  let new_flavor flavor_data =
    let self = Apero.Option.get !self in
    Logs.debug (fun m -> m "[FOSConn] - New flavor");
    let flavor_data = Yojson.Safe.to_string flavor_data |> FDU.computational_requirements_of_string in
    Flavor.add flavor_data self.client

  let delete_flavor flv_id =
    let self = Apero.Option.get !self in
    Logs.debug (fun m -> m "[FOSConn] - Delete flavor %s" flv_id);
    Flavor.remove flv_id self.client

  let new_image image_data =
    let self = Apero.Option.get !self in
    ignore image_data;
    Logs.debug (fun m -> m "[FOSConn] - Add image");
    let img_data = Yojson.Safe.to_string image_data |> FDU.image_of_string in
    let%lwt img_id = Image.add  img_data self.client in
    Lwt.return img_id

  let get_image_list () =
    let self = Apero.Option.get !self in
    Logs.debug (fun m -> m "[FOSConn] - Get image list");
    Image.list self.client >>= fun x -> Lwt.return @@ List.map (fun (x:FDU.image) -> Apero.Option.get x.uuid) x

  let new_fdu_instance ~name ~description ~start ~image_id ~flavor_id ~net_list ~cloud_config ~nodeid =
    let self = Apero.Option.get !self in
    ignore self;
    Logs.debug ( fun m -> m "[FOSConn] - New FDU instance");
    ignore name;
    ignore description;
    ignore start;
    ignore image_id;
    ignore flavor_id;
    ignore net_list;
    ignore cloud_config;

    let%lwt image = Image.list self.client >>= Lwt_list.filter_p (fun( x:FDU.image) -> Lwt.return @@ ((Apero.Option.get x.uuid) = image_id)) >>= fun x -> Lwt.return @@ List.hd x in
    let%lwt comp_requirements = Flavor.list self.client >>= Lwt_list.filter_p (fun( x:FDU.computational_requirements) -> Lwt.return @@ ((Apero.Option.get x.uuid) = flavor_id)) >>= fun x -> Lwt.return @@ List.hd x in

    let mgmt_face =
      match self.conf.mgmt_net with
      | Some nid ->
        let cp_id = Apero.Uuid.make () |> Apero.Uuid.to_string in
        let pair_id = nid in
        let intf_name = Printf.sprintf "mgmt" in
        let cp_d = FDU.{uuid = cp_id; pair_id = Some pair_id} in
        let vif = FDU.{intf_type = `VIRTIO; vpci = "0:0:0"; bandwidth=100} in
        let faced = FDU.{name=intf_name; is_mgmt=true; if_type=`INTERNAL; virtual_interface=vif; mac_address = None; cp_id = Some cp_id}
        in [faced, cp_d]
      | None -> []
    in
    let faces_cps = List.mapi (
        fun i e ->
          let cp_id = Apero.Uuid.make () |> Apero.Uuid.to_string in
          let pair_id = e in
          let intf_name = Printf.sprintf "eth%d" i in
          let cp_d = FDU.{uuid = cp_id; pair_id = Some pair_id} in
          let vif = FDU.{intf_type = `VIRTIO; vpci = "0:0:0"; bandwidth=100} in
          let faced = FDU.{name=intf_name; is_mgmt=false; if_type=`INTERNAL; virtual_interface=vif; mac_address = None; cp_id = Some cp_id}
          in faced, cp_d
      ) net_list
    in
    let faces_cps = faces_cps @ mgmt_face in
    let faces = List.map (fun (f,_) -> f) faces_cps in
    let cps = List.map (fun (_,c) -> c) faces_cps in



    let fdu = FDU.{name; image = Some image; computation_requirements = comp_requirements; geographical_requirements = None;
                   energy_requirements = None; hypervisor = (Fos_im.hv_type_of_string (Apero.Option.get_or_default self.conf.hypervisor "LXD"));
                   migration_kind=`LIVE; interfaces=faces; connection_points=cps; configuration = None; io_ports = []; depends_on = []; uuid=None; description= Some description; command = None} in
    let%lwt fduid = Fos_fim_api.FDU.onboard fdu self.client in
    Fos_fim_api.FDU.instantiate fduid nodeid self.client
    >>= fun _ ->
    Lwt.return (fduid, Fos_im.JSON.create_empty ())

  let get_fdu_instance fdu_instance_id =
    let self = Apero.Option.get !self in
    Logs.debug (fun m -> m "[FOSConn] - Get FDU instance %s" fdu_instance_id);
    let%lwt fdu_info = Fos_fim_api.FDU.instance_info fdu_instance_id self.client in
    Lwt.return (FDU.string_of_record fdu_info |> Yojson.Safe.from_string)

  let delete_fdu_instance fdu_instance_id =
    let self = Apero.Option.get !self in
    Logs.debug (fun m -> m"[FOSConn] - Delete FDU instance %s" fdu_instance_id);
    Fos_fim_api.FDU.terminate fdu_instance_id self.client

  let action_fdu_instance fdu_instance_id created_items action =
    Logs.debug (fun m -> m "[FOSConn] - Actiont to FDU instance %s -> %s" fdu_instance_id action);
    ignore created_items;
    ignore action;
    Lwt.return (fdu_instance_id, created_items)

  let get_fim_status () =
    Logs.debug (fun m -> m "[FOSConn] - Get FIM Status");
    let self = Apero.Option.get (!self) in
    let%lwt nodes = Node.list self.client in
    Lwt_list.map_p (fun (e:Fos_types.node_info) ->
        let%lwt ns = Node.status e.uuid self.client in
        let%lwt pls = Node.plugins e.uuid self.client in
        let%lwt hvs = Lwt_list.filter_map_p
            (fun (x:Fos_types.plugin) ->
               match x.plugin_type with
               | "runtime" -> Lwt.return @@ Some x.name
               | _ -> Lwt.return None
            ) pls in
        let ram = Fos_types.string_of_ram_status ns.ram |> Pl_types.ram_status_of_string in
        let disk = List.map (fun e -> Fos_types.string_of_disk_status e |> Pl_types.disk_status_of_string) ns.disk in
        let neighbors = List.map (fun e -> Fos_types.string_of_neighbor e |> Pl_types.neighbor_of_string) ns.neighbors in
        Lwt.return @@ Pl_types.create_node_status ~uuid:e.uuid ~ram ~disk ~hypervisors:hvs ~neighbors ()
      ) nodes


end


module M:FIMPlugin =
struct

  let make url user password conf =
    (module  (FOSConn(struct
                let url = url
                let user = user
                let password = password
                let configuration = conf
              end)) : FIM.FIMConn)
end


let () =
  p := Some (module M:FIMPlugin)

(* Check *)

(* http://zderadicka.eu/plugins-in-ocaml-with-dynlink-library/ *)