package fog05

import (
	"encoding/json"
	"math/rand"
	"time"

	"github.com/atolab/yaks-go"

	"github.com/google/uuid"
)

// NodeAPI is a component of FIMAPI
type NodeAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
}

// NewNodeAPI returns a new NodeAPI objects
func NewNodeAPI(connector *YaksConnector, sysid string, tenantid string) *NodeAPI {
	return &NodeAPI{connector, sysid, tenantid}
}

// List returns a slice with the node id of the nodes in the system
func (n *NodeAPI) List() ([]string, error) {
	return n.connector.Global.Actual.GetAllNodes(n.sysid, n.tenantid)
}

// Info returns a NodeInfo object with information on the specified node
func (n *NodeAPI) Info(nodeid string) (*NodeInfo, error) {
	return n.connector.Global.Actual.GetNodeInfo(n.sysid, n.tenantid, nodeid)
}

// Status returns a NodeStatus object with status information on the specified node
func (n *NodeAPI) Status(nodeid string) (*NodeStatus, error) {
	return n.connector.Global.Actual.GetNodeStatus(n.sysid, n.tenantid, nodeid)
}

// Plugins returns a slice of olugin ids for the specified node
func (n *NodeAPI) Plugins(nodeid string) ([]string, error) {
	return n.connector.Global.Actual.GetAllPluginsIDs(n.sysid, n.tenantid, nodeid)
}

// PluginAPI is a component of FIMAPI
type PluginAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
}

// NewPluginAPI returns a new PluginAPI object
func NewPluginAPI(connector *YaksConnector, sysid string, tenantid string) *PluginAPI {
	return &PluginAPI{connector, sysid, tenantid}
}

// Info returns a PluginInfo object with information on the specified plugin in the specified node
func (p *PluginAPI) Info(nodeid string, pluginid string) (*Plugin, error) {
	return p.connector.Global.Actual.GetPluginInfo(p.sysid, p.tenantid, nodeid, pluginid)
}

// NetworkAPI is a component of FIMAPI
type NetworkAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
}

// NewNetworkAPI returns a new NetworkAPI object
func NewNetworkAPI(connector *YaksConnector, sysid string, tenantid string) *NetworkAPI {
	return &NetworkAPI{connector, sysid, tenantid}
}

// AddNetwork registers a new virtual network in the system catalog
func (n *NetworkAPI) AddNetwork(descriptor VirtualNetwork) error {
	v := "add"
	descriptor.Status = &v
	return n.connector.Global.Desired.AddNetwork(n.sysid, n.tenantid, descriptor.UUID, descriptor)
}

// RemoveNetwork remove a virtual network from the system catalog
func (n *NetworkAPI) RemoveNetwork(netid string) error {
	return n.connector.Global.Desired.RemoveNetwork(n.sysid, n.tenantid, netid)

}

// AddNetworkToNode creates a virtual network on a specified node and returns a VirtualNetwork object associated to the created network
func (n *NetworkAPI) AddNetworkToNode(nodeid string, descriptor VirtualNetwork) (*VirtualNetwork, error) {
	netid := descriptor.UUID
	// _, err := n.connector.Global.Actual.GetNodeNetwork(n.sysid, n.tenantid, nodeid, netid)
	// if err == nil {
	// 	return &descriptor, nil
	// }

	res, err := n.connector.Global.Actual.CreateNetworkInNode(n.sysid, n.tenantid, nodeid, netid, descriptor)
	if err != nil {
		return nil, err
	}
	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var net VirtualNetwork
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &net)
	if err != nil {
		return nil, err
	}
	return &net, nil
}

// RemoveNetworkFromNode removes a virtual network from the specified node and returns the VirtualNetwork object associated
func (n *NetworkAPI) RemoveNetworkFromNode(nodeid string, netid string) (*VirtualNetwork, error) {
	// _, err := n.connector.Global.Actual.GetNodeNetwork(n.sysid, n.tenantid, nodeid, netid)
	// if err != nil {
	// 	return nil, err
	// }

	res, err := n.connector.Global.Actual.RemoveNetworkFromNode(n.sysid, n.tenantid, nodeid, netid)
	if err != nil {
		return nil, err
	}
	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var net VirtualNetwork
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &net)
	if err != nil {
		return nil, err
	}
	return &net, nil
}

