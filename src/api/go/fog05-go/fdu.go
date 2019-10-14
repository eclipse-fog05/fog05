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

const (
	LIVE string = "LIVE"
	COLD string = "COLD"

	BARE   string = "BARE"
	KVM    string = "KVM"
	KVMUK  string = "KVM_UK"
	XEN    string = "XEN"
	XENUK  string = "XEN_UK"
	LXD    string = "LXD"
	DOCKER string = "DOCKER"
	MCU    string = "MCU"

	SCRIPT    string = "SCRIPT"
	CLOUDINIT string = "CLOUD_INIT"

	INTERNAL  string = "INTERNAL"
	EXTERNAL  string = "EXTERNAL"
	WLAN      string = "WLAN"
	BLUETOOTH string = "BLUETOOTH"

	PARAVIRT       string = "PARAVIRT"
	FOSMGMT        string = "FOS_MGMT"
	PCIPASSTHROUGH string = "PCI_PASSTHROUGH"
	SRIOV          string = "SR_IOV"
	E1000          string = "E1000"
	RTL8139        string = "RTL8139"
	PHYSICAL       string = "PHYSICAL"
	BRIDGED        string = "BRIDGED"

	GPIO string = "GPIO"
	I2C  string = "I2C"
	BUS  string = "BUS"
	COM  string = "COM"
	CAN  string = "CAN"

	BLOCK  string = "BLOCK"
	FILE   string = "FILE"
	OBJECT string = "OBJECT"

	DEFINE    string = "DEFINE"
	CONFIGURE string = "CONFIGURE"
	CLEAN     string = "CLEAN"
	RUN       string = "RUN"
	STARTING  string = "STARTING"
	STOP      string = "STOP"
	RESUME    string = "RESUME"
	PAUSE     string = "PAUSE"
	SCALE     string = "SCALE"
	TAKEOFF   string = "TAKE_OFF"
	LAND      string = "LAND"
	MIGRATE   string = "MIGRATE"
	UNDEFINE  string = "UNDEFINE"
	ERROR     string = "ERROR"
)

// FDUImage ...
type FDUImage struct {
	UUID     *string `json:"uuid,omitempty"`
	Name     *string `json:"name,omitempty"`
	URI      string  `json:"uri"`
	Checksum string  `json:"checksum"` //SHA1SUM
	Format   string  `json:"format"`
}

// FDUCommand ...
type FDUCommand struct {
	Binary string   `json:"binary"`
	Args   []string `json:"args"`
}

// FDUGeographicalRequirements ...
type FDUGeographicalRequirements struct {
	Position  *FDUPosition  `json:"position,omitempty"`
	Proximity *FDUProximity `json:"proximity,omitempty"`
}

// FDUPosition ...
type FDUPosition struct {
	Latitude  string  `json:"lat"`
	Longitude string  `json:"lon"`
	Radius    float64 `json:"radius"`
}

// FDUProximity ...
type FDUProximity struct {
	Neighbor string  `json:"neighbour"`
	Radius   float64 `json:"radius"`
}

// FDUEnergyRequirements ...
type FDUEnergyRequirements struct {
	Key string `json:"key"`
}

// FDUComputationalRequirements ...
type FDUComputationalRequirements struct {
	Name            *string  `json:"name,omitempty"`
	UUID            *string  `json:"uuid,omitempty"`
	CPUArch         string   `json:"cpu_arch"`
	CPUMinFrequency int      `json:"cpu_min_freq"`
	CPUMinCount     int      `json:"cpu_min_count"`
	GPUMinCount     *int     `json:"gpu_min_count,omitempty"`
	FPGAMinCount    *int     `json:"fpga_min_count,omitempty"`
	RAMSizeMB       float64  `json:"ram_size_mb"`
	StorageSizeGB   float64  `json:"storage_size_gb"`
	DutyCycle       *float64 `json:"duty_cycle,omitempty"`
}

// FDUConfiguration ...
type FDUConfiguration struct {
	ConfType string   `json:"conf_type"`
	Script   string   `json:"script"`
	SSHKeys  []string `json:"ssh_keys,omitempty"`
}

// FDUVirtualInterface ...
type FDUVirtualInterface struct {
	InterfaceType string `json:"intf_type"`
	VPCI          string `json:"vpci"`
	Bandwidth     int    `json:"bandwidth"`
}

// FDUIOPort ...
type FDUIOPort struct {
	Address    string `json:"address"`
	IOKind     string `json:"io_kind"`
	MinIOPorts int    `json:"min_io_ports"`
}

