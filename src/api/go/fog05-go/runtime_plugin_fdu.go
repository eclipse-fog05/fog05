package fog05

import (
	"fmt"
	"time"

	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
)

// FOSRuntimePluginInterface is the interface to be implenter for a Runtime Plugin
type FOSRuntimePluginInterface interface {

	//StartRuntime starts the plugin
	StartRuntime() error

	//StopRuntime stops the plugin
	StopRuntime() error

	//GetFDUs gets all FDU and instances information
	GetFDUs() map[string]FDURecord

	//DefineFDU defines an FDU instance from the given record
	DefineFDU(FDURecord) error

	//UndefineFDU undefines the given FDU instance
	UndefineFDU(string) error

	//ConfigureFDU configures the given FDU instance
	ConfigureFDU(string) error

	//CleanFDU cleans the given FDU instance
	CleanFDU(string) error

	//RunFDU starts the given FDU instance
	RunFDU(string) error

	//StopFDU stops the given FDU instance
	StopFDU(string) error

	//MigrateFDU migrates the given FDU instance
	MigrateFDU(string) error

	//ScaleFDU scales the given FDU instance
	ScaleFDU(string) error

	//PauseFDU pauses the given FDU instance
	PauseFDU(string) error

	//ResumeFDU resumes the given FDU instance
	ResumeFDU(string) error
}

// FOSRuntimePluginAbstract represents a Runtime Plugin for Eclipse fog05
type FOSRuntimePluginAbstract struct {
	Pid           int
	Name          string
	Connector     *YaksConnector
	Node          string
	Configuration map[string]string
	// Plugin        *FOSPlugin
	Logger *log.Logger
	FOSRuntimePluginInterface
	FOSPlugin
}

// NewFOSRuntimePluginAbstract returns a new FOSRuntimePluginFDU object
func NewFOSRuntimePluginAbstract(name string, version int, pluginid string, manifest Plugin) (*FOSRuntimePluginAbstract, error) {
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

	return &FOSRuntimePluginAbstract{Pid: -1, Name: name, Connector: con, Node: conf["nodeid"].(string), FOSPlugin: *pl, Logger: log.New()}, nil
}

// Start starts the Plugin and calls StartRuntime of FOSRuntimePluginInterface
func (rt *FOSRuntimePluginAbstract) Start() {
	rt.WaitDependencies()
	rt.Connector.Local.Desired.ObserveNodeRuntimeFDU(rt.Node, rt.FOSPlugin.UUID, rt.react)
	err := rt.FOSRuntimePluginInterface.StartRuntime()
	if err != nil {
		rt.Logger.Error(fmt.Sprintf("Plugin StartRuntime returned error %s", err.Error()))
		rt.Close()
	}
}

// Close closes the Plugin, called by FOSRuntimePluginInterface.StopRuntime()
func (rt *FOSRuntimePluginAbstract) Close() {
	rt.RemovePlugin()
	rt.Connector.Close()
	rt.Logger.Info("Plugin closed")
}

// WaitDestinationReady waits for the destination node of a migration to be ready
func (rt *FOSRuntimePluginAbstract) WaitDestinationReady(fduid string, instanceid string, destinationid string) bool {
	return false
}

// WaitDependencies waits that the Agent, OS and NM Plugins are up and gets those from YAKS
func (rt *FOSRuntimePluginAbstract) WaitDependencies() {
	rt.FOSPlugin.GetAgent()
	for rt.FOSPlugin.OS == nil {
		rt.FOSPlugin.GetOSPlugin()
		time.Sleep(1 * time.Second)
	}
	for rt.FOSPlugin.NM == nil {
		rt.FOSPlugin.GetNMPlugin()
		time.Sleep(1 * time.Second)
	}

}

