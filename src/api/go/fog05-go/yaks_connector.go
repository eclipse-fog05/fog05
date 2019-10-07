package fog05

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/atolab/yaks-go"

	log "github.com/sirupsen/logrus"
)

var logger = log.WithFields(log.Fields{"pkg": "fog05"})

// GlobalActualPrefix ...
const GlobalActualPrefix string = "/agfos"

// GlobalDesiredPrefix ...
const GlobalDesiredPrefix string = "/dgfos"

// LocalActualPrefix ...
const LocalActualPrefix string = "/alfos"

// LocalDesiredPrefix ...
const LocalDesiredPrefix string = "/dlfos"

// Not Used

// LocalConstraintActualPrefix ...
const LocalConstraintActualPrefix string = "/aclfos"

// LocalConstraintDesiredPrefix ...
const LocalConstraintDesiredPrefix string = "/dclfos"

// URISeparator ...
const URISeparator string = "/"

// CreatePath ...
func CreatePath(tokens []string) *yaks.Path {
	p, err := yaks.NewPath(strings.Join(tokens[:], URISeparator))
	if err != nil {
		panic(err.Error())
	}
	return p
}

// CreateSelector ...
func CreateSelector(tokens []string) *yaks.Selector {
	s, err := yaks.NewSelector(strings.Join(tokens[:], URISeparator))
	if err != nil {
		panic(err.Error())
	}
	return s
}

// Dict2Args ...
func Dict2Args(d map[string]interface{}) string {

	var s strings.Builder
	var i int = 0
	for k := range d {
		v := d[k]
		_, ok := v.(map[string]interface{})
		if ok {
			v, _ = json.Marshal(v)
		}
		if i == 0 {
			s.WriteString(fmt.Sprintf("%s=%s", k, v))
		} else {
			s.WriteString(fmt.Sprintf(";%s=%s", k, v))
		}
		i++
	}

	return fmt.Sprintf("(%s)", s.String())
}

// GAD is Global Actual Desired
type GAD struct {
	ws        *yaks.Workspace
	prefix    string
	listeners []*yaks.SubscriptionID
	evals     []*yaks.Path
}

// GetSysInfoPath ...
func (gad *GAD) GetSysInfoPath(sysid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "info"})
}

// GetSysConfigurationPath ...
func (gad *GAD) GetSysConfigurationPath(sysid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "configuration"})
}

// System

// GetAllUsersSelector ...
func (gad *GAD) GetAllUsersSelector(sysid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "users", "*"})
}

// GetUserInfoPath ...
func (gad *GAD) GetUserInfoPath(sysid string, userid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "users", userid, "info"})
}

// Tenants

// GetAllTenantsSelector ...
func (gad *GAD) GetAllTenantsSelector(sysid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", "*"})
}

// GetTenantInfoPath ...
func (gad *GAD) GetTenantInfoPath(sysid string, tenantid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "info"})
}

// GetTenantConfigurationPath ...
func (gad *GAD) GetTenantConfigurationPath(sysid string, tenantid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "configuration"})
}

// Catalog

// GetCatalogAtomicEntityInfoPath ...
func (gad *GAD) GetCatalogAtomicEntityInfoPath(sysid string, tenantid string, aeid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "catalog", "atomic-entities", aeid, "info"})
}

// GetCatalogAllAtomicEntitiesSelector ...
func (gad *GAD) GetCatalogAllAtomicEntitiesSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "catalog", "atomic-entities", "*", "info"})
}

// GetCatalogFDUInfoPath ...
func (gad *GAD) GetCatalogFDUInfoPath(sysid string, tenantid string, fduid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "catalog", "fdu", fduid, "info"})
}

// GetCatalogAllFDUSelector ...
func (gad *GAD) GetCatalogAllFDUSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "catalog", "fdu", "*", "info"})
}

// GetCatalogEntityInfoPath ...
func (gad *GAD) GetCatalogEntityInfoPath(sysid string, tenantid string, eid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "catalog", "entities", eid, "info"})
}

// GetCatalogAllEntitiesSelector ...
func (gad *GAD) GetCatalogAllEntitiesSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "catalog", "entities", "*", "info"})
}

// Records

// GetRecordsAtomicEntityInstanceInfoPath ...
func (gad *GAD) GetRecordsAtomicEntityInstanceInfoPath(sysid string, tenantid string, aeid string, instanceid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "records", "atomic-entities", aeid, "instances", instanceid, "info"})
}

// GetRecordsAllAtomicEntityInstancesSelector ...
func (gad *GAD) GetRecordsAllAtomicEntityInstancesSelector(sysid string, tenantid string, aeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "records", "atomic-entities", aeid, "instances", "*", "info"})
}

// GetRecordsAllAtomicEntitiesInstancesSelector ...
func (gad *GAD) GetRecordsAllAtomicEntitiesInstancesSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "records", "atomic-entities", "*", "instances", "*", "info"})
}

// GetRecordsEntityInstanceInfoPath ...
func (gad *GAD) GetRecordsEntityInstanceInfoPath(sysid string, tenantid string, eid string, instanceid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "records", "entities", eid, "instances", instanceid, "info"})
}

// GetRecordsAllEntityInstancesSelector ..
func (gad *GAD) GetRecordsAllEntityInstancesSelector(sysid string, tenantid string, eid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "records", "entities", eid, "instances", "*", "info"})
}

// GetRecordsAllEntitiesInstancesSelector ...
func (gad *GAD) GetRecordsAllEntitiesInstancesSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "records", "entities", "*", "instances", "*", "info"})
}

// Nodes

// GetAllNodesSelector ...
func (gad *GAD) GetAllNodesSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", "*", "info"})
}

// GetNodeInfoPath ...
func (gad *GAD) GetNodeInfoPath(sysid string, tenantid string, nodeid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "info"})
}

// GetNodeConfigurationPath ...
func (gad *GAD) GetNodeConfigurationPath(sysid string, tenantid string, nodeid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "configuration"})
}

// GetNodeStatusPath ...
func (gad *GAD) GetNodeStatusPath(sysid string, tenantid string, nodeid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "status"})
}

// GetNodePluginsSelector ...
func (gad *GAD) GetNodePluginsSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "plugins", "**"})
}

// GetNodePluginInfoPath ...
func (gad *GAD) GetNodePluginInfoPath(sysid string, tenantid string, nodeid string, plugind string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "plugins", plugind, "info"})
}

// GetNodePluginEvalPath ...
func (gad *GAD) GetNodePluginEvalPath(sysid string, tenantid string, nodeid string, plugind string, funcname string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "plugins", plugind, "exec", funcname})
}

// Node FDU or FDU Records

// GetNodeFDUInfoPath ...
func (gad *GAD) GetNodeFDUInfoPath(sysid string, tenantid string, nodeid string, fduid string, instanceid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "fdu", fduid, "instances", instanceid, "info"})
}

// GetNodeFDUSelector ...
func (gad *GAD) GetNodeFDUSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "fdu", "*", "instances", "*", "info"})
}

// GetNodeFDUInstancesSelector ...
func (gad *GAD) GetNodeFDUInstancesSelector(sysid string, tenantid string, nodeid string, fduid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "fdu", fduid, "instances", "*", "info"})
}

// GetNodeFDUInstanceSelector ...
func (gad *GAD) GetNodeFDUInstanceSelector(sysid string, tenantid string, nodeid string, instanceid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "fdu", "*", "instances", instanceid, "info"})
}

// GetFDUInstanceSelector ...
func (gad *GAD) GetFDUInstanceSelector(sysid string, tenantid string, instanceid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", "*", "fdu", "*", "instances", instanceid, "info"})
}

// Network

// GetAllNetworksSelector ...
func (gad *GAD) GetAllNetworksSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "network", "*", "info"})
}

// GetNetworkInfoPath ...
func (gad *GAD) GetNetworkInfoPath(sysid string, tenantid string, networkid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "network", networkid, "info"})
}

// GetNetworkPortInfoPath ...
func (gad *GAD) GetNetworkPortInfoPath(sysid string, tenantid string, portid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "network", "ports", portid, "info"})
}

// GetAllPortsSelector ...
func (gad *GAD) GetAllPortsSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "network", "ports", "*", "info"})
}

// GetNetworkRouterInfoPath ..
func (gad *GAD) GetNetworkRouterInfoPath(sysid string, tenantid string, routerid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "network", "routers", routerid, "info"})
}

// GetAllRoutersSelector ...
func (gad *GAD) GetAllRoutersSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "network", "routers", "*", "info"})
}

// Images

// GetImageInfoPath ...
func (gad *GAD) GetImageInfoPath(sysid string, tenantid string, imageid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "image", imageid, "info"})
}

// GetAllImageSelector ...
func (gad *GAD) GetAllImageSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "image", "*", "info"})
}

// Node Images