// AddConnectionPoint registers a new connection point in the system catalog
func (n *NetworkAPI) AddConnectionPoint(descriptor ConnectionPointDescriptor) error {
	v := "add"
	descriptor.Status = &v
	return n.connector.Global.Desired.AddNetworkPort(n.sysid, n.tenantid, *descriptor.UUID, descriptor)
}

// DeleteConnectionPoint removes the specified connection point from the system catalog
func (n *NetworkAPI) DeleteConnectionPoint(cpid string) error {
	descriptor, err := n.connector.Global.Actual.GetNetworkPort(n.sysid, n.tenantid, cpid)
	if err != nil {
		return err
	}
	v := "remove"
	descriptor.Status = &v
	return n.connector.Global.Desired.AddNetworkPort(n.sysid, n.tenantid, *descriptor.UUID, *descriptor)

}

// ConnectCPToNetwork connects the specified connection point with the specified virtual network and returns the connection point id
func (n *NetworkAPI) ConnectCPToNetwork(cpid string, netid string) (*string, error) {

	ports, err := n.connector.Global.Actual.GetAllNetworkPorts(n.sysid, n.tenantid)
	if err != nil {
		return nil, err
	}

	var node *string = nil
	var portInfo *ConnectionPointRecord = nil

	for _, p := range ports {
		nid := p.St
		pid := p.Nd
		if pid == cpid {
			portInfo, err = n.connector.Global.Actual.GetNodeNetworkPort(n.sysid, n.tenantid, nid, pid)
			if err != nil {
				return nil, err
			}
			node = &nid
			break
		}
	}
	if portInfo == nil && node == nil {
		return nil, &FError{"Not found", nil}
	}

	res, err := n.connector.Global.Actual.AddNodePortToNetwork(n.sysid, n.tenantid, *node, portInfo.UUID, netid)
	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	v := (*res.Result).(string)
	return &v, nil
}

// DisconnectCP disconnect the specified connection point and returns its id
func (n *NetworkAPI) DisconnectCP(cpid string) (*string, error) {
	ports, err := n.connector.Global.Actual.GetAllNetworkPorts(n.sysid, n.tenantid)
	if err != nil {
		return nil, err
	}

	var node *string = nil
	var portInfo *ConnectionPointRecord = nil

	for _, p := range ports {
		nid := p.St
		pid := p.Nd
		if pid == cpid {
			portInfo, err = n.connector.Global.Actual.GetNodeNetworkPort(n.sysid, n.tenantid, nid, pid)
			if err != nil {
				return nil, err
			}
			node = &nid
			break
		}
	}
	if portInfo == nil && node == nil {
		return nil, &FError{"Not found", nil}
	}
	res, err := n.connector.Global.Actual.RemoveNodePortFromNetwork(n.sysid, n.tenantid, *node, portInfo.UUID)
	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	v := (*res.Result).(string)
	return &v, nil
}

// AddRouter creates a new virtual router in the specified node and returns the associated RouterRecord object
func (n *NetworkAPI) AddRouter(nodeid string, router RouterRecord) (*RouterRecord, error) {
	err := n.connector.Global.Desired.AddNodeNetworkRouter(n.sysid, n.tenantid, nodeid, router.UUID, router)
	if err != nil {
		return nil, err
	}
	routerInfo, _ := n.connector.Global.Actual.GetNodeNetworkRouter(n.sysid, n.tenantid, nodeid, router.UUID)

	for routerInfo == nil {
		routerInfo, _ = n.connector.Global.Actual.GetNodeNetworkRouter(n.sysid, n.tenantid, nodeid, router.UUID)
	}
	return routerInfo, nil
}

// RemoveRouter removes the specified virtual router from the specified node
func (n *NetworkAPI) RemoveRouter(nodeid string, routerid string) error {
	return n.connector.Global.Desired.RemoveNodeNetworkRouter(n.sysid, n.tenantid, nodeid, routerid)
}