// WriteFDUError given an fdu id, instance id, error number and error message, stores the error in YAKS
func (rt *FOSRuntimePluginAbstract) WriteFDUError(fduid string, instanceid string, errno int, errmsg string) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.FOSPlugin.UUID, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = ERROR
	record.ErrorCode = &errno
	record.ErrorMsg = &errmsg

	err = rt.Connector.Local.Actual.AddNodeFDU(rt.Node, rt.FOSPlugin.UUID, fduid, instanceid, *record)
	return err
}

// UpdateFDUStatus given an fdu id, instance id and status updates the status in YAKS
func (rt *FOSRuntimePluginAbstract) UpdateFDUStatus(fduid string, instanceid string, status string) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.FOSPlugin.UUID, fduid, instanceid)
	if err != nil {
		return err
	}

	record.Status = status

	err = rt.Connector.Local.Actual.AddNodeFDU(rt.Node, rt.FOSPlugin.UUID, fduid, instanceid, *record)
	return err
}

// GetLocalInstances given an fdu id returns all the instances of that fdu running locally, returns string slice
func (rt *FOSRuntimePluginAbstract) GetLocalInstances(fduid string) ([]string, error) {
	return rt.Connector.Local.Actual.GetNodeFDUInstances(rt.Node, fduid)

}

// RegisterPlugin registers the plugin in the node
func (rt *FOSRuntimePluginAbstract) RegisterPlugin(manifest *Plugin) {
	rt.Connector.Local.Actual.AddNodePlugin(rt.Node, rt.FOSPlugin.UUID, *manifest)
}

// RemovePlugin removes the plugin in the node
func (rt *FOSRuntimePluginAbstract) RemovePlugin() {
	rt.Connector.Local.Actual.RemoveNodePlugin(rt.Node, rt.FOSPlugin.UUID)
}

// GetFDUDescriptor retrives an FDURecord for the plugin
func (rt *FOSRuntimePluginAbstract) GetFDUDescriptor(fduid string, instanceid string) (*FDU, error) {
	return rt.FOSPlugin.Agent.GetFDUInfo(rt.Node, fduid, instanceid)
}

// GetFDURecord retrives an FDURecord for the plugin
func (rt *FOSRuntimePluginAbstract) GetFDURecord(instanceid string) (*FDURecord, error) {
	return rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.FOSPlugin.UUID, "*", instanceid)
}

// AddFDURecord adds an FDU record to the node
func (rt *FOSRuntimePluginAbstract) AddFDURecord(instanceid string, info *FDURecord) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.FOSPlugin.UUID, "*", instanceid)
	if err != nil {
		return err
	}
	return rt.Connector.Local.Actual.AddNodeFDU(rt.Node, rt.FOSPlugin.UUID, record.FDUID, instanceid, *info)
}

// RemoveFDURecord removes an FDURecord from the node
func (rt *FOSRuntimePluginAbstract) RemoveFDURecord(instanceid string) error {
	record, err := rt.Connector.Local.Actual.GetNodeFDU(rt.Node, rt.FOSPlugin.UUID, "*", instanceid)
	if err != nil {
		return err
	}
	return rt.Connector.Local.Actual.RemoveNodeFDU(rt.Node, rt.FOSPlugin.UUID, record.FDUID, instanceid)
}

func (rt *FOSRuntimePluginAbstract) react(info FDURecord) {

	action := info.Status
	id := info.UUID
	switch action {
	case DEFINE:
		rt.DefineFDU(info)
	case UNDEFINE:
		rt.UndefineFDU(id)
	case CLEAN:
		rt.CleanFDU(id)
	case CONFIGURE:
		rt.ConfigureFDU(id)
	case RUN:
		rt.RunFDU(id)
	case STOP:
		rt.StopFDU(id)
	case PAUSE:
		rt.PauseFDU(id)
	case RESUME:
		rt.ResumeFDU(id)
	case LAND:
		rt.MigrateFDU(id)
	case TAKEOFF:
		rt.MigrateFDU(id)
	default:
		rt.Logger.Error(fmt.Sprintf("Action %s not recognized", action))
	}
}
