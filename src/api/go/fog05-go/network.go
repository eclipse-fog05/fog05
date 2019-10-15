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

type jsont = map[string]interface{}

//Couple represent a Couple object usefull in case of functions returning couples
type Couple struct {
	St string
	Nd string
}

// VPORT ...
const (
	VPORT string = "VPORT"

	ELINE string = "ELINE"
	ELAN  string = "ELAN"

	IPV6 string = "IPV6"
	IPV4 string = "IPV4"

	CREATE       string = "CREATE"
	CONNECTED    string = "CONNECTED"
	DISCONNECTED string = "DISCONNECTED"
	DESTROY      string = "DESTROY"
)

// AddressInformation represents Address configuration for a network
type AddressInformation struct {
	IPVersion  string  `json:"ip_version"`
	Subnet     string  `json:"subnet"`
	Gateway    *string `json:"gateway,omitempty"`
	DHCPEnable bool    `json:"dhcp_enable"`
	DHCPRange  *string `json:"dhcp_range,omitempty"`
	DNS        *string `json:"dns,omitempty"`
}

// ConnectionPointDescriptor represents a Connection Point
type ConnectionPointDescriptor struct {
	UUID                *string `json:"uuid,omitempty"`
	Name                string  `json:"name"`
	ID                  string  `json:"id"`
	VLDRef              *string `json:"vld_ref,omitempty"`
	ShortName           *string `json:"short_name,omitempty"`
	CPType              *string `json:"cp_type,omitempty"`
	PortSecurityEnabled *bool   `json:"port_security_enabled,omitempty"`
	Status              *string `json:"status,omitempty"`
}

// ConnectionPointRecord represent a Connection Point record
type ConnectionPointRecord struct {
	UUID                string  `json:"uuid"`
	CPID                string  `json:"cp_id"`
	CPType              *string `json:"cp_type,omitempty"`
	VLDRef              *string `json:"vld_ref,omitempty"`
	PortSecurityEnabled *bool   `json:"port_security_enabled,omitempty"`
	VEthFaceName        *string `json:"veth_face_name,omitempty"`
	BrName              *string `json:"br_name,omitempty"`
	Properties          *jsont  `json:"properties,omitempty"`
	Status              string  `json:"status"`
}

// RouterPort represent a router port
type RouterPort struct {
	PortType     string  `json:"port_type"`
	VirtualNetID *string `json:"vnet_id,omitempty"`
	IPAddress    *string `json:"ip_address,omitempty"`
}

// RouterDescriptor represent a Virtual Router
type RouterDescriptor struct {
	UUID  *string      `json:"uuid,omitempty"`
	Ports []RouterPort `json:"ports"`
}

// RouterPortRecord represent a router port record
type RouterPortRecord struct {
	PortType     *string  `json:"port_type,omitempty"`
	Faces        []string `json:"faces"`
	ExternalFace *string  `json:"ext_face,omitempty"`
	IPAddress    string   `json:"ip_address"`
	PairID       *string  `json:"vnet_id,omitempty"`
}

// RouterRecord represent a virtual router record
type RouterRecord struct {
	UUID     string             `json:"uuid"`
	State    string             `json:"state"`
	Ports    []RouterPortRecord `json:"ports"`
	RouterNS string             `json:"router_ns"`
	NodeID   string             `json:"nodeid"`
}

// VirtualNetwork represent a virtual network
type VirtualNetwork struct {
	UUID             string              `json:"uuid"`
	Name             string              `json:"name"`
	NetworkType      string              `json:"net_type"`
	IsMGMT           bool                `json:"is_mgmt"`
	IPConfiguration  *AddressInformation `json:"ip_configuration,omitempty"`
	Overlay          *bool               `json:"overlay,omitempty"`
	MulticastAddress *string             `json:"mcat_addr,omitempty"`
	VLANID           *int                `json:"vlan_id,omitempty"`
	Face             *string             `json:"face,omitempty"`
	Status           *string             `json:"status,omitempty"`
}

// FloatingIPDescriptor represent a floating IP
type FloatingIPDescriptor struct {
	UUID      string `json:"uuid"`
	IPVersion string `json:"ip_version"`
	Address   string `json:"address"`
}

// FloatingIPRecord represent a floating IP record
type FloatingIPRecord struct {
	UUID        string `json:"uuid"`
	IPVersion   string `json:"ip_version"`
	Address     string `json:"address"`
	Face        string `json:"face"`
	VirtualFace string `json:"vface"`
	CPID        string `json:"cp_id"`
}