// GetNodeImageInfoPath ...
func (gad *GAD) GetNodeImageInfoPath(sysid string, tenantid string, nodeid string, imageid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "image", imageid, "info"})
}

// GetAllNodeImageSelector ...
func (gad *GAD) GetAllNodeImageSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "image", "*", "info"})
}

// Flavor

// GetFlavorInfoPath ...
func (gad *GAD) GetFlavorInfoPath(sysid string, tenantid string, flavorid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "flavor", flavorid, "info"})
}

// GetAllFlavorSelector ...
func (gad *GAD) GetAllFlavorSelector(sysid string, tenantid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "flavor", "*", "info"})
}

// Node Flavor

// GetNodeFlavorInfoPath ...
func (gad *GAD) GetNodeFlavorInfoPath(sysid string, tenantid string, nodeid string, flavorid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "flavor", flavorid, "info"})
}

// GetAllNodeFlavorSelector ...
func (gad *GAD) GetAllNodeFlavorSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "flavor", "*", "info"})
}

// Node Network

// GetNodeNetworkFloatingIPInfoPath ...
func (gad *GAD) GetNodeNetworkFloatingIPInfoPath(sysid string, tenantid string, nodeid string, ipid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "floating-ips", ipid, "info"})
}

// GetNodeAllNetworkFloatingIPsSelector ...
func (gad *GAD) GetNodeAllNetworkFloatingIPsSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "floating-ips", "*", "info"})
}

// GetNodeNetworkPortsSelector ...
func (gad *GAD) GetNodeNetworkPortsSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "ports", "*", "info"})
}

// GetNodeNetworkPortInfoPath ...
func (gad *GAD) GetNodeNetworkPortInfoPath(sysid string, tenantid string, nodeid string, portid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "ports", portid, "info"})
}

// GetNodeNetworkRoutersSelector ...
func (gad *GAD) GetNodeNetworkRoutersSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "routers", "*", "info"})
}

// GetNodeNetworkRouterInfoPath ...
func (gad *GAD) GetNodeNetworkRouterInfoPath(sysid string, tenantid string, nodeid string, routerid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "routers", routerid, "info"})
}

// GetNodeNetworkInfoPath ...
func (gad *GAD) GetNodeNetworkInfoPath(sysid string, tenantid string, nodeid string, networkid string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", networkid, "info"})
}

// GetNodeNetworSelector ...
func (gad *GAD) GetNodeNetworSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "*", "info"})
}

// Evals

// GetAgentExecPath ...
func (gad *GAD) GetAgentExecPath(sysid string, tenantid string, nodeid string, funcname string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "agent", "exec", funcname})
}

// GetAgentExecSelectorWithParams ...
func (gad *GAD) GetAgentExecSelectorWithParams(sysid string, tenantid string, nodeid string, funcname string, params map[string]interface{}) *yaks.Selector {
	var f string
	if len(params) > 0 {
		p := Dict2Args(params)
		f = fmt.Sprintf("%s?%s", funcname, p)
	} else {
		f = funcname
	}
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "agent", "exec", f})
}

// ID Extraction

// ExtractUserIDFromPath ...
func (gad *GAD) ExtractUserIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[4]
}

// ExtractTenantIDFromPath ...
func (gad *GAD) ExtractTenantIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[4]
}

// ExtractEntityIDFromPath ...
func (gad *GAD) ExtractEntityIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[7]
}

// ExtractAtomicEntityIDFromPath ...
func (gad *GAD) ExtractAtomicEntityIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[7]
}

// ExtractAtomicEntityInstanceIDFromPath ...
func (gad *GAD) ExtractAtomicEntityInstanceIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[9]
}

// ExtractFDUIDFromPath ...
func (gad *GAD) ExtractFDUIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[7]
}

// ExtractNodeIDFromPath ...
func (gad *GAD) ExtractNodeIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractPluginIDFromPath ...
func (gad *GAD) ExtractPluginIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[8]
}

// ExtractPortIDFromPath ...
func (gad *GAD) ExtractPortIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractRouterIDFromPath ...
func (gad *GAD) ExtractRouterIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractNetworkIDFromPath ...
func (gad *GAD) ExtractNetworkIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[5]
}

// ExtractImageIDFromPath ...
func (gad *GAD) ExtractImageIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[5]
}

// ExtractFlavorIDFromPath ...
func (gad *GAD) ExtractFlavorIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[5]
}

// ExtractNodeFDUIDFromPath ...
func (gad *GAD) ExtractNodeFDUIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[8]
}

// ExtractNodeImageIDFromPath ...
func (gad *GAD) ExtractNodeImageIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[7]
}

// ExtractNodeFlavorIDFromPath ...
func (gad *GAD) ExtractNodeFlavorIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[7]
}

// ExtractNodeInstanceIDFromPath ...
func (gad *GAD) ExtractNodeInstanceIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[10]
}

// ExtractNodePortIDFromPath ...
func (gad *GAD) ExtractNodePortIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[9]
}

// ExtractNodeRouterIDFromPath ...
func (gad *GAD) ExtractNodeRouterIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[9]
}

// ExtractNodeFloatingIDFromPath ...
func (gad *GAD) ExtractNodeFloatingIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[9]
}

// ExtractNodeNetworkIDFromPath ...
func (gad *GAD) ExtractNodeNetworkIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[7]
}

// System