// AddRouterPort add a port to the specified virtual router in the specified node and returns the RouterRecord object associated
func (n *NetworkAPI) AddRouterPort(nodeid string, routerid string, portType string, vnetid *string, ipAddress *string) (*RouterRecord, error) {

	var cont bool = false

	switch portType {
	case EXTERNAL:
		cont = true
	case INTERNAL:
		cont = true
	default:
		cont = false
	}

	if !cont {
		return nil, &FError{"portType can be only one of : INTERNAL, EXTERNAL, you used: " + string(portType), nil}
	}

	res, err := n.connector.Global.Actual.AddPortToRouter(n.sysid, n.tenantid, nodeid, routerid, portType, vnetid, ipAddress)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var r RouterRecord
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &r)
	if err != nil {
		return nil, err
	}
	return &r, nil
}

// RemoveRouterPort removes the specified port from the specified router in the specified node and returns the RouterRecord object associated
func (n *NetworkAPI) RemoveRouterPort(nodeid string, routerid string, vnetid string) (*RouterRecord, error) {
	res, err := n.connector.Global.Actual.RemovePortFromRouter(n.sysid, n.tenantid, nodeid, routerid, vnetid)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var r RouterRecord
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &r)
	if err != nil {
		return nil, err
	}
	return &r, nil
}

// CreateFloatingIP create a floating ip in the specified node and returns the FloatingIPRecord object associated
func (n *NetworkAPI) CreateFloatingIP(nodeid string) (*FloatingIPRecord, error) {
	res, err := n.connector.Global.Actual.CrateFloatingIPInNode(n.sysid, n.tenantid, nodeid)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var fip FloatingIPRecord
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &fip)
	if err != nil {
		return nil, err
	}
	return &fip, nil
}

// DeleteFloatingIP delete the specified floating ip from the specified node and returns the FloatingIPRecord object associated
func (n *NetworkAPI) DeleteFloatingIP(nodeid string, ipid string) (*FloatingIPRecord, error) {
	res, err := n.connector.Global.Actual.RemoveFloatingIPFromNode(n.sysid, n.tenantid, nodeid, ipid)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var fip FloatingIPRecord
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &fip)
	if err != nil {
		return nil, err
	}
	return &fip, nil
}

// AssignFloatingIP assign the specified floating ip to the specified connection point and returns the FloatingIPRecord object associated
func (n *NetworkAPI) AssignFloatingIP(nodeid string, ipid string, cpid string) (*FloatingIPRecord, error) {
	res, err := n.connector.Global.Actual.AssignNodeFloatingIP(n.sysid, n.tenantid, nodeid, ipid, cpid)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	v := (*res.Result).(FloatingIPRecord)
	return &v, nil
}

// RetainFloatingIP retain the previously assigned floating ip and returns the FloatingIPRecord object associated
func (n *NetworkAPI) RetainFloatingIP(nodeid string, ipid string, cpid string) (*FloatingIPRecord, error) {
	res, err := n.connector.Global.Actual.RetainNodeFloatingIP(n.sysid, n.tenantid, nodeid, ipid, cpid)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	var fip FloatingIPRecord
	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &fip)
	if err != nil {
		return nil, err
	}
	return &fip, nil
}

// List returns a slice with the networks registered in the system catalog
func (n *NetworkAPI) List() ([]string, error) {
	return n.connector.Global.Actual.GetAllNetwork(n.sysid, n.tenantid)
}

// FDUAPI is a component of FIMAPI
type FDUAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
}

// NewFDUAPI returns a new FDUAPI object
func NewFDUAPI(connector *YaksConnector, sysid string, tenantid string) *FDUAPI {
	rand.Seed(time.Now().Unix())
	return &FDUAPI{connector, sysid, tenantid}
}

func (f *FDUAPI) waitFDUOffloading(fduid string) {
	time.Sleep(1 * time.Second)
	fdu, _ := f.connector.Global.Actual.GetCatalogFDUInfo(f.sysid, f.tenantid, fduid)
	if fdu != nil {
		f.waitFDUOffloading(fduid)
	}
}

func (f *FDUAPI) waitFDUInstanceStateChange(nodeid string, fduid string, instanceid, newState string) (chan bool, *yaks.SubscriptionID) {

	c := make(chan bool, 1)
	cb := func(fdu *FDURecord, isRemove bool) {
		if isRemove {
			c <- true
		}
		if fdu.FDUID == fduid && fdu.UUID == instanceid && fdu.Status == newState {
			c <- true
		}
		return
	}

	sid, err := f.connector.Global.Actual.ObserveNodeFDU(f.sysid, f.tenantid, nodeid, cb)
	if err != nil {
		panic(err.Error())
	}
	return c, sid
}