// FDUInterfaceDescriptor ...
type FDUInterfaceDescriptor struct {
	Name             string              `json:"name"`
	IsMGMT           bool                `json:"is_mgmt"`
	InterfaceType    string              `json:"if_type"`
	MACAddress       *string             `json:"mac_address,omitempty"`
	VirtualInterface FDUVirtualInterface `json:"virtual_interface"`
	CPID             *string             `json:"cp_id,omitempty"`
	ExtCPID          *string             `json:"ext_cp_id,omitempty"`
}

// FDUStorageDescriptor ...
type FDUStorageDescriptor struct {
	ID                 string  `json:"id"`
	StorageType        string  `json:"storage_type"`
	Size               int     `json:"size"`
	FileSystemProtocol *string `json:"file_system_protocol,omitempty"`
	CPID               *string `json:"cp_id,omitempty"`
}

// FDU ...
type FDU struct {
	ID                       string                       `json:"id"`
	Name                     string                       `json:"name"`
	UUID                     *string                      `json:"uuid,omitempty"`
	Description              *string                      `json:"description,omitempty"`
	ComputationRequirements  FDUComputationalRequirements `json:"computation_requirements"`
	Image                    *FDUImage                    `json:"image,omitempty"`
	Command                  *FDUCommand                  `json:"command,omitempty"`
	Storage                  []FDUStorageDescriptor       `json:"storage"`
	GeographicalRequirements *FDUGeographicalRequirements `json:"geographical_requirements,omitempty"`
	EnergyRequirements       *FDUEnergyRequirements       `json:"energy_requirements,omitempty"`
	Hypervisor               string                       `json:"hypervisor"`
	MigrationKind            string                       `json:"migration_kind"`
	Configuration            *FDUConfiguration            `json:"configuration,omitempty"`
	Interfaces               []FDUInterfaceDescriptor     `json:"interfaces"`
	IOPorts                  []FDUIOPort                  `json:"io_ports"`
	ConnectionPoints         []ConnectionPointDescriptor  `json:"connection_points"`
	DependsOn                []string                     `json:"depends_on"`
}

// FDUStorageRecord ...
type FDUStorageRecord struct {
	UUID               string  `json:"uuid"`
	StorageID          string  `json:"storage_id"`
	StorageType        string  `json:"storage_type"`
	Size               int     `json:"size"`
	FileSystemProtocol *string `json:"file_system_protocol,omitempty"`
	CPID               *string `json:"cp_id,omitempty"`
}

// FDUInterfaceRecord ...
type FDUInterfaceRecord struct {
	Name                 string               `json:"name"`
	IsMGMT               bool                 `json:"is_mgmt"`
	InterfaceType        string               `json:"if_type"`
	MACAddress           *string              `json:"mac_address,omitempty"`
	VirtualInterface     *FDUVirtualInterface `json:"virtual_interface,omitempty"`
	CPID                 *string              `json:"cp_id,omitempty"`
	ExtCPID              *string              `json:"ext_cp_id,omitempty"`
	VirtualInterfaceName string               `json:"vintf_name"`
	Status               string               `json:"status"`
	PhysicalFace         *string              `json:"phy_face,omitempty"`
	VEthFaceName         *string              `json:"veth_face_name,omitempty"`
	Properties           *jsont               `json:"properties,omitempty"`
}

// FDUMigrationProperties ...
type FDUMigrationProperties struct {
	Destination string `json:"destination"`
	Source      string `json:"source"`
}

// FDURecord ...
type FDURecord struct {
	UUID                     string                       `json:"uuid"`
	FDUID                    string                       `json:"fdu_id"`
	Status                   string                       `json:"status"`
	Image                    *FDUImage                    `json:"image,omitempty"`
	Command                  *FDUCommand                  `json:"command,omitempty"`
	Storage                  []FDUStorageRecord           `json:"storage"`
	ComputationRequirements  FDUComputationalRequirements `json:"computation_requirements"`
	GeographicalRequirements *FDUGeographicalRequirements `json:"geographical_requirements,omitempty"`
	EnergyRequirements       *FDUEnergyRequirements       `json:"energy_requirements,omitempty"`
	Hypervisor               string                       `json:"hypervisor"`
	MigrationKind            string                       `json:"migration_kind"`
	Configuration            *FDUConfiguration            `json:"configuration,omitempty"`
	Interfaces               *[]FDUInterfaceRecord        `json:"interfaces,omitempty"`
	IOPorts                  []FDUIOPort                  `json:"io_ports"`
	ConnectionPoints         []ConnectionPointRecord      `json:"connection_points"`
	DependsOn                []string                     `json:"depends_on"`
	ErrorCode                *int                         `json:"error_code,omitempty"`
	ErrorMsg                 *string                      `json:"error_msg,omitempty"`
	MigrationProperties      *FDUMigrationProperties      `json:"migration_properties,omitempty"`
	HypervisorInfo           *jsont                       `json:"hypervisor_info,omitempty"`
}
