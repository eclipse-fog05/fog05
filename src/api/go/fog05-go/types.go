/*
* Copyright (c) 2014,2019 Contributors to the Eclipse Foundation
* See the NOTICE file(s) distributed with this work for additional
* information regarding copyright ownership.
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
* which is available at https://www.apache.org/licenses/LICENSE-2.0.
* SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
* Contributors: Gabriele Baldoni, ADLINK Technology Inc.
* golang APIs
 */

package fog05

// DefaultSysID constant for Default System ID
const DefaultSysID = "0"

// DefaultTenantID constant for Default Tenant ID
const DefaultTenantID = "0"

// FError fog05 Error
type FError struct {
	msg   string
	cause error
}

func (e *FError) Error() string {
	if e.cause != nil {
		return e.msg + " - caused by:" + e.cause.Error()
	}
	return e.msg
}

// SystemInfo rapresent system information
type SystemInfo struct {
	Name string `json:"name"`
	UUID string `json:"uuid"`
}

// SystemConfig represents system configuration
type SystemConfig struct {
	Config string `json:"config"`
}

// TenantInfo represents tenant information
type TenantInfo struct {
	Name string `json:"name"`
	UUID string `json:"uuid"`
}

// CPUSpec represents CPU specification
type CPUSpec struct {
	Model     string  `json:"model"`
	Frequency float64 `json:"frequency"`
	Arch      string  `json:"arch"`
}

// RAMSpec represents RAM specification
type RAMSpec struct {
	Size float64 `json:"size"`
}

// DiskSpec rapresent Disk specification
type DiskSpec struct {
	LocalAddress string  `json:"local_address"`
	Dimension    float64 `json:"dimension"`
	MountPoint   string  `json:"mount_point"`
	FileSystem   string  `json:"filesystem"`
}

// IOSpec represents I/O specification
type IOSpec struct {
	Name      string `json:"name"`
	IOType    string `json:"io_type"`
	IOFile    string `json:"io_file"`
	Available bool   `json:"available"`
}

// VolatilitySpec represents Volatility specification
type VolatilitySpec struct {
	AverageAvailabilityMinutes   int   `json:"avg_availability_minutes"`
	QuartilesAvailabilityMinutes []int `json:"quartiles_availability_minutes"`
}

// AcceleratorSpec rapresent HW Accelerators specification
type AcceleratorSpec struct {
	HWAddress        string   `json:"hw_address"`
	Name             string   `json:"name"`
	SupportedLibrary []string `json:"supported_library"`
	Available        bool     `json:"available"`
}

// InterfaceConfiguration rapresent network interface specification
type InterfaceConfiguration struct {
	IPV4Address string  `json:"ipv4_address"`
	IPV4Netmask string  `json:"ipv4_netmask"`
	IPV4Gateway string  `json:"ipv4_gateway"`
	IPV6Address string  `json:"ipv6_address"`
	IPV6Netmask string  `json:"ipv6_netmask"`
	IPV6Gateway *string `json:"ipv6_gateway,omitempty"`
	BUSAddress  *string `json:"bus_address,omitempty"`
}

// PositionSpec represents Position specification
type PositionSpec struct {
	Latitude  float64 `json:"lat"`
	Longitude float64 `json:"lon"`
}

// NetworkSpec represents network specification
type NetworkSpec struct {
	InterfaceName       string                 `json:"intf_name"`
	InterfaceMACAddress string                 `json:"intf_mac_address"`
	InterfaceSpeed      int                    `json:"intf_speed"`
	InterfaceType       string                 `json:"type"`
	Available           bool                   `json:"available"`
	DefaultGW           bool                   `json:"default_gw"`
	InterfaceConf       InterfaceConfiguration `json:"intf_configuration"`
}

// NodeInfo represents node information
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
	Position    *PositionSpec     `json:"position,omitempty"`
	Volatility  *VolatilitySpec   `json:"volatility,omitempty"`
}

// AgentConfiguration represents agent configuration
type AgentConfiguration struct {
	System        string  `json:"system,omitempty"`
	UUID          *string `json:"uuid,omitempty"`
	Expose        bool    `json:"expose"`
	User          *string `json:"user,omitempty"`
	Password      *string `json:"passwd,omitempty"`
	YAKS          string  `json:"yaks"`
	Path          string  `json:"path"`
	EnableLLDP    bool    `json:"enable_lldp"`
	EnableSpawner bool    `json:"enable_spawner"`
	PIDFile       string  `json:"pid_file"`
	MGMTInterface string  `json:"mgmt_interface"`
	LLDPConf      string  `json:"lldp_conf"`
}

// PluginsConfiguration represents Ageng plugin configuration
type PluginsConfiguration struct {
	PluginPath string   `json:"plugin_path"`
	Autoload   bool     `json:"autoload"`
	Auto       []string `json:"auto,omitempty"`
}

// NodeConfiguration represents node configuration
type NodeConfiguration struct {
	Agent   AgentConfiguration   `json:"agent"`
	Plugins PluginsConfiguration `json:"plugins"`
}

// RAMStatus represents RAM status
type RAMStatus struct {
	Total float64 `json:"total"`
	Free  float64 `json:"free"`
}

// DiskStatus represents disk status
type DiskStatus struct {
	MountPoint string  `json:"mount_point"`
	Total      float64 `json:"total"`
	Free       float64 `json:"free"`
}

// NeighborPeerInfo represents node neighbor peer
type NeighborPeerInfo struct {
	Name string `json:"name"`
	ID   string `json:"id"`
}

// NeighborInfo represents node neighbor
type NeighborInfo struct {
	Node NeighborPeerInfo `json:"node"`
	Port NeighborPeerInfo `json:"port"`
}

// Neighbor represents node neighbor
type Neighbor struct {
	Src NeighborInfo `json:"src"`
	Dst NeighborInfo `json:"dst"`
}

// NodeStatus represents node status
type NodeStatus struct {
	UUID      string       `json:"uuid"`
	RAM       RAMStatus    `json:"ram"`
	Disk      []DiskStatus `json:"disk"`
	Neighbors []Neighbor   `json:"neighbors"`
}

// Plugin represents plugin configuration
type Plugin struct {
	UUID          string   `json:"uuid"`
	Name          string   `json:"name"`
	Version       int      `json:"version"`
	Type          string   `json:"type"`
	Status        *string  `json:"status,omitempty"`
	Requirements  []string `json:"requirements,omitempty"`
	Description   *string  `json:"description,omitempty"`
	URL           *string  `json:"url,omitempty"`
	Configuration *jsont   `json:"configuration,omitempty"`
}

// EvalResult represents results of Eval
type EvalResult struct {
	Result       *interface{} `json:"result,omitempty"`
	Error        *int         `json:"error,omitempty"`
	ErrorMessage *string      `json:"error_msg,omitempty"`
}