func (f *FDUAPI) waitFDUInstanceUndefine(nodeid string, instanceid string) {

	time.Sleep(1 * time.Second)
	fdu, _ := f.connector.Global.Actual.GetNodeFDUInstance(f.sysid, f.tenantid, nodeid, instanceid)
	if fdu != nil {
		f.waitFDUInstanceUndefine(nodeid, instanceid)
	}
}

func (f *FDUAPI) changeFDUInstanceState(instanceid string, state string, newState string) (string, error) {
	node, err := f.connector.Global.Actual.GetFDUInstanceNode(f.sysid, f.tenantid, instanceid)
	if err != nil {
		return instanceid, err
	}
	record, err := f.connector.Global.Actual.GetNodeFDUInstance(f.sysid, f.tenantid, node, instanceid)
	if err != nil {
		return instanceid, err
	}
	record.Status = state
	c, sid := f.waitFDUInstanceStateChange(node, record.FDUID, instanceid, newState)

	f.connector.Global.Desired.AddNodeFDU(f.sysid, f.tenantid, node, record.FDUID, record.UUID, *record)

	<-c

	f.connector.Global.Actual.Unsubscribe(sid)

	return instanceid, nil
}

// Onboard register an FDU in the system catalog and returns the associated FDU object
func (f *FDUAPI) Onboard(descriptor FDU) (*FDU, error) {
	var fdu FDU

	nodes, err := f.connector.Global.Actual.GetAllNodes(f.sysid, f.tenantid)
	if err != nil {
		return nil, err
	}
	nid := nodes[rand.Intn(len(nodes))]
	res, err := f.connector.Global.Actual.OnboardFDUFromNode(f.sysid, f.tenantid, nid, descriptor)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &fdu)
	if err != nil {
		return nil, err
	}
	return &fdu, nil
}

// Offload removes a registered FDU from the system catalog and returns its UUID
func (f *FDUAPI) Offload(fduid string) (string, error) {
	err := f.connector.Global.Desired.RemoveCatalogFDUInfo(f.sysid, f.tenantid, fduid)
	return fduid, err
}

// Define creates and FDU Instance for the specified FDU in the specified node and returns the FDURecord object associated
func (f *FDUAPI) Define(nodeid string, fduid string) (*FDURecord, error) {
	var fdu FDURecord
	_, err := f.connector.Global.Actual.GetCatalogFDUInfo(f.sysid, f.tenantid, fduid)
	if err != nil {
		return nil, err
	}
	res, err := f.connector.Global.Actual.DefineFDUInNode(f.sysid, f.tenantid, nodeid, fduid)
	if err != nil {
		return nil, err
	}

	if res.Error != nil {
		return nil, &FError{*res.ErrorMessage + " ErrNo: " + string(*res.Error), nil}
	}

	v, err := json.Marshal(*res.Result)
	if err != nil {
		return nil, err
	}

	err = json.Unmarshal([]byte(v), &fdu)
	if err != nil {
		return nil, err
	}

	c, sid := f.waitFDUInstanceStateChange(nodeid, fdu.FDUID, fdu.UUID, DEFINE)

	<-c

	f.connector.Global.Actual.Unsubscribe(sid)

	return &fdu, nil

}

// Undefine removes the specified FDU instance and returns its UUID
func (f *FDUAPI) Undefine(instanceid string) (string, error) {
	node, err := f.connector.Global.Actual.GetFDUInstanceNode(f.sysid, f.tenantid, instanceid)
	if err != nil {
		return instanceid, err
	}
	record, err := f.connector.Global.Actual.GetNodeFDUInstance(f.sysid, f.tenantid, node, instanceid)
	if err != nil {
		return instanceid, err
	}
	record.Status = UNDEFINE
	err = f.connector.Global.Desired.AddNodeFDU(f.sysid, f.tenantid, node, record.FDUID, record.UUID, *record)
	return instanceid, err
}

// Configure the specified FDU instance and returns its UUID
func (f *FDUAPI) Configure(instanceid string) (string, error) {
	return f.changeFDUInstanceState(instanceid, CONFIGURE, CONFIGURE)
}

