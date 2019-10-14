package fog05

import (
	"time"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
)

// FOSRuntimePluginFDU ...
type FOSRuntimePluginFDU struct {
	Pid           int
	Name          string
	Connector     *YaksConnector
	Node          string
	Configuration map[string]string
	Plugin        *FOSPlugin
	Logger        *log.Logger
}

// NewFOSRuntimePluginFDU ...
func NewFOSRuntimePluginFDU(name string, version int, pluginid string, manifest Plugin) (*FOSRuntimePluginFDU, error) {
	if pluginid == "" {
		pluginid = uuid.UUID.String(uuid.New())
	}
	pl := NewPlugin(version, pluginid)

	conf := *manifest.Configuration
	// json.Unmarshal([]byte(manifest.Configuration), &conf)
	con, err := NewYaksConnector(conf["ylocator"].(string))
	if err != nil {
		return nil, err
	}
	pl.connector = con
	pl.node = conf["nodeid"].(string)

	return &FOSRuntimePluginFDU{Pid: -1, Name: name, Connector: con, Node: conf["nodeid"].(string), Plugin: pl, Logger: log.New()}, nil
}

// Close ...
func (rt *FOSRuntimePluginFDU) Close() {
	rt.Connector.Close()
}

// WaitDestinationReady ...
func (rt *FOSRuntimePluginFDU) WaitDestinationReady(fduid string, instanceid string, destinationid string) bool {
	return false
}

// WaitDependencies ...
func (rt *FOSRuntimePluginFDU) WaitDependencies() {
	rt.Plugin.GetAgent()
	for rt.Plugin.OS == nil {
		rt.Plugin.GetOSPlugin()
		time.Sleep(1 * time.Second)
	}
	for rt.Plugin.NM == nil {
		rt.Plugin.GetNMPlugin()
		time.Sleep(1 * time.Second)
	}

}

// WriteFDUError ...
func (rt *FOSRuntimePluginFDU) WriteFDUError(fduid string, instanceid string, errno int, errmsg string) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.Plugin.UUID, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = ERROR
	record.ErrorCode = &errno
	record.ErrorMsg = &errmsg

	err = rt.Connector.Local.Actual.AddNodeFDU(rt.Node, rt.Plugin.UUID, fduid, instanceid, *record)
	return err
}

// UpdateFDUStatus ...
func (rt *FOSRuntimePluginFDU) UpdateFDUStatus(fduid string, instanceid string, status string) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.Plugin.UUID, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = status

	err = rt.Connector.Local.Actual.AddNodeFDU(rt.Node, rt.Plugin.UUID, fduid, instanceid, *record)
	return err
}

// GetLocalInstances ...
func (rt *FOSRuntimePluginFDU) GetLocalInstances(fduid string) ([]string, error) {
	return rt.Connector.Local.Actual.GetNodeFDUInstances(rt.Node, fduid)

}