// GetSysInfo ...
func (gad *GAD) GetSysInfo(sysid string) (*SystemInfo, error) {
	s, _ := yaks.NewSelector(gad.GetSysInfoPath(sysid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Empty sys info", nil}
	}
	v := kvs[0].Value().ToString()
	sv := SystemInfo{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetSysConfig ...
func (gad *GAD) GetSysConfig(sysid string) (*SystemConfig, error) {
	s, _ := yaks.NewSelector(gad.GetSysConfigurationPath(sysid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Empty sys config", nil}
	}
	v := kvs[0].Value().ToString()
	sv := SystemConfig{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetAllUserIDs ...
func (gad *GAD) GetAllUserIDs(sysid string) ([]string, error) {
	s := gad.GetAllUsersSelector(sysid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractUserIDFromPath(p))
	}
	return ids, nil
}

// Tenant

// GetAllTenantsIDs ...
func (gad *GAD) GetAllTenantsIDs(sysid string) ([]string, error) {
	s := gad.GetAllTenantsSelector(sysid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractTenantIDFromPath(p))
	}
	return ids, nil
}

// GetAllNodes ...
func (gad *GAD) GetAllNodes(sysid string, tenantid string) ([]string, error) {
	s := gad.GetAllNodesSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeIDFromPath(p))
	}
	return ids, nil
}

// GetNodeInfo ...
func (gad *GAD) GetNodeInfo(sysid string, tenantid string, nodeid string) (*NodeInfo, error) {
	s, _ := yaks.NewSelector(gad.GetNodeInfoPath(sysid, tenantid, nodeid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Empty Node Info", nil}
	}
	v := kvs[0].Value().ToString()
	sv := NodeInfo{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeInfo ...
func (gad *GAD) AddNodeInfo(sysid string, tenantid string, nodeid string, info NodeInfo) error {
	s := gad.GetNodeInfoPath(sysid, tenantid, nodeid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeInfo ...
func (gad *GAD) RemoveNodeInfo(sysid string, tenantid string, nodeid string) error {
	s := gad.GetNodeInfoPath(sysid, tenantid, nodeid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeConfiguration ...
func (gad *GAD) GetNodeConfiguration(sysid string, tenantid string, nodeid string) (*NodeConfiguration, error) {
	s, _ := yaks.NewSelector(gad.GetNodeConfigurationPath(sysid, tenantid, nodeid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Empty Node Configuration", nil}
	}
	v := kvs[0].Value().ToString()
	sv := NodeConfiguration{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeConfiguration ...
func (gad *GAD) AddNodeConfiguration(sysid string, tenantid string, nodeid string, conf NodeConfiguration) error {
	s := gad.GetNodeConfigurationPath(sysid, tenantid, nodeid)
	v, err := json.Marshal(conf)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeConfiguration ...
func (gad *GAD) RemoveNodeConfiguration(sysid string, tenantid string, nodeid string) error {
	s := gad.GetNodeConfigurationPath(sysid, tenantid, nodeid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeStatus ...
func (gad *GAD) GetNodeStatus(sysid string, tenantid string, nodeid string) (*NodeStatus, error) {
	s, _ := yaks.NewSelector(gad.GetNodeStatusPath(sysid, tenantid, nodeid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Empty Node Status", nil}
	}
	v := kvs[0].Value().ToString()
	sv := NodeStatus{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeStatus ...
func (gad *GAD) AddNodeStatus(sysid string, tenantid string, nodeid string, info NodeStatus) error {
	s := gad.GetNodeStatusPath(sysid, tenantid, nodeid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeStatus ...
func (gad *GAD) RemoveNodeStatus(sysid string, tenantid string, nodeid string) error {
	s := gad.GetNodeStatusPath(sysid, tenantid, nodeid)
	err := gad.ws.Remove(s)
	return err
}

// ObserveNodeStatus ...
func (gad *GAD) ObserveNodeStatus(sysid string, tenantid string, nodeid string, listener func(NodeStatus)) error {
	s, _ := yaks.NewSelector(gad.GetNodeStatusPath(sysid, tenantid, nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := NodeStatus{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := gad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	gad.listeners = append(gad.listeners, sid)
	return nil
}

// Omiting Entities and Atomic Entities

// GetCatalogAllFDUs ...
func (gad *GAD) GetCatalogAllFDUs(sysid string, tenantid string) ([]string, error) {
	s := gad.GetCatalogAllFDUSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractFDUIDFromPath(p))
	}
	return ids, nil
}

// GetCatalogFDUInfo ...
func (gad *GAD) GetCatalogFDUInfo(sysid string, tenantid string, fduid string) (*FDU, error) {
	s, _ := yaks.NewSelector(gad.GetCatalogFDUInfoPath(sysid, tenantid, fduid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"FDU Not Found in catalog", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDU{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddCatalogFDUInfo ...
func (gad *GAD) AddCatalogFDUInfo(sysid string, tenantid string, fduid string, info FDU) error {
	s := gad.GetCatalogFDUInfoPath(sysid, tenantid, fduid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveCatalogFDUInfo ...
func (gad *GAD) RemoveCatalogFDUInfo(sysid string, tenantid string, fduid string) error {
	s := gad.GetNodeStatusPath(sysid, tenantid, fduid)
	err := gad.ws.Remove(s)
	return err
}

// ObserveCatalogFDUs ...
func (gad *GAD) ObserveCatalogFDUs(sysid string, tenantid string, fduid string, listener func(FDU)) error {
	s, _ := yaks.NewSelector(gad.GetCatalogFDUInfoPath(sysid, tenantid, fduid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := FDU{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := gad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	gad.listeners = append(gad.listeners, sid)
	return nil
}

// NodeFDU

// GetNodeFDUs ...
func (gad *GAD) GetNodeFDUs(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetNodeFDUSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeFDUIDFromPath(p))
	}
	return ids, nil
}

// GetFDUNodes ...
func (gad *GAD) GetFDUNodes(sysid string, tenantid string, fduid string) ([]string, error) {
	s := gad.GetNodeFDUInstancesSelector(sysid, tenantid, "*", fduid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeIDFromPath(p))
	}
	return ids, nil
}

// GetNodeFDUInstances ...
func (gad *GAD) GetNodeFDUInstances(sysid string, tenantid string, nodeid string, fduid string) ([]string, error) {
	s := gad.GetNodeFDUInstancesSelector(sysid, tenantid, nodeid, fduid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeInstanceIDFromPath(p))
	}
	return ids, nil
}

// GetNodeFDUInstance ...
func (gad *GAD) GetNodeFDUInstance(sysid string, tenantid string, nodeid string, instanceid string) (*FDURecord, error) {
	s := gad.GetNodeFDUInstanceSelector(sysid, tenantid, nodeid, instanceid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"FDU Instance Not Found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDURecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeFDU ...
func (gad *GAD) AddNodeFDU(sysid string, tenantid string, nodeid string, fduid string, instanceid string, info FDURecord) error {
	s := gad.GetNodeFDUInfoPath(sysid, tenantid, nodeid, fduid, instanceid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeFDU ...
func (gad *GAD) RemoveNodeFDU(sysid string, tenantid string, nodeid string, fduid string, instanceid string) error {
	s := gad.GetNodeFDUInfoPath(sysid, tenantid, nodeid, fduid, instanceid)
	err := gad.ws.Remove(s)
	return err
}

// ObserveNodeFDU ...
func (gad *GAD) ObserveNodeFDU(sysid string, tenantid string, nodeid string, listener func(FDURecord)) error {
	s, _ := yaks.NewSelector(gad.GetCatalogFDUInfoPath(sysid, tenantid, nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := FDURecord{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := gad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	gad.listeners = append(gad.listeners, sid)
	return nil
}

// Plugins

// GetAllPluginsIDs ...
func (gad *GAD) GetAllPluginsIDs(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetNodePluginsSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractPluginIDFromPath(p))
	}
	return ids, nil
}

// GetPluginInfo ...
func (gad *GAD) GetPluginInfo(sysid string, tenantid string, nodeid string, pluginid string) (*Plugin, error) {
	s, _ := yaks.NewSelector(gad.GetNodePluginInfoPath(sysid, tenantid, nodeid, pluginid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Plugin Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := Plugin{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodePlugin ...
func (gad *GAD) AddNodePlugin(sysid string, tenantid string, nodeid string, pluginid string, info Plugin) error {
	s := gad.GetNodePluginInfoPath(sysid, tenantid, nodeid, pluginid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// AddNodePluginEval ...
func (gad *GAD) AddNodePluginEval(sysid string, tenantid string, nodeid string, plugind string, funcname string, evalcb func(yaks.Properties) interface{}) error {
	s := gad.GetNodePluginEvalPath(sysid, tenantid, nodeid, plugind, funcname)

	cb := func(path *yaks.Path, props yaks.Properties) yaks.Value {
		v, _ := json.Marshal(evalcb(props))
		sv := yaks.NewStringValue(string(v))
		return sv
	}

	err := gad.ws.RegisterEval(s, cb)
	gad.evals = append(gad.evals, s)
	return err
}

// ObserveNodePlugins ...
func (gad *GAD) ObserveNodePlugins(sysid string, tenantid string, nodeid string, listener func(Plugin)) error {
	s := gad.GetNodePluginsSelector(sysid, tenantid, nodeid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := Plugin{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := gad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	gad.listeners = append(gad.listeners, sid)
	return nil
}

// Network

// GetNetworkPort ...
func (gad *GAD) GetNetworkPort(sysid string, tenantid string, portid string) (*ConnectionPointDescriptor, error) {
	s, _ := yaks.NewSelector(gad.GetNetworkPortInfoPath(sysid, tenantid, portid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Port not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := ConnectionPointDescriptor{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNetworkPort ...
func (gad *GAD) AddNetworkPort(sysid string, tenantid string, portid string, info ConnectionPointDescriptor) error {
	s := gad.GetNetworkPortInfoPath(sysid, tenantid, portid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNetworkPort ...
func (gad *GAD) RemoveNetworkPort(sysid string, tenantid string, portid string) error {
	s := gad.GetNetworkPortInfoPath(sysid, tenantid, portid)
	err := gad.ws.Remove(s)
	return err
}

// GetAllNetworkPorts ...
func (gad *GAD) GetAllNetworkPorts(sysid string, tenantid string) ([]string, error) {
	s := gad.GetAllPortsSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractPortIDFromPath(p))
	}
	return ids, nil
}

// GetNetworkRouter ...
func (gad *GAD) GetNetworkRouter(sysid string, tenantid string, portid string) (*RouterDescriptor, error) {
	s, _ := yaks.NewSelector(gad.GetNetworkPortInfoPath(sysid, tenantid, portid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Router not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := RouterDescriptor{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNetWorkRouter ...
func (gad *GAD) AddNetWorkRouter(sysid string, tenantid string, routerid string, info RouterDescriptor) error {
	s := gad.GetNetworkPortInfoPath(sysid, tenantid, routerid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNetworkRouter ...
func (gad *GAD) RemoveNetworkRouter(sysid string, tenantid string, routerid string) error {
	s := gad.GetNetworkPortInfoPath(sysid, tenantid, routerid)
	err := gad.ws.Remove(s)
	return err
}

// GetAllNetworkRouters ...
func (gad *GAD) GetAllNetworkRouters(sysid string, tenantid string) ([]string, error) {
	s := gad.GetAllRoutersSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractPortIDFromPath(p))
	}
	return ids, nil
}

// GetNetwork ...
func (gad *GAD) GetNetwork(sysid string, tenantid string, netid string) (*VirtualNetwork, error) {
	s, _ := yaks.NewSelector(gad.GetNetworkInfoPath(sysid, tenantid, netid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := VirtualNetwork{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNetwork ...
func (gad *GAD) AddNetwork(sysid string, tenantid string, netid string, info VirtualNetwork) error {
	s := gad.GetNetworkInfoPath(sysid, tenantid, netid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNetwork ...
func (gad *GAD) RemoveNetwork(sysid string, tenantid string, netid string) error {
	s := gad.GetNetworkInfoPath(sysid, tenantid, netid)
	err := gad.ws.Remove(s)
	return err
}

// GetAllNetwork ...
func (gad *GAD) GetAllNetwork(sysid string, tenantid string) ([]string, error) {
	s := gad.GetAllNetworksSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNetworkIDFromPath(p))
	}
	return ids, nil
}

// Images

// GetImage ...
func (gad *GAD) GetImage(sysid string, tenantid string, imageid string) (*FDUImage, error) {
	s, _ := yaks.NewSelector(gad.GetImageInfoPath(sysid, tenantid, imageid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Image not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDUImage{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddImage ...
func (gad *GAD) AddImage(sysid string, tenantid string, imageid string, info FDUImage) error {
	s := gad.GetImageInfoPath(sysid, tenantid, imageid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveImage ...
func (gad *GAD) RemoveImage(sysid string, tenantid string, imageid string) error {
	s := gad.GetImageInfoPath(sysid, tenantid, imageid)
	err := gad.ws.Remove(s)
	return err
}

// GetAllImages ...
func (gad *GAD) GetAllImages(sysid string, tenantid string) ([]string, error) {
	s := gad.GetAllImageSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractImageIDFromPath(p))
	}
	return ids, nil
}

// Node Images

// GetNodeImage ...
func (gad *GAD) GetNodeImage(sysid string, tenantid string, nodeid string, imageid string) (*FDUImage, error) {
	s, _ := yaks.NewSelector(gad.GetNodeImageInfoPath(sysid, tenantid, nodeid, imageid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Image not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDUImage{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeImage ...
func (gad *GAD) AddNodeImage(sysid string, tenantid string, nodeid string, imageid string, info FDUImage) error {
	s := gad.GetNodeImageInfoPath(sysid, tenantid, nodeid, imageid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeImage ...
func (gad *GAD) RemoveNodeImage(sysid string, tenantid string, nodeid string, imageid string) error {
	s := gad.GetNodeImageInfoPath(sysid, tenantid, nodeid, imageid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeAllImages ...
func (gad *GAD) GetNodeAllImages(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetAllNodeImageSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeImageIDFromPath(p))
	}
	return ids, nil
}

// Flavors

// GetFlavor ...
func (gad *GAD) GetFlavor(sysid string, tenantid string, flvid string) (*FDUComputationalRequirements, error) {
	s, _ := yaks.NewSelector(gad.GetFlavorInfoPath(sysid, tenantid, flvid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Flavor not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDUComputationalRequirements{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddFlavor ...
func (gad *GAD) AddFlavor(sysid string, tenantid string, flvid string, info FDUComputationalRequirements) error {
	s := gad.GetFlavorInfoPath(sysid, tenantid, flvid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveFlavor ...
func (gad *GAD) RemoveFlavor(sysid string, tenantid string, flvid string) error {
	s := gad.GetFlavorInfoPath(sysid, tenantid, flvid)
	err := gad.ws.Remove(s)
	return err
}

// GetAllFlavors ...
func (gad *GAD) GetAllFlavors(sysid string, tenantid string) ([]string, error) {
	s := gad.GetAllFlavorSelector(sysid, tenantid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractFlavorIDFromPath(p))
	}
	return ids, nil
}

// Node Flavor

// GetNodeFlavor ...
func (gad *GAD) GetNodeFlavor(sysid string, tenantid string, nodeid string, flvid string) (*FDUComputationalRequirements, error) {
	s, _ := yaks.NewSelector(gad.GetNodeFlavorInfoPath(sysid, tenantid, nodeid, flvid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Flavort not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDUComputationalRequirements{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeFlavor ...
func (gad *GAD) AddNodeFlavor(sysid string, tenantid string, nodeid string, flvid string, info FDUComputationalRequirements) error {
	s := gad.GetNodeFlavorInfoPath(sysid, tenantid, nodeid, flvid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeFlavor ...
func (gad *GAD) RemoveNodeFlavor(sysid string, tenantid string, nodeid string, flvid string) error {
	s := gad.GetNodeFlavorInfoPath(sysid, tenantid, nodeid, flvid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeAllFlavors ...
func (gad *GAD) GetNodeAllFlavors(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetAllNodeFlavorSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeFlavorIDFromPath(p))
	}
	return ids, nil
}

// Node Network

// GetNodeNetwork ...
func (gad *GAD) GetNodeNetwork(sysid string, tenantid string, nodeid string, netid string) (*VirtualNetwork, error) {
	s, _ := yaks.NewSelector(gad.GetNodeNetworkInfoPath(sysid, tenantid, nodeid, netid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := VirtualNetwork{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeNetwork ...
func (gad *GAD) AddNodeNetwork(sysid string, tenantid string, nodeid string, netid string, info VirtualNetwork) error {
	s := gad.GetNodeNetworkInfoPath(sysid, tenantid, nodeid, netid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeNetwork ...
func (gad *GAD) RemoveNodeNetwork(sysid string, tenantid string, nodeid string, netid string) error {
	s := gad.GetNodeNetworkInfoPath(sysid, tenantid, nodeid, netid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeAllNetworks ...
func (gad *GAD) GetNodeAllNetworks(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetNodeNetworSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeNetworkIDFromPath(p))
	}
	return ids, nil
}

// GetNodeFlatingIP ...
func (gad *GAD) GetNodeFlatingIP(sysid string, tenantid string, nodeid string, floatingid string) (*FloatingIPRecord, error) {
	s, _ := yaks.NewSelector(gad.GetNodeNetworkFloatingIPInfoPath(sysid, tenantid, nodeid, floatingid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Floating IP not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FloatingIPRecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeFloatingIP ...
func (gad *GAD) AddNodeFloatingIP(sysid string, tenantid string, nodeid string, floatingid string, info FloatingIPRecord) error {
	s := gad.GetNodeNetworkFloatingIPInfoPath(sysid, tenantid, nodeid, floatingid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeFloatingIP ...
func (gad *GAD) RemoveNodeFloatingIP(sysid string, tenantid string, nodeid string, floatingid string) error {
	s := gad.GetNodeNetworkFloatingIPInfoPath(sysid, tenantid, nodeid, floatingid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeAllFlatingIPs ...
func (gad *GAD) GetNodeAllFlatingIPs(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetNodeAllNetworkFloatingIPsSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeFloatingIDFromPath(p))
	}
	return ids, nil
}

// GetNodeNetworkPort ...
func (gad *GAD) GetNodeNetworkPort(sysid string, tenantid string, nodeid string, portid string) (*ConnectionPointRecord, error) {
	s, _ := yaks.NewSelector(gad.GetNodeNetworkPortInfoPath(sysid, tenantid, nodeid, portid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Port not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := ConnectionPointRecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeNetworkPort ...
func (gad *GAD) AddNodeNetworkPort(sysid string, tenantid string, nodeid string, portid string, info ConnectionPointRecord) error {
	s := gad.GetNodeNetworkPortInfoPath(sysid, tenantid, nodeid, portid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeNetworkPort ...
func (gad *GAD) RemoveNodeNetworkPort(sysid string, tenantid string, nodeid string, portid string) error {
	s := gad.GetNodeNetworkPortInfoPath(sysid, tenantid, nodeid, portid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeAllNetworkPorts ...
func (gad *GAD) GetNodeAllNetworkPorts(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetNodeNetworkPortsSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodePortIDFromPath(p))
	}
	return ids, nil
}

// GetNodeNetworkRouter ...
func (gad *GAD) GetNodeNetworkRouter(sysid string, tenantid string, nodeid string, routerid string) (*RouterRecord, error) {
	s, _ := yaks.NewSelector(gad.GetNodeNetworkRouterInfoPath(sysid, tenantid, nodeid, routerid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Router not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := RouterRecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeNetworkRouter ...
func (gad *GAD) AddNodeNetworkRouter(sysid string, tenantid string, nodeid string, routerid string, info RouterRecord) error {
	s := gad.GetNodeNetworkRouterInfoPath(sysid, tenantid, nodeid, routerid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = gad.ws.Put(s, sv)
	return err
}

// RemoveNodeNetworkRouter ...
func (gad *GAD) RemoveNodeNetworkRouter(sysid string, tenantid string, nodeid string, routerid string) error {
	s := gad.GetNodeNetworkRouterInfoPath(sysid, tenantid, nodeid, routerid)
	err := gad.ws.Remove(s)
	return err
}

// GetNodeAllNetworkRouters ...
func (gad *GAD) GetNodeAllNetworkRouters(sysid string, tenantid string, nodeid string) ([]string, error) {
	s := gad.GetNodeNetworkRoutersSelector(sysid, tenantid, nodeid)
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, gad.ExtractNodeRouterIDFromPath(p))
	}
	return ids, nil
}

// ObserveNodeNetworkRouters ...
func (gad *GAD) ObserveNodeNetworkRouters(sysid string, tenantid string, nodeid string, listener func(RouterRecord)) error {
	s, _ := yaks.NewSelector(gad.GetNodeNetworkRoutersSelector(sysid, tenantid, nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := RouterRecord{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := gad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	gad.listeners = append(gad.listeners, sid)
	return nil
}

// Agent Evals

// AddNodePortToNetwork ...
func (gad *GAD) AddNodePortToNetwork(sysid string, tenantid string, nodeid string, portid string, netid string) (*EvalResult, error) {

	fname := "add_port_to_network"
	params := make(map[string]interface{})

	params["cp_uuid"] = portid
	params["network_uuid"] = netid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"AddNodePortToNetwork function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// RemoveNodePortFromNetwork ...
func (gad *GAD) RemoveNodePortFromNetwork(sysid string, tenantid string, nodeid string, portid string) (*EvalResult, error) {

	fname := "remove_port_from_network"
	params := make(map[string]interface{})

	params["cp_uuid"] = portid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"RemoveNodePortFromNetwork function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// CrateFloatingIPInNode ...
func (gad *GAD) CrateFloatingIPInNode(sysid string, tenantid string, nodeid string) (*EvalResult, error) {

	fname := "create_floating_ip"

	s, _ := yaks.NewSelector(gad.GetAgentExecPath(sysid, tenantid, nodeid, fname).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"CrateFloatingIPInNode function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// RemoveFloatingIPFromNode ...
func (gad *GAD) RemoveFloatingIPFromNode(sysid string, tenantid string, nodeid string, ipid string) (*EvalResult, error) {

	fname := "delete_floating_ip"
	params := make(map[string]interface{})

	params["floating_uuid"] = ipid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"RemoveFloatingIPFromNode function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AssignNodeFloatingIP ...
func (gad *GAD) AssignNodeFloatingIP(sysid string, tenantid string, nodeid string, ipid string, cpid string) (*EvalResult, error) {

	fname := "remove_floating_ip"
	params := make(map[string]interface{})

	params["floating_uuid"] = ipid
	params["cp_uuid"] = cpid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"AssignNodeFloatingIP function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// RetainNodeFloatingIP ...
func (gad *GAD) RetainNodeFloatingIP(sysid string, tenantid string, nodeid string, ipid string, cpid string) (*EvalResult, error) {

	fname := "remove_floating_ip"
	params := make(map[string]interface{})

	params["floating_uuid"] = ipid
	params["cp_uuid"] = cpid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"RetainNodeFloatingIP function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddPortToRouter ...
func (gad *GAD) AddPortToRouter(sysid string, tenantid string, nodeid string, routerid string, porttype string, vnetid *string, ipaddress *string) (*EvalResult, error) {

	fname := "add_router_port"
	params := make(map[string]interface{})

	params["router_id"] = routerid
	params["port_type"] = porttype
	if vnetid != nil {
		params["vnet_id"] = *vnetid
	}
	if ipaddress != nil {
		params["ip_address"] = *ipaddress
	}

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"AddPortToRouter function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// RemovePortFromRouter ...
func (gad *GAD) RemovePortFromRouter(sysid string, tenantid string, nodeid string, routerid string, vnetid string) (*EvalResult, error) {

	fname := "remove_router_port"
	params := make(map[string]interface{})

	params["router_id"] = routerid
	params["vnet_id"] = vnetid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"RemovePortFromRouter function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// OnboardFDUFromNode ...
func (gad *GAD) OnboardFDUFromNode(sysid string, tenantid string, nodeid string, fduid string, info FDU) (*EvalResult, error) {

	fname := "onboard_fdu"
	params := make(map[string]interface{})

	d, err := json.Marshal(info)

	params["descriptor"] = string(d)

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"OnboardFDUFromNode function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err = json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// DefineFDUInNode ...
func (gad *GAD) DefineFDUInNode(sysid string, tenantid string, nodeid string, fduid string) (*EvalResult, error) {

	fname := "define_fdu"
	params := make(map[string]interface{})

	params["fdu_id"] = fduid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"DefineFDUInNode function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// CreateNetworkInNode ...
func (gad *GAD) CreateNetworkInNode(sysid string, tenantid string, nodeid string, netid string, info VirtualNetwork) (*EvalResult, error) {

	fname := "create_node_network"
	params := make(map[string]interface{})

	d, err := json.Marshal(info)

	params["descriptor"] = string(d)

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"CreateNetworkInNode function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err = json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// RemoveNetworkFromNode ...
func (gad *GAD) RemoveNetworkFromNode(sysid string, tenantid string, nodeid string, netid string) (*EvalResult, error) {

	fname := "remove_node_netwotk"
	params := make(map[string]interface{})

	params["net_id"] = netid

	s, _ := yaks.NewSelector(gad.GetAgentExecSelectorWithParams(sysid, tenantid, nodeid, fname, params).ToString())

	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"RemoveNetworkFromNode function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// LAD is Local Actual Desired
type LAD struct {
	ws        *yaks.Workspace
	prefix    string
	listeners []*yaks.SubscriptionID
	evals     []*yaks.Path
}

// Node

// GetNodeInfoPath ...
func (lad *LAD) GetNodeInfoPath(nodeid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "info"})
}

// GetNodeConfigurationPath ...
func (lad *LAD) GetNodeConfigurationPath(nodeid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "configuration"})
}

// GetNodeStatusPath ...
func (lad *LAD) GetNodeStatusPath(nodeid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "status"})
}

// GetNodePlguinsSelector ...
func (lad *LAD) GetNodePlguinsSelector(nodeid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "plugins", "*", "info"})
}

// GetNodePlguinsSubscriberSelector ...
func (lad *LAD) GetNodePlguinsSubscriberSelector(nodeid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "plugins", "**"})
}

// GetNodePlguinInfoPath ...
func (lad *LAD) GetNodePlguinInfoPath(nodeid string, pluginid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "plugins", pluginid, "info"})
}

// GetNodeRuntimesSelector ...
func (lad *LAD) GetNodeRuntimesSelector(nodeid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "runtimes", "**"})
}

// GetNodeNetworkManagersSelector ...
func (lad *LAD) GetNodeNetworkManagersSelector(nodeid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "network_managers", "*"})
}

// Node FDU

// GetNodeRuntimeFDUsSelector ...
func (lad *LAD) GetNodeRuntimeFDUsSelector(nodeid string, pluginid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "runtimes", pluginid, "fdu", "*", "instances", "*", "info"})
}

// GetNodeRuntimeFDUsSubcrinerSelector ...
func (lad *LAD) GetNodeRuntimeFDUsSubcrinerSelector(nodeid string, pluginid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "runtimes", pluginid, "fdu", "*", "instances", "*", "info"})
}

// GetNodeRuntimeFDUInfoPath ...
func (lad *LAD) GetNodeRuntimeFDUInfoPath(nodeid string, pluginid string, fduid string, instanceid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "runtimes", pluginid, "fdu", fduid, "instances", instanceid, "info"})
}

// GetNodeFDUInstancesSelector ...
func (lad *LAD) GetNodeFDUInstancesSelector(nodeid string, fduid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "runtimes", "*", "fdu", fduid, "instances", "*", "info"})
}

// GetNodeFDUInstanceSelector ...
func (lad *LAD) GetNodeFDUInstanceSelector(nodeid string, instanceid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "runtimes", "*", "fdu", "*", "instances", instanceid, "info"})
}

// GetNodeFDUIAllnstancesSelector ...
func (lad *LAD) GetNodeFDUIAllnstancesSelector(nodeid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "runtimes", "*", "fdu", "*", "instances", "*", "info"})
}

// Node Images

// GetNodeIimageInfoPath ...
func (lad *LAD) GetNodeIimageInfoPath(nodeid string, pluginid string, imgid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "runtimes", pluginid, "images", imgid, "info"})
}

// Node Flavors

// GetNodeFlavorInfoPath ...
func (lad *LAD) GetNodeFlavorInfoPath(nodeid string, pluginid string, flvid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "runtimes", pluginid, "flavors", flvid, "info"})
}

// Node Networks

// GetNodeNetworksSelector ...
func (lad *LAD) GetNodeNetworksSelector(nodeid string, pluginid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "network_manager", pluginid, "networks", "*", "info"})
}

// GetNodeNetworksFindSelector ...
func (lad *LAD) GetNodeNetworksFindSelector(nodeid string, netid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "network_manager", "*", "networks", netid, "info"})
}

// GetNodeNetworkInfoPath ...
func (lad *LAD) GetNodeNetworkInfoPath(nodeid string, pluginid string, netid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "network_manager", pluginid, "networks", netid, "info"})
}

// GetNodeNetworkPortInfoPath ...
func (lad *LAD) GetNodeNetworkPortInfoPath(nodeid string, pluginid string, portid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "network_manager", pluginid, "ports", portid, "info"})
}

// GetNodeNetworkPortsSelector ...
func (lad *LAD) GetNodeNetworkPortsSelector(nodeid string, pluginid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "network_manager", pluginid, "ports", "*", "info"})
}

// GetNodeNetworkRouterInfoPath ...
func (lad *LAD) GetNodeNetworkRouterInfoPath(nodeid string, pluginid string, routerid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "network_manager", pluginid, "routers", routerid, "info"})
}

// GetNodeNetworkRoutersSelector ...
func (lad *LAD) GetNodeNetworkRoutersSelector(nodeid string, pluginid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "network_manager", pluginid, "routers", "*", "info"})
}

// GetNodeNetworkFloatingIPInfoPath ...
func (lad *LAD) GetNodeNetworkFloatingIPInfoPath(nodeid string, pluginid string, ipid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "network_manager", pluginid, "floating-ips", ipid, "info"})
}

// GetNodeNetworkFloatingIPsSelector ...
func (lad *LAD) GetNodeNetworkFloatingIPsSelector(nodeid string, pluginid string) *yaks.Selector {
	return CreateSelector([]string{lad.prefix, nodeid, "network_manager", pluginid, "floating-ips", "*", "info"})
}

// Node Evals

// GetAgentExecPath ...
func (lad *LAD) GetAgentExecPath(nodeid string, funcname string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "agent", "exec", funcname})
}

// GetAgentExecSelectorWithParams ...
func (lad *LAD) GetAgentExecSelectorWithParams(nodeid string, funcname string, params map[string]interface{}) *yaks.Selector {
	var f string
	if len(params) > 0 {
		p := Dict2Args(params)
		f = fmt.Sprintf("%s?%s", funcname, p)
	} else {
		f = funcname
	}
	return CreateSelector([]string{lad.prefix, nodeid, "agent", "exec", f})
}

// GetNodeOSExecPath ...
func (lad *LAD) GetNodeOSExecPath(nodeid string, funcname string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "os", "exec", funcname})
}

// GetNodeOSExecSelectorWithParams ...
func (lad *LAD) GetNodeOSExecSelectorWithParams(nodeid string, funcname string, params map[string]interface{}) *yaks.Selector {
	var f string
	if len(params) > 0 {
		p := Dict2Args(params)
		f = fmt.Sprintf("%s?%s", funcname, p)
	} else {
		f = funcname
	}
	return CreateSelector([]string{lad.prefix, nodeid, "os", "exec", f})
}

// GetNodeNMExecPath ...
func (lad *LAD) GetNodeNMExecPath(nodeid string, pluginid string, funcname string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "network_managers", pluginid, "exec", funcname})
}

// GetNodeNMExecSelectorWithParams ...
func (lad *LAD) GetNodeNMExecSelectorWithParams(nodeid string, pluginid string, funcname string, params map[string]interface{}) *yaks.Selector {
	var f string
	if len(params) > 0 {
		p := Dict2Args(params)
		f = fmt.Sprintf("%s?%s", funcname, p)
	} else {
		f = funcname
	}
	return CreateSelector([]string{lad.prefix, nodeid, "network_managers", pluginid, "exec", f})
}

// GetNodePluginEvalPath ...
func (lad *LAD) GetNodePluginEvalPath(nodeid string, pluginid string, funcname string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "plugins", pluginid, "exec", funcname})
}

// GetNodePluginEvalSelectorWithParams ...
func (lad *LAD) GetNodePluginEvalSelectorWithParams(nodeid string, pluginid string, funcname string, params map[string]interface{}) *yaks.Selector {
	var f string
	if len(params) > 0 {
		p := Dict2Args(params)
		f = fmt.Sprintf("%s?%s", funcname, p)
	} else {
		f = funcname
	}
	return CreateSelector([]string{lad.prefix, nodeid, "plugins", pluginid, "exec", f})
}

// GetNodeOSInfoPath ...
func (lad *LAD) GetNodeOSInfoPath(nodeid string) *yaks.Path {
	return CreatePath([]string{lad.prefix, nodeid, "os", "info"})
}

// ID Extraction

// ExtractNodeIDFromPath ...
func (lad *LAD) ExtractNodeIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[2]
}

// ExtractPluginIDFromPath ...
func (lad *LAD) ExtractPluginIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[4]
}

// ExtractNodeFDUIDFromPath ...
func (lad *LAD) ExtractNodeFDUIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractNodeInstanceIDFromPath ...
func (lad *LAD) ExtractNodeInstanceIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[8]
}

// ExtractNodeRouterIDFromPath ...
func (lad *LAD) ExtractNodeRouterIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractNodeNetworkIDFromPath ...
func (lad *LAD) ExtractNodeNetworkIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractNodePortIDFromPath ...
func (lad *LAD) ExtractNodePortIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// ExtractNodeFloatingIPIDFromPath ...
func (lad *LAD) ExtractNodeFloatingIPIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[6]
}

// Node Evals

// AddOSEval ...
func (lad *LAD) AddOSEval(nodeid string, funcname string, evalcb func(yaks.Properties) interface{}) error {
	s := lad.GetNodeOSExecPath(nodeid, funcname)

	cb := func(path *yaks.Path, props yaks.Properties) yaks.Value {
		v, _ := json.Marshal(evalcb(props))
		sv := yaks.NewStringValue(string(v))
		return sv
	}

	err := lad.ws.RegisterEval(s, cb)
	lad.evals = append(lad.evals, s)
	return err
}

// AddNMEval ...
func (lad *LAD) AddNMEval(nodeid string, pluginid string, funcname string, evalcb func(yaks.Properties) interface{}) error {
	s := lad.GetNodeNMExecPath(nodeid, pluginid, funcname)

	cb := func(path *yaks.Path, props yaks.Properties) yaks.Value {
		v, _ := json.Marshal(evalcb(props))
		sv := yaks.NewStringValue(string(v))
		return sv
	}

	err := lad.ws.RegisterEval(s, cb)
	lad.evals = append(lad.evals, s)
	return err
}

// AddPluginEval ...
func (lad *LAD) AddPluginEval(nodeid string, pluginid string, funcname string, evalcb func(yaks.Properties) interface{}) error {
	s := lad.GetNodePluginEvalPath(nodeid, pluginid, funcname)

	cb := func(path *yaks.Path, props yaks.Properties) yaks.Value {
		v, _ := json.Marshal(evalcb(props))
		sv := yaks.NewStringValue(string(v))
		return sv
	}

	err := lad.ws.RegisterEval(s, cb)
	lad.evals = append(lad.evals, s)
	return err
}

// ExecAgentEval ...
func (lad *LAD) ExecAgentEval(nodeid string, fname string, props map[string]interface{}) (*EvalResult, error) {

	var s *yaks.Selector
	if len(props) == 0 {
		s, _ = yaks.NewSelector(lad.GetAgentExecPath(nodeid, fname).ToString())
	} else {
		s = lad.GetAgentExecSelectorWithParams(nodeid, fname, props)
	}

	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"ExecAgentEval function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ExecOSEval ...
func (lad *LAD) ExecOSEval(nodeid string, fname string, props map[string]interface{}) (*EvalResult, error) {

	var s *yaks.Selector
	if len(props) == 0 {
		s, _ = yaks.NewSelector(lad.GetNodeOSExecPath(nodeid, fname).ToString())
	} else {
		s = lad.GetNodeOSExecSelectorWithParams(nodeid, fname, props)
	}

	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"ExecOSEval function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ExecNMEval ...
func (lad *LAD) ExecNMEval(nodeid string, pluginid string, fname string, props map[string]interface{}) (*EvalResult, error) {

	var s *yaks.Selector
	if len(props) == 0 {
		s, _ = yaks.NewSelector(lad.GetNodeNMExecPath(nodeid, pluginid, fname).ToString())
	} else {
		s = lad.GetNodeNMExecSelectorWithParams(nodeid, pluginid, fname, props)
	}

	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"ExecNMEval function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ExecPluginEval ...
func (lad *LAD) ExecPluginEval(nodeid string, pluginid string, fname string, props map[string]interface{}) (*EvalResult, error) {

	var s *yaks.Selector
	if len(props) == 0 {
		s, _ = yaks.NewSelector(lad.GetNodePluginEvalPath(nodeid, pluginid, fname).ToString())
	} else {
		s = lad.GetNodePluginEvalSelectorWithParams(nodeid, pluginid, fname, props)
	}

	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"ExecPluginEval function replied nil", nil}
	}
	v := kvs[0].Value().ToString()
	sv := EvalResult{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// Node

// AddNodePlugin ...
func (lad *LAD) AddNodePlugin(nodeid string, pluginid string, info Plugin) error {
	s := lad.GetNodePlguinInfoPath(nodeid, pluginid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// GetAllPlugins ...
func (lad *LAD) GetAllPlugins(nodeid string) ([]string, error) {
	s := lad.GetNodePlguinsSelector(nodeid)
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, lad.ExtractPluginIDFromPath(p))
	}
	return ids, nil
}

// GetNodePlugin ...
func (lad *LAD) GetNodePlugin(nodeid string, pluginid string) (*Plugin, error) {
	s, _ := yaks.NewSelector(lad.GetNodePlguinInfoPath(nodeid, pluginid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Plugin not Found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := Plugin{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// AddNodeInformation ...
func (lad *LAD) AddNodeInformation(nodeid string, info NodeInfo) error {
	s := lad.GetNodeInfoPath(nodeid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeInformation ...
func (lad *LAD) RemoveNodeInformation(nodeid string) error {
	s := lad.GetNodeInfoPath(nodeid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeInformation ...
func (lad *LAD) GetNodeInformation(nodeid string) (*NodeInfo, error) {
	s, _ := yaks.NewSelector(lad.GetNodeInfoPath(nodeid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Node information emtpy", nil}
	}
	v := kvs[0].Value().ToString()
	sv := NodeInfo{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ObserveNodeInformation ...
func (lad *LAD) ObserveNodeInformation(nodeid string, listener func(NodeInfo)) error {
	s, _ := yaks.NewSelector(lad.GetNodeInfoPath(nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := NodeInfo{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// AddNodeStatus ...
func (lad *LAD) AddNodeStatus(nodeid string, info NodeStatus) error {
	s := lad.GetNodeStatusPath(nodeid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeStatus ...
func (lad *LAD) RemoveNodeStatus(nodeid string) error {
	s := lad.GetNodeStatusPath(nodeid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeStatus ...
func (lad *LAD) GetNodeStatus(nodeid string) (*NodeStatus, error) {
	s, _ := yaks.NewSelector(lad.GetNodeStatusPath(nodeid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Node status emtpy", nil}
	}
	v := kvs[0].Value().ToString()
	sv := NodeStatus{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ObserveNodeStatus ...
func (lad *LAD) ObserveNodeStatus(nodeid string, listener func(NodeStatus)) error {
	s, _ := yaks.NewSelector(lad.GetNodeStatusPath(nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := NodeStatus{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// AddNodeConfiguration ...
func (lad *LAD) AddNodeConfiguration(nodeid string, info NodeConfiguration) error {
	s := lad.GetNodeConfigurationPath(nodeid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeConfiguration ...
func (lad *LAD) RemoveNodeConfiguration(nodeid string) error {
	s := lad.GetNodeConfigurationPath(nodeid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeConfiguration ...
func (lad *LAD) GetNodeConfiguration(nodeid string) (*NodeConfiguration, error) {
	s, _ := yaks.NewSelector(lad.GetNodeConfigurationPath(nodeid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Node configuration emtpy", nil}
	}
	v := kvs[0].Value().ToString()
	sv := NodeConfiguration{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ObserveNodeConfiguration ...
func (lad *LAD) ObserveNodeConfiguration(nodeid string, listener func(NodeConfiguration)) error {
	s, _ := yaks.NewSelector(lad.GetNodeConfigurationPath(nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := NodeConfiguration{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// ObserveNodePlugins ...
func (lad *LAD) ObserveNodePlugins(nodeid string, listener func(Plugin)) error {
	s := lad.GetNodePlguinsSelector(nodeid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := Plugin{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// AddNodeOSInfo ...
func (lad *LAD) AddNodeOSInfo(nodeid string, info map[string]interface{}) error {
	s := lad.GetNodeOSInfoPath(nodeid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeOSInfo ...
func (lad *LAD) RemoveNodeOSInfo(nodeid string) error {
	s := lad.GetNodeOSInfoPath(nodeid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeOSInfo ...
func (lad *LAD) GetNodeOSInfo(nodeid string) (*map[string]interface{}, error) {
	s, _ := yaks.NewSelector(lad.GetNodeOSInfoPath(nodeid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Node OS info emtpy", nil}
	}
	v := kvs[0].Value().ToString()
	sv := map[string]interface{}{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// ObserveNodeOSInfo ...
func (lad *LAD) ObserveNodeOSInfo(nodeid string, listener func(map[string]interface{})) error {
	s, _ := yaks.NewSelector(lad.GetNodeInfoPath(nodeid).ToString())

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := map[string]interface{}{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// Node FDU

// AddNodeFDU ...
func (lad *LAD) AddNodeFDU(nodeid string, pluginid string, fduid string, instanceid string, info FDURecord) error {
	s := lad.GetNodeRuntimeFDUInfoPath(nodeid, pluginid, fduid, instanceid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeFDU ...
func (lad *LAD) RemoveNodeFDU(nodeid string, pluginid string, fduid string, instanceid string) error {
	s := lad.GetNodeRuntimeFDUInfoPath(nodeid, pluginid, fduid, instanceid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeFDU ...
func (lad *LAD) GetNodeFDU(nodeid string, pluginid string, fduid string, instanceid string) (*FDURecord, error) {
	s, _ := yaks.NewSelector(lad.GetNodeRuntimeFDUInfoPath(nodeid, pluginid, fduid, instanceid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"FDU Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDURecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetNodeFDUInstances ...
func (lad *LAD) GetNodeFDUInstances(nodeid string, fduid string) ([]string, error) {
	s := lad.GetNodeFDUInstancesSelector(nodeid, fduid)
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return []string{}, nil
	}
	var ids []string = []string{}
	for _, kv := range kvs {
		p := kv.Path()
		ids = append(ids, lad.ExtractNodeInstanceIDFromPath(p))
	}
	return ids, nil
}

// GetNodeAllFDUsInstances ...
func (lad *LAD) GetNodeAllFDUsInstances(nodeid string) ([]FDURecord, error) {
	s := lad.GetNodeFDUIAllnstancesSelector(nodeid)
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return []FDURecord{}, nil
	}
	var instances []FDURecord = []FDURecord{}
	for _, kv := range kvs {
		v := kv.Value().ToString()
		sv := FDURecord{}
		err := json.Unmarshal([]byte(v), &sv)
		if err != nil {
			return nil, err
		}
		instances = append(instances, sv)
	}
	return instances, nil
}

// ObserveNodeRuntimeFDU ...
func (lad *LAD) ObserveNodeRuntimeFDU(nodeid string, pluginid string, listener func(FDURecord)) error {
	s := lad.GetNodeRuntimeFDUsSelector(nodeid, pluginid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := FDURecord{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// Node Images

// AddNodeImage ...
func (lad *LAD) AddNodeImage(nodeid string, pluginid string, imgid string, info FDUImage) error {
	s := lad.GetNodeIimageInfoPath(nodeid, pluginid, imgid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeImage ...
func (lad *LAD) RemoveNodeImage(nodeid string, pluginid string, imgid string) error {
	s := lad.GetNodeIimageInfoPath(nodeid, pluginid, imgid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeImage ...
func (lad *LAD) GetNodeImage(nodeid string, pluginid string, imgid string) (*FDUImage, error) {
	s, _ := yaks.NewSelector(lad.GetNodeIimageInfoPath(nodeid, pluginid, imgid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Image Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDUImage{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// Node Flavors

// AddNodeFlavor ...
func (lad *LAD) AddNodeFlavor(nodeid string, pluginid string, flvid string, info FDUComputationalRequirements) error {
	s := lad.GetNodeFlavorInfoPath(nodeid, pluginid, flvid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeFlavor ...
func (lad *LAD) RemoveNodeFlavor(nodeid string, pluginid string, flvid string) error {
	s := lad.GetNodeFlavorInfoPath(nodeid, pluginid, flvid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeFlavor ...
func (lad *LAD) GetNodeFlavor(nodeid string, pluginid string, flvid string) (*FDUComputationalRequirements, error) {
	s, _ := yaks.NewSelector(lad.GetNodeIimageInfoPath(nodeid, pluginid, flvid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Flavor Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FDUComputationalRequirements{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// Node Network

// AddNodeNetwork ...
func (lad *LAD) AddNodeNetwork(nodeid string, pluginid string, netid string, info VirtualNetwork) error {
	s := lad.GetNodeNetworkInfoPath(nodeid, pluginid, netid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeNetwork ...
func (lad *LAD) RemoveNodeNetwork(nodeid string, pluginid string, netid string) error {
	s := lad.GetNodeNetworkInfoPath(nodeid, pluginid, netid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeNetwork ...
func (lad *LAD) GetNodeNetwork(nodeid string, pluginid string, netid string) (*VirtualNetwork, error) {
	s, _ := yaks.NewSelector(lad.GetNodeNetworkInfoPath(nodeid, pluginid, netid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := VirtualNetwork{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// FindNodeNetwork ...
func (lad *LAD) FindNodeNetwork(nodeid string, netid string) (*VirtualNetwork, error) {
	s := lad.GetNodeNetworksFindSelector(nodeid, netid)
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Network Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := VirtualNetwork{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetAllNodeNetworks ...
func (lad *LAD) GetAllNodeNetworks(nodeid string, plugindid string) ([]VirtualNetwork, error) {
	var nets []VirtualNetwork = []VirtualNetwork{}
	s := lad.GetNodeNetworksSelector(nodeid, plugindid)
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nets, nil
	}

	for _, kv := range kvs {
		v := kv.Value().ToString()
		sv := VirtualNetwork{}
		err := json.Unmarshal([]byte(v), &sv)
		if err != nil {
			return nil, err
		}
		nets = append(nets, sv)
	}
	return nets, nil
}

// ObserveNodeNetworks ...
func (lad *LAD) ObserveNodeNetworks(nodeid string, pluginid string, listener func(VirtualNetwork)) error {
	s := lad.GetNodeNetworksSelector(nodeid, pluginid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := VirtualNetwork{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// AddNodePort ...
func (lad *LAD) AddNodePort(nodeid string, pluginid string, portid string, info ConnectionPointDescriptor) error {
	s := lad.GetNodeNetworkPortInfoPath(nodeid, pluginid, portid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodePort ...
func (lad *LAD) RemoveNodePort(nodeid string, pluginid string, portid string) error {
	s := lad.GetNodeNetworkPortInfoPath(nodeid, pluginid, portid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodePort ...
func (lad *LAD) GetNodePort(nodeid string, pluginid string, portid string) (*ConnectionPointDescriptor, error) {
	s, _ := yaks.NewSelector(lad.GetNodeNetworkInfoPath(nodeid, pluginid, portid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Port Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := ConnectionPointDescriptor{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetAllNodePorts ...
func (lad *LAD) GetAllNodePorts(nodeid string, plugindid string) ([]ConnectionPointDescriptor, error) {
	s := lad.GetNodeNetworksSelector(nodeid, plugindid)
	var ports []ConnectionPointDescriptor = []ConnectionPointDescriptor{}
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return ports, nil
	}

	for _, kv := range kvs {
		v := kv.Value().ToString()
		sv := ConnectionPointDescriptor{}
		err := json.Unmarshal([]byte(v), &sv)
		if err != nil {
			return nil, err
		}
		ports = append(ports, sv)
	}
	return ports, nil
}

// ObserveNodePorts ...
func (lad *LAD) ObserveNodePorts(nodeid string, pluginid string, listener func(ConnectionPointDescriptor)) error {
	s := lad.GetNodeNetworkPortsSelector(nodeid, pluginid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := ConnectionPointDescriptor{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// AddNodeRouter ...
func (lad *LAD) AddNodeRouter(nodeid string, pluginid string, routerid string, info RouterRecord) error {
	s := lad.GetNodeNetworkRouterInfoPath(nodeid, pluginid, routerid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeRouter ...
func (lad *LAD) RemoveNodeRouter(nodeid string, pluginid string, routerid string) error {
	s := lad.GetNodeNetworkRouterInfoPath(nodeid, pluginid, routerid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeRouter ...
func (lad *LAD) GetNodeRouter(nodeid string, pluginid string, routerid string) (*RouterRecord, error) {
	s, _ := yaks.NewSelector(lad.GetNodeNetworkRouterInfoPath(nodeid, pluginid, routerid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Router Not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := RouterRecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetAllNodeRouters ...
func (lad *LAD) GetAllNodeRouters(nodeid string, plugindid string) ([]RouterRecord, error) {
	s := lad.GetNodeNetworkRoutersSelector(nodeid, plugindid)
	var routers []RouterRecord = []RouterRecord{}
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return routers, nil
	}

	for _, kv := range kvs {
		v := kv.Value().ToString()
		sv := RouterRecord{}
		err := json.Unmarshal([]byte(v), &sv)
		if err != nil {
			return nil, err
		}
		routers = append(routers, sv)
	}
	return routers, nil
}

// ObserveNodeRouters ...
func (lad *LAD) ObserveNodeRouters(nodeid string, pluginid string, listener func(RouterRecord)) error {
	s := lad.GetNodeNetworkRoutersSelector(nodeid, pluginid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := RouterRecord{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// AddNodeFloatingIP ...
func (lad *LAD) AddNodeFloatingIP(nodeid string, pluginid string, ipid string, info FloatingIPRecord) error {
	s := lad.GetNodeNetworkFloatingIPInfoPath(nodeid, pluginid, ipid)
	v, err := json.Marshal(info)
	if err != nil {
		return err
	}
	sv := yaks.NewStringValue(string(v))
	err = lad.ws.Put(s, sv)
	return err
}

// RemoveNodeFloatingIP ...
func (lad *LAD) RemoveNodeFloatingIP(nodeid string, pluginid string, ipid string) error {
	s := lad.GetNodeNetworkFloatingIPInfoPath(nodeid, pluginid, ipid)
	err := lad.ws.Remove(s)
	return err
}

// GetNodeFloatingIP ...
func (lad *LAD) GetNodeFloatingIP(nodeid string, pluginid string, ipid string) (*FloatingIPRecord, error) {
	s, _ := yaks.NewSelector(lad.GetNodeNetworkFloatingIPInfoPath(nodeid, pluginid, ipid).ToString())
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, &FError{"Floating IP not found", nil}
	}
	v := kvs[0].Value().ToString()
	sv := FloatingIPRecord{}
	err := json.Unmarshal([]byte(v), &sv)
	if err != nil {
		return nil, err
	}
	return &sv, nil
}

// GetAllNodeFloatingIPs ...
func (lad *LAD) GetAllNodeFloatingIPs(nodeid string, plugindid string) ([]FloatingIPRecord, error) {
	s := lad.GetNodeNetworkFloatingIPsSelector(nodeid, plugindid)
	var ips []FloatingIPRecord = []FloatingIPRecord{}
	kvs := lad.ws.Get(s)
	if len(kvs) == 0 {
		return ips, nil
	}

	for _, kv := range kvs {
		v := kv.Value().ToString()
		sv := FloatingIPRecord{}
		err := json.Unmarshal([]byte(v), &sv)
		if err != nil {
			return nil, err
		}
		ips = append(ips, sv)
	}
	return ips, nil
}

// ObserveNodeFloatingIPs ...
func (lad *LAD) ObserveNodeFloatingIPs(nodeid string, pluginid string, listener func(FloatingIPRecord)) error {
	s := lad.GetNodeNetworkFloatingIPsSelector(nodeid, pluginid)

	cb := func(kvs []yaks.Change) {
		if len(kvs) > 0 {
			v := kvs[0].Value().ToString()
			sv := FloatingIPRecord{}
			err := json.Unmarshal([]byte(v), &sv)
			if err != nil {
				panic(err.Error())
			}
			listener(sv)
		}
	}

	sid, err := lad.ws.Subscribe(s, cb)
	if err != nil {
		return err
	}
	lad.listeners = append(lad.listeners, sid)
	return nil
}

// Global and Local

// Global is Global Actual and Desired
type Global struct {
	ws      *yaks.Workspace
	actual  GAD
	desired GAD
}

// NewGlobal ...
func NewGlobal(wspace *yaks.Workspace) Global {
	ac := GAD{evals: []*yaks.Path{}, listeners: []*yaks.SubscriptionID{}, prefix: GlobalActualPrefix, ws: wspace}
	ds := GAD{evals: []*yaks.Path{}, listeners: []*yaks.SubscriptionID{}, prefix: GlobalDesiredPrefix, ws: wspace}
	return Global{ws: wspace, actual: ac, desired: ds}

}

// Local is Global Actual and Desired
type Local struct {
	ws      *yaks.Workspace
	actual  LAD
	desired LAD
}

// NewLocal ...
func NewLocal(wspace *yaks.Workspace) Local {
	ac := LAD{evals: []*yaks.Path{}, listeners: []*yaks.SubscriptionID{}, prefix: LocalActualPrefix, ws: wspace}
	ds := LAD{evals: []*yaks.Path{}, listeners: []*yaks.SubscriptionID{}, prefix: LocalDesiredPrefix, ws: wspace}
	return Local{ws: wspace, actual: ac, desired: ds}
}

// YaksConnector is Yaks Connector
type YaksConnector struct {
	yclient *yaks.Yaks
	yadmin  *yaks.Admin
	ws      *yaks.Workspace
	global  Global
	local   Local
}

func (yc *YaksConnector) close() error {
	return yc.yclient.Logout()
}

// NewYaksConnector ...
func NewYaksConnector(locator string) (*YaksConnector, error) {

	y, err := yaks.Login(locator, yaks.Properties{})
	if err != nil {
		return nil, err
	}

	ad := y.Admin()

	wpath, err := yaks.NewPath("/**")
	if err != nil {
		return nil, err
	}

	ws := y.Workspace(wpath)

	g := NewGlobal(ws)
	l := NewLocal(ws)

	return &YaksConnector{ws: ws, global: g, local: l, yadmin: ad, yclient: y}, nil
}