// Clean the specified FDU instance and returns its UUID
func (f *FDUAPI) Clean(instanceid string) (string, error) {
	return f.changeFDUInstanceState(instanceid, CLEAN, DEFINE)
}

// Start the specified FDU instance and returns its UUID
func (f *FDUAPI) Start(instanceid string) (string, error) {
	return f.changeFDUInstanceState(instanceid, RUN, RUN)
}

// Stop the specified FDU instance and returns its UUID
func (f *FDUAPI) Stop(instanceid string) (string, error) {
	return f.changeFDUInstanceState(instanceid, STOP, CONFIGURE)
}

// Pause the specified FDU instance and returns its UUID
func (f *FDUAPI) Pause(instanceid string) (string, error) {
	return f.changeFDUInstanceState(instanceid, PAUSE, PAUSE)
}

// Resume the specified FDU instance and returns its UUID
func (f *FDUAPI) Resume(instanceid string) (string, error) {
	return f.changeFDUInstanceState(instanceid, RESUME, RUN)
}

// Migrate the specified FDU instance to the specified node and returns the FDU instance UUID
func (f *FDUAPI) Migrate(instanceid string, destination string) (string, error) {
	return "", &FError{"Not Implemented", nil}
}

// Instantiate is a commodity function that does Define, Configure and Start for a specified FDU in the specified node and returns the FDU instance UUID
func (f *FDUAPI) Instantiate(nodeid string, fduid string) (string, error) {
	fdur, err := f.Define(nodeid, fduid)
	if err != nil {
		return fduid, err
	}
	time.Sleep(500 * time.Millisecond)
	_, err = f.Configure(fdur.UUID)
	if err != nil {
		return fdur.UUID, err
	}
	time.Sleep(500 * time.Millisecond)
	_, err = f.Start(fdur.UUID)
	return fdur.UUID, err
}

// Terminate is a commodity function that does  Stop, Clean and Undefine for the specified FDU instance and returns its UUID
func (f *FDUAPI) Terminate(instanceid string) (string, error) {
	_, err := f.Stop(instanceid)
	if err != nil {
		return instanceid, err
	}
	time.Sleep(500 * time.Millisecond)
	_, err = f.Clean(instanceid)
	if err != nil {
		return instanceid, err
	}
	time.Sleep(500 * time.Millisecond)
	_, err = f.Undefine(instanceid)
	return instanceid, err
}

// GetNodes returns a slice with the node id in which the FDU is running
func (f *FDUAPI) GetNodes(fduid string) ([]string, error) {
	return f.connector.Global.Actual.GetFDUNodes(f.sysid, f.tenantid, fduid)
}

// Info returns the FDU object with information on the specified FDU
func (f *FDUAPI) Info(fduid string) (*FDU, error) {
	return f.connector.Global.Actual.GetCatalogFDUInfo(f.sysid, f.tenantid, fduid)
}

// InstanceInfo return the FDURecord object with information on the specified FDU instance
func (f *FDUAPI) InstanceInfo(instanceid string) (*FDURecord, error) {
	return f.connector.Global.Actual.GetNodeFDUInstance(f.sysid, f.tenantid, "*", instanceid)
}

// List returns a slice with the UUID of all the FDU registered in the system catalog
func (f *FDUAPI) List() ([]string, error) {
	return f.connector.Global.Actual.GetCatalogAllFDUs(f.sysid, f.tenantid)
}

// InstanceList for a given FDU and node returns the a map of FDU instances running
func (f *FDUAPI) InstanceList(fduid string, nodeid *string) (map[string][]string, error) {
	if nodeid == nil {
		x := "*"
		nodeid = &x
	}
	res := map[string][]string{}
	instances, err := f.connector.Global.Actual.GetNodeFDUInstances(f.sysid, f.tenantid, *nodeid, fduid)
	if err != nil {
		return res, err
	}
	for _, c := range instances {
		res[c.St] = []string{}
	}
	for _, c := range instances {
		res[c.St] = append(res[c.St], c.Nd)
	}
	return res, nil

}

