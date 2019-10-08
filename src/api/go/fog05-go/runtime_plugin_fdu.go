package fog05

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
)

// FOSRuntimePluginFDU ...
type FOSRuntimePluginFDU struct {
	pid           int
	name          string
	connector     *YaksConnector
	node          string
	configuration map[string]string
	plugin        *FOSPlugin
	logger        *log.Logger
}

// NewFOSRuntimePluginFDU ...
func NewFOSRuntimePluginFDU(name string, version string, pluginid string, manifest Plugin) (*FOSRuntimePluginFDU, error) {
	if pluginid == "" {
		pluginid = uuid.UUID.String(uuid.New())
	}
	pl := NewPlugin(version, pluginid)

	conf := map[string]string{}
	json.Unmarshal([]byte(manifest.Configuration), &conf)

	con, err := NewYaksConnector(conf["ylocator"])
	if err != nil {
		return nil, err
	}
	pl.connector = con
	pl.node = conf["nodeid"]

	return &FOSRuntimePluginFDU{pid: -1, name: name, connector: con, node: conf["nodeid"], plugin: pl, logger: log.New()}, nil
}

// WaitDestinationReady ...
func (rt *FOSRuntimePluginFDU) WaitDestinationReady(fduid string, instanceid string, destinationid string) bool {
	return false
}

// WaitDependencies ...
func (rt *FOSRuntimePluginFDU) WaitDependencies() {
	rt.plugin.GetAgent()
	for rt.plugin.os == nil {
		rt.plugin.GetOSPlugin()
		time.Sleep(1 * time.Second)
	}
	for rt.plugin.nm == nil {
		rt.plugin.GetNMPlugin()
		time.Sleep(1 * time.Second)
	}

}

// WriteFDUError ...
func (rt *FOSRuntimePluginFDU) WriteFDUError(fduid string, instanceid string, errno int, errmsg string) error {
	record, err := rt.connector.local.actual.GetNodeFDU(rt.node, rt.plugin.uuid, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = ERROR
	record.ErrorCode = errno
	record.ErrorMsg = errmsg

	err = rt.connector.local.actual.AddNodeFDU(rt.node, rt.plugin.uuid, fduid, instanceid, *record)
	return err
}

// UpdateFDUStatus ...
func (rt *FOSRuntimePluginFDU) UpdateFDUStatus(fduid string, instanceid string, status string) error {
	record, err := rt.connector.local.actual.GetNodeFDU(rt.node, rt.plugin.uuid, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = status

	err = rt.connector.local.actual.AddNodeFDU(rt.node, rt.plugin.uuid, fduid, instanceid, *record)
	return err
}

// GetLocalInstances ...
func (rt *FOSRuntimePluginFDU) GetLocalInstances(fduid string) ([]string, error) {
	return rt.connector.local.actual.GetNodeFDUInstances(rt.node, fduid)

}
