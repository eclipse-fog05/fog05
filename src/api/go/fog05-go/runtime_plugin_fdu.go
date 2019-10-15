package fog05

import (
	"time"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
)

// FOSRuntimePluginFDU represents a Runtime Plugin for Eclipse fog05
type FOSRuntimePluginFDU struct {
	Pid           int
	Name          string
	Connector     *YaksConnector
	Node          string
	Configuration map[string]string
	Plugin        *FOSPlugin
	Logger        *log.Logger
}

// NewFOSRuntimePluginFDU returns a new FOSRuntimePluginFDU object
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

// Close closes the Plugin
func (rt *FOSRuntimePluginFDU) Close() {
	rt.Connector.Close()
}

// WaitDestinationReady waits for the destination node of a migration to be ready
func (rt *FOSRuntimePluginFDU) WaitDestinationReady(fduid string, instanceid string, destinationid string) bool {
	return false
}

// WaitDependencies waits that the Agent, OS and NM Plugins are up and gets those from YAKS
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

// WriteFDUError given an fdu id, instance id, error number and error message, stores the error in YAKS
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

// UpdateFDUStatus given an fdu id, instance id and status updates the status in YAKS
func (rt *FOSRuntimePluginFDU) UpdateFDUStatus(fduid string, instanceid string, status string) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.Plugin.UUID, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = status

	err = rt.Connector.Local.Actual.AddNodeFDU(rt.Node, rt.Plugin.UUID, fduid, instanceid, *record)
	return err
}

// GetLocalInstances given an fdu id returns all the instances of that fdu running locally, returns string slice
func (rt *FOSRuntimePluginFDU) GetLocalInstances(fduid string) ([]string, error) {
	return rt.Connector.Local.Actual.GetNodeFDUInstances(rt.Node, fduid)

}