// ConnectInterfaceToCP given a connection point, and FDU instance and interface and a node connects the connection point to the specified interface and returns the FDU instance UUID
func (f *FDUAPI) ConnectInterfaceToCP(cpid string, instanceid string, face string, nodeid string) (string, error) {
	return "", &FError{"Not Implemented", nil}
}

// DisconnectInterfaceToCP disconnect the given interface and returns the FDU instance UUID
func (f *FDUAPI) DisconnectInterfaceToCP(face string, instanceid string, nodeid string) (string, error) {
	return "", &FError{"Not Implemented", nil}
}

// ImageAPI is a component of FIMAPI
type ImageAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
}

// NewImageAPI returns a new ImageAPI object
func NewImageAPI(connector *YaksConnector, sysid string, tenantid string) *ImageAPI {
	return &ImageAPI{connector, sysid, tenantid}
}

// Add registers an image in the system catalog and returns its UUID
func (i *ImageAPI) Add(descriptor FDUImage) (string, error) {
	if *descriptor.UUID == "" {
		v := (uuid.UUID.String(uuid.New()))
		descriptor.UUID = &v
	}
	err := i.connector.Global.Desired.AddImage(i.sysid, i.tenantid, *descriptor.UUID, descriptor)
	return *descriptor.UUID, err
}

// Remove removes the given image from the system catalog and returns its UUID
func (i *ImageAPI) Remove(imgid string) (string, error) {
	err := i.connector.Global.Desired.RemoveImage(i.sysid, i.tenantid, imgid)
	return imgid, err
}

// List returns a slice with the UUIDs of the images registered in the system catalog
func (i *ImageAPI) List() ([]string, error) {
	return i.connector.Global.Actual.GetAllImages(i.sysid, i.tenantid)
}

// FlavorAPI is a component of FIMAPI
type FlavorAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
}

// NewFlavorAPI returns a new FlavorAPI object
func NewFlavorAPI(connector *YaksConnector, sysid string, tenantid string) *FlavorAPI {
	return &FlavorAPI{connector, sysid, tenantid}
}

// Add registers a new flavor in the system catalog and returns its UUID
func (f *FlavorAPI) Add(descriptor FDUComputationalRequirements) (string, error) {
	if *descriptor.UUID == "" {
		v := (uuid.UUID.String(uuid.New()))
		descriptor.UUID = &v
	}
	err := f.connector.Global.Desired.AddFlavor(f.sysid, f.tenantid, *descriptor.UUID, descriptor)
	return *descriptor.UUID, err
}

// Remove removes the given flavor from the system catalog and returns its UUID
func (f *FlavorAPI) Remove(flvid string) (string, error) {
	err := f.connector.Global.Desired.RemoveFlavor(f.sysid, f.tenantid, flvid)
	return flvid, err
}

// List returns a slice with the UUIDs of the flavors registered in the system catalog
func (f *FlavorAPI) List() ([]string, error) {
	return f.connector.Global.Actual.GetAllFlavors(f.sysid, f.tenantid)
}

// FIMAPI is the api to interact with Eclipse fog05 FIM
type FIMAPI struct {
	connector *YaksConnector
	sysid     string
	tenantid  string
	Image     *ImageAPI
	FDU       *FDUAPI
	Network   *NetworkAPI
	Node      *NodeAPI
	Plugin    *PluginAPI
}

// NewFIMAPI returns a new FIMAPI object, locators has to be in this form tcp/<yaks server address>:<yaks port>
func NewFIMAPI(locator string, sysid *string, tenantid *string) (*FIMAPI, error) {

	if sysid == nil {
		v := DefaultSysID
		sysid = &v
	}

	if tenantid == nil {
		v := DefaultTenantID
		tenantid = &v
	}

	yco, err := NewYaksConnector(locator)
	if err != nil {
		return nil, err
	}

	node := NewNodeAPI(yco, *sysid, *tenantid)
	img := NewImageAPI(yco, *sysid, *tenantid)
	fdu := NewFDUAPI(yco, *sysid, *tenantid)
	net := NewNetworkAPI(yco, *sysid, *tenantid)
	pl := NewPluginAPI(yco, *sysid, *tenantid)

	return &FIMAPI{yco, *sysid, *tenantid, img, fdu, net, node, pl}, nil
}

// Close closes the connection of the FIM API
func (f *FIMAPI) Close() error {
	return f.connector.Close()
}
