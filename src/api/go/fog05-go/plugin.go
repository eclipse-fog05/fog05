package fog05

import (
	b64 "encoding/base64"
	"encoding/hex"
	"encoding/json"

	"github.com/google/uuid"
)

// OS ...
type OS struct {
	uuid      string
	connector *YaksConnector
	node      string
}

// CallOSPluginFunction ...
func (os *OS) CallOSPluginFunction(fname string, fparameters map[string]interface{}) (*interface{}, error) {
	res, err := os.connector.Local.Actual.ExecOSEval(os.node, fname, fparameters)
	if err != nil {
		return nil, err
	}
	if res.Error != 0 {
		er := FError{res.ErrorMessage + " ErrNo: " + string(res.Error), nil}
		return nil, &er
	}
	return &res.Result, nil
}

// DirExists ...
func (os *OS) DirExists(dirpath string) (bool, error) {
	r, err := os.CallOSPluginFunction("dir_exists", map[string]interface{}{"dir_path": dirpath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// CreateDir ...
func (os *OS) CreateDir(dirpath string) (bool, error) {
	r, err := os.CallOSPluginFunction("create_dir", map[string]interface{}{"dir_path": dirpath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// RemoveDir ...
func (os *OS) RemoveDir(dirpath string) (bool, error) {
	r, err := os.CallOSPluginFunction("remove_dir", map[string]interface{}{"dir_path": dirpath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// DownloadFile ...
func (os *OS) DownloadFile(url string, filepath string) (bool, error) {
	r, err := os.CallOSPluginFunction("download_file", map[string]interface{}{"url": url, "file_path": filepath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// ExecuteCommand ...
func (os *OS) ExecuteCommand(command string, blocking bool, external bool) (string, error) {
	r, err := os.CallOSPluginFunction("execute_command", map[string]interface{}{"command": command, "blocking": blocking, "external": external})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// CreateFile ...
func (os *OS) CreateFile(filepath string) (bool, error) {
	r, err := os.CallOSPluginFunction("create_file", map[string]interface{}{"file_path": filepath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// RemoveFile ...
func (os *OS) RemoveFile(filepath string) (bool, error) {
	r, err := os.CallOSPluginFunction("remove_file", map[string]interface{}{"file_path": filepath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// StoreFile ...
func (os *OS) StoreFile(content string, filepath string, filename string) (bool, error) {

	c := hex.EncodeToString([]byte(b64.StdEncoding.EncodeToString([]byte(content))))
	r, err := os.CallOSPluginFunction("store_file", map[string]interface{}{"file_path": filepath, "filename": filename, "content": c})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// ReadFile ...
func (os *OS) ReadFile(filepath string, root bool) (string, error) {
	r, err := os.CallOSPluginFunction("read_file", map[string]interface{}{"file_path": filepath, "root": root})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// FileExists ...
func (os *OS) FileExists(filepath string) (bool, error) {
	r, err := os.CallOSPluginFunction("file_exists", map[string]interface{}{"file_path": filepath})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// SendSigInt ...
func (os *OS) SendSigInt(pid int) (bool, error) {
	r, err := os.CallOSPluginFunction("send_sig_int", map[string]interface{}{"pid": pid})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// SendSigKill ...
func (os *OS) SendSigKill(pid int) (bool, error) {
	r, err := os.CallOSPluginFunction("send_sig_kill", map[string]interface{}{"pid": pid})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// CheckIfPIDExists ...
func (os *OS) CheckIfPIDExists(pid int) (bool, error) {
	r, err := os.CallOSPluginFunction("check_if_pid_exists", map[string]interface{}{"pid": pid})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// GetInterfaceType ...
func (os *OS) GetInterfaceType(facename string) (string, error) {
	r, err := os.CallOSPluginFunction("get_intf_type", map[string]interface{}{"name": facename})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// SetInterfaceUnaviable ...
func (os *OS) SetInterfaceUnaviable(facename string) (bool, error) {
	r, err := os.CallOSPluginFunction("set_interface_unaviable", map[string]interface{}{"intf_name": facename})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// SetInterfaceAvailable ...
func (os *OS) SetInterfaceAvailable(facename string) (bool, error) {
	r, err := os.CallOSPluginFunction("set_interface_available", map[string]interface{}{"intf_name": facename})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// Checksum ...
func (os *OS) Checksum(filepath string) (string, error) {
	r, err := os.CallOSPluginFunction("checksum", map[string]interface{}{"file_path": filepath})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// LocalMgmtAddress ...
func (os *OS) LocalMgmtAddress() (string, error) {
	r, err := os.CallOSPluginFunction("local_mgmt_address", map[string]interface{}{})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// NM ...
type NM struct {
	uuid      string
	connector *YaksConnector
	node      string
}

// CallNMPluginFunction ...
func (nm *NM) CallNMPluginFunction(fname string, fparameters map[string]interface{}) (*interface{}, error) {
	res, err := nm.connector.Local.Actual.ExecNMEval(nm.node, nm.uuid, fname, fparameters)
	if err != nil {
		return nil, err
	}
	if res.Error != 0 {
		er := FError{res.ErrorMessage + " ErrNo: " + string(res.Error), nil}
		return nil, &er
	}
	return &res.Result, nil
}

// CreateVirtualInterface ...
func (nm *NM) CreateVirtualInterface(intfid string, descriptor map[string]interface{}) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("create_virtual_interface", map[string]interface{}{"intf_id": intfid, "descriptor": descriptor})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// DeleteVirtualInterface ...
func (nm *NM) DeleteVirtualInterface(intfid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("delete_virtual_interface", map[string]interface{}{"intf_id": intfid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// CreateVirtualBridge ...
func (nm *NM) CreateVirtualBridge(name string, uuid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("create_virtual_bridge", map[string]interface{}{"name": name, "uuid": uuid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// DeleteVirtualBridge ...
func (nm *NM) DeleteVirtualBridge(uuid string) (string, error) {
	r, err := nm.CallNMPluginFunction("delete_virtual_bridge", map[string]interface{}{"br_uuid": uuid})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// CreateBridgesIfNotExists ...
func (nm *NM) CreateBridgesIfNotExists(expected []string) (*[]map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("create_bridges_if_not_exist", map[string]interface{}{"expected_bridges": expected})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.([]map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// ConnectInterfaceToConnectionPoint ...
func (nm *NM) ConnectInterfaceToConnectionPoint(intfid string, cpid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("connect_interface_to_connection_point", map[string]interface{}{"intf_id": intfid, "cp_id": cpid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// DisconnectInterface ...
func (nm *NM) DisconnectInterface(intfid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("disconnect_interface", map[string]interface{}{"intf_id": intfid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// ConnectCPToVNetwork ...
func (nm *NM) ConnectCPToVNetwork(cpid string, vnetid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("connect_cp_to_vnetwork", map[string]interface{}{"cp_id": cpid, "vnet_id": vnetid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// DisconnectCP ...
func (nm *NM) DisconnectCP(cpid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("disconnect_cp", map[string]interface{}{"cp_id": cpid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// DeletePort ...
func (nm *NM) DeletePort(cpid string) (bool, error) {
	r, err := nm.CallNMPluginFunction("delete_port", map[string]interface{}{"cp_id": cpid})
	if err != nil {
		return false, err
	}

	x := *r
	switch bb := x.(type) {
	case bool:
		return x.(bool), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return false, &er
	}
}

// GetAddress ...
func (nm *NM) GetAddress(cpid string) (string, error) {
	r, err := nm.CallNMPluginFunction("delete_port", map[string]interface{}{"cp_id": cpid})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// AddPortToRouter ...
func (nm *NM) AddPortToRouter(routerid string, porttype string, vnetid string, ipaddress string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("add_router_port", map[string]interface{}{"router_id": routerid, "port_type": porttype, "vnet_id": vnetid, "ip_address": ipaddress})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// RemovePortFromRouter ...
func (nm *NM) RemovePortFromRouter(routerid string, vnetid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("remove_port_from_router", map[string]interface{}{"router_id": routerid, "vnet_id": vnetid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// CreateFloatingIP ...
func (nm *NM) CreateFloatingIP() (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("create_floating_ip", map[string]interface{}{})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// DeleteFloatingIP ...
func (nm *NM) DeleteFloatingIP(ipid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("delete_floating_ip", map[string]interface{}{"ip_id": ipid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// AssignFloatingIP ...
func (nm *NM) AssignFloatingIP(ipid string, cpid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("assign_floating_ip", map[string]interface{}{"ip_id": ipid, "cp_id": cpid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// RemoveFloatingIP ...
func (nm *NM) RemoveFloatingIP(ipid string, cpid string) (*map[string]interface{}, error) {
	r, err := nm.CallNMPluginFunction("remove_floating_ip", map[string]interface{}{"ip_id": ipid, "cp_id": cpid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		return &sv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// GetOverlayFace ...
func (nm *NM) GetOverlayFace() (string, error) {
	r, err := nm.CallNMPluginFunction("get_overlay_face", map[string]interface{}{})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// GetVLANFace ...
func (nm *NM) GetVLANFace() (string, error) {
	r, err := nm.CallNMPluginFunction("get_vlan_face", map[string]interface{}{})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// Agent ...
type Agent struct {
	connector *YaksConnector
	node      string
}

// CallAgentFunction ...
func (ag *Agent) CallAgentFunction(fname string, fparameters map[string]interface{}) (*interface{}, error) {
	res, err := ag.connector.Local.Actual.ExecAgentEval(ag.node, fname, fparameters)
	if err != nil {
		return nil, err
	}
	if res.Error != 0 {
		er := FError{res.ErrorMessage + " ErrNo: " + string(res.Error), nil}
		return nil, &er
	}
	return &res.Result, nil
}

// GetImageInfo ...
func (ag *Agent) GetImageInfo(imgid string) (*FDUImage, error) {
	r, err := ag.CallAgentFunction("get_image_info", map[string]interface{}{"image_uuid": imgid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		jsv, err := json.Marshal(sv)
		if err != nil {
			return nil, err
		}
		ssv := FDUImage{}
		json.Unmarshal(jsv, &ssv)
		return &ssv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// GetFDUInfo ...
func (ag *Agent) GetFDUInfo(nodeid string, fduid string, instanceid string) (*FDU, error) {
	r, err := ag.CallAgentFunction("get_node_fdu_info", map[string]interface{}{"fdu_uuid": fduid, "instance_uuid": instanceid, "node_uuid": nodeid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		jsv, err := json.Marshal(sv)
		if err != nil {
			return nil, err
		}
		ssv := FDU{}
		json.Unmarshal(jsv, &ssv)
		return &ssv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// GetNetworkInfo ...
func (ag *Agent) GetNetworkInfo(netid string) (*VirtualNetwork, error) {
	r, err := ag.CallAgentFunction("get_network_info", map[string]interface{}{"uuid": netid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		jsv, err := json.Marshal(sv)
		if err != nil {
			return nil, err
		}
		ssv := VirtualNetwork{}
		json.Unmarshal(jsv, &ssv)
		return &ssv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// GetPortInfo ...
func (ag *Agent) GetPortInfo(cpid string) (*ConnectionPointDescriptor, error) {
	r, err := ag.CallAgentFunction("get_port_info", map[string]interface{}{"cp_uuid": cpid})
	if err != nil {
		return nil, err
	}

	x := *r
	switch bb := x.(type) {
	case map[string]interface{}:
		sv := x.(map[string]interface{})
		jsv, err := json.Marshal(sv)
		if err != nil {
			return nil, err
		}
		ssv := ConnectionPointDescriptor{}
		json.Unmarshal(jsv, &ssv)
		return &ssv, nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return nil, &er
	}
}

// GetNodeMGMTAddress ...
func (ag *Agent) GetNodeMGMTAddress(nodeid string) (string, error) {
	r, err := ag.CallAgentFunction("get_node_mgmt_address", map[string]interface{}{"node_uuid": nodeid})
	if err != nil {
		return "", err
	}

	x := *r
	switch bb := x.(type) {
	case string:
		return x.(string), nil
	default:
		er := FError{"Unexpected type: " + bb.(string), nil}
		return "", &er
	}
}

// FOSPlugin ...
type FOSPlugin struct {
	version   int
	connector *YaksConnector
	node      string
	NM        *NM
	OS        *OS
	Agent     *Agent
	UUID      string
}

// NewPlugin ...
func NewPlugin(version int, pluginuuid string) *FOSPlugin {
	if pluginuuid == "" {
		pluginuuid = uuid.UUID.String(uuid.New())
	}
	return &FOSPlugin{version: version, UUID: pluginuuid, node: "", NM: nil, OS: nil, connector: nil, Agent: nil}
}

// GetOSPlugin ...
func (pl *FOSPlugin) GetOSPlugin() bool {
	pls, err := pl.connector.Local.Actual.GetAllPlugins(pl.node)
	if err != nil {
		panic(err.Error())
	}
	for _, pid := range pls {
		pld, err := pl.connector.Local.Actual.GetNodePlugin(pl.node, pid)
		if err != nil {
			panic(err.Error())
		}
		if pld.Type == "os" {
			pl.OS = &OS{uuid: pld.UUID, connector: pl.connector, node: pl.node}
			return true
		}
	}
	return false
}

// GetNMPlugin ...
func (pl *FOSPlugin) GetNMPlugin() bool {
	pls, err := pl.connector.Local.Actual.GetAllPlugins(pl.node)
	if err != nil {
		panic(err.Error())
	}
	for _, pid := range pls {
		pld, err := pl.connector.Local.Actual.GetNodePlugin(pl.node, pid)
		if err != nil {
			panic(err.Error())
		}
		if pld.Type == "network" {
			pl.NM = &NM{uuid: pld.UUID, connector: pl.connector, node: pl.node}
			return true
		}
	}
	return false
}

// GetAgent ...
func (pl *FOSPlugin) GetAgent() bool {
	pls, err := pl.connector.Local.Actual.GetAllPlugins(pl.node)
	if err != nil {
		panic(err.Error())
	}
	for _, pid := range pls {
		pld, err := pl.connector.Local.Actual.GetNodePlugin(pl.node, pid)
		if err != nil {
			panic(err.Error())
		}
		if pld.Type == "network" {
			pl.Agent = &Agent{connector: pl.connector, node: pl.node}
			return true
		}
	}
	return false
}

// GetLocalMGMTAddress ...
func (pl *FOSPlugin) GetLocalMGMTAddress() string {
	ip, err := pl.OS.LocalMgmtAddress()
	if err != nil {
		panic(err.Error())
	}
	return ip
}

// GetPluginState ...
func (pl *FOSPlugin) GetPluginState() map[string]interface{} {
	s, err := pl.connector.Local.Actual.GetNodePluginState(pl.node, pl.UUID)
	if err != nil {
		panic(err.Error())
	}
	return *s
}

// SavePluginState ...
func (pl *FOSPlugin) SavePluginState(state map[string]interface{}) error {
	return pl.connector.Local.Actual.AddNodePluginState(pl.node, pl.UUID, state)
}

// RemovePluginState ...
func (pl *FOSPlugin) RemovePluginState(state map[string]interface{}) error {
	return pl.connector.Local.Actual.RemoveNodePluginState(pl.node, pl.UUID)
}
