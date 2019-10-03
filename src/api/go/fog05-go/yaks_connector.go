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

// GetNodeNetworkNetworksSelector ...
func (gad *GAD) GetNodeNetworkNetworksSelector(sysid string, tenantid string, nodeid string) *yaks.Selector {
	return CreateSelector([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "networks", "*", "info"})
}

// Evals

// Dict2Args ...
func (gad *GAD) Dict2Args(d map[string]interface{}) string {

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

// GetAgentExecPath ...
func (gad *GAD) GetAgentExecPath(sysid string, tenantid string, nodeid string, funcname string) *yaks.Path {
	return CreatePath([]string{gad.prefix, sysid, "tenants", tenantid, "nodes", nodeid, "agent", "exec", funcname})
}

// GetAgentExecSelectorWithParams ...
func (gad *GAD) GetAgentExecSelectorWithParams(sysid string, tenantid string, nodeid string, funcname string, params map[string]interface{}) *yaks.Selector {
	var f string
	if len(params) > 0 {
		p := gad.Dict2Args(params)
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

// ExtractNodeFDUIDFromPath ...
func (gad *GAD) ExtractNodeFDUIDFromPath(path *yaks.Path) string {
	return strings.Split(path.ToString(), URISeparator)[8]
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

// System

// GetSysInfo ...
func (gad *GAD) GetSysInfo(sysid string) (*SystemInfo, error) {
	s, _ := yaks.NewSelector(gad.GetSysInfoPath(sysid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, nil
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
		return nil, nil
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
		return nil, nil
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
		return nil, nil
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
		return nil, nil
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

// GetNodeStatus ...
func (gad *GAD) GetNodeStatus(sysid string, tenantid string, nodeid string) (*NodeStatus, error) {
	s, _ := yaks.NewSelector(gad.GetNodeStatusPath(sysid, tenantid, nodeid).ToString())
	kvs := gad.ws.Get(s)
	if len(kvs) == 0 {
		return nil, nil
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
