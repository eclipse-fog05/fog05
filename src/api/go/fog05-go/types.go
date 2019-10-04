package fog05

/*

type MyStruct struct {
    Name  string `json:"name,omitempty"`
    Age   int    `json:"age"`
    Email string `json:"email,omitempty"`
}

*/

// SystemInfo ...
type SystemInfo struct {
	Name string `json:"name"`
	UUID string `json:"uuid"`
}

// SystemConfig ...
type SystemConfig struct {
	Config string `json:"config"`
}

// TenantInfo ...
type TenantInfo struct {
	Name string `json:"name"`
	UUID string `json:"uuid"`
}

// CPUSpec ...
type CPUSpec struct {
	Model     string  `json:"model"`
	Frequency float64 `json:"frequency"`
	Arch      string  `json:"arch"`
}

// RAMSpec ...
type RAMSpec struct {
	Size float64 `json:"size"`
}

// DiskSpec ...
type DiskSpec struct {
	LocalAddress string  `json:"local_address"`
	Dimension    float64 `json:"dimension"`
	MountPoint   string  `json:"mount_point"`
	FileSystem   string  `json:"filesystem"`
}

// IOSpec ...
type IOSpec struct {
	Name      string `json:"name"`
	IOType    string `json:"io_type"`
	IOFile    string `json:"io_file"`
	Available bool   `json:"available"`
}

// VolatilitySpec ...
type VolatilitySpec struct {
	AverageAvailabilityMinutes   int   `json:"avg_availability_minutes"`
	QuartilesAvailabilityMinutes []int `json:"quartiles_availability_minutes"`
}

// AcceleratorSpec ...
type AcceleratorSpec struct {
	HWAddress        string   `json:"hw_address"`
	Name             string   `json:"name"`
	SupportedLibrary []string `json:"supported_library"`
	Available        bool     `json:"available"`
}

// InterfaceConfiguration ...
type InterfaceConfiguration struct {
	IPV4Address string `json:"ipv4_address"`
	IPV4Netmask string `json:"ipv4_netmask"`
	IPV4Gateway string `json:"ipv4_gateway"`
	IPV6Address string `json:"ipv6_address"`
	IPV6Netmask string `json:"ipv6_netmask"`
	IPV6Gateway string `json:"ipv6_gateway,omitempty"`
	BUSAddress  string `json:"bus_address,omitempty"`
}

// PositionSpec ...
type PositionSpec struct {
	Latitude  float64 `json:"lat"`
	Longitude float64 `json:"lon"`
}

// NetworkSpec ...
type NetworkSpec struct {
	InterfaceName       string                 `json:"intf_name"`
	InterfaceMACAddress string                 `json:"intf_mac_address"`
	InterfaceSpeed      int                    `json:"intf_speed"`
	InterfaceType       string                 `json:"type"`
	Available           bool                   `json:"available"`
	DefaultGW           bool                   `json:"default_gw"`
	InterfaceConf       InterfaceConfiguration `json:"intf_configuration"`
}

// NodeInfo ...
type NodeInfo struct {
	UUID        string            `json:"uuid"`
	Name        string            `json:"name"`
	OS          string            `json:"os"`
	CPU         []CPUSpec         `json:"cpu"`
	RAM         RAMSpec           `json:"ram"`
	Disks       []DiskSpec        `json:"disks"`
	IO          []IOSpec          `json:"io"`
	Accelerator []AcceleratorSpec `json:"accelerator"`
	Network     []NetworkSpec     `json:"network"`
	Position    PositionSpec      `json:"position,omitempty"`
	Volatility  VolatilitySpec    `json:"volatility,omitempty"`
}

// AgentConfiguration ...
type AgentConfiguration struct {
	System        string `json:"system,omitempty"`
	UUID          string `json:"uuid,omitempty"`
	Expose        bool   `json:"expose"`
	User          string `json:"user,omitempty"`
	Password      string `json:"passwd,omitempty"`
	YAKS          string `json:"yaks"`
	Path          string `json:"path"`
	EnableLLDP    bool   `json:"enable_lldp"`
	EnableSpawner bool   `json:"enable_spawner"`
	PIDFile       string `json:"pid_file"`
	MGMTInterface string `json:"mgmt_interface"`
	LLDPConf      string `json:"lldp_conf"`
}

// PluginsConfiguration ...
type PluginsConfiguration struct {
	PluginPath string   `json:"plugin_path"`
	Autoload   bool     `json:"autoload"`
	Auto       []string `json:"auto,omitempty"`
}

// NodeConfiguration ...
type NodeConfiguration struct {
	Agent   AgentConfiguration   `json:"agent"`
	Plugins PluginsConfiguration `json:"plugins"`
}

// RAMStatus ...
type RAMStatus struct {
	Total float64 `json:"total"`
	Free  float64 `json:"free"`
}

// DiskStatus ...
type DiskStatus struct {
	MountPoint string  `json:"mount_point"`
	Total      float64 `json:"total"`
	Free       float64 `json:"free"`
}

// NeighborPeerInfo ...
type NeighborPeerInfo struct {
	Name string `json:"name"`
	ID   string `json:"id"`
}

// NeighborInfo ...
type NeighborInfo struct {
	Node NeighborPeerInfo `json:"node"`
	Port NeighborPeerInfo `json:"port"`
}

// Neighbor ...
type Neighbor struct {
	Src NeighborInfo `json:"src"`
	Dst NeighborInfo `json:"dst"`
}

// NodeStatus ...
type NodeStatus struct {
	UUID      string       `json:"uuid"`
	RAM       RAMStatus    `json:"ram"`
	Disk      []DiskStatus `json:"disk"`
	Neighbors []Neighbor   `json:"neighbors"`
}

// Plugin ...
type Plugin struct {
	UUID          string   `json:"uuid"`
	Name          string   `json:"name"`
	Version       int      `json:"version"`
	Type          string   `json:"type"`
	Status        string   `json:"status,omitempty"`
	Requirements  []string `json:"requirements,omitempty"`
	Description   string   `json:"description,omitempty"`
	URL           string   `json:"url,omitempty"`
	Configuration string   `json:"configuration,omitempty"`
}

// EvalResult ...
type EvalResult struct {
	Result       jsont  `json:"result,omitempty"`
	Error        int    `json:"error,omitempty"`
	ErrorMessage string `json:"error_msg,omitempty"`
}
