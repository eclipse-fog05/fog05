package fog05

type jsont = map[string]interface{}

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

// AddressInformation ...
type AddressInformation struct {
	IPVersion  string `json:"ip_kind"`
	Subnet     string `json:"subnet"`
	Gateway    string `json:"gateway,omitempty"`
	DHCPEnable bool   `json:"dhcp_enable"`
	DHCPRange  string `json:"dhcp_range,omitempty"`
	DNS        string `json:"dns,omitempty"`
}

// ConnectionPointDescriptor ...
type ConnectionPointDescriptor struct {
	UUID                string `json:"uuid,omitempty"`
	Name                string `json:"name"`
	ID                  string `json:"id"`
	VLDRef              string `json:"vld_ref,omitempty"`
	ShortName           string `json:"short_name,omitempty"`
	CPType              string `json:"cp_type,omitempty"`
	PortSecurityEnabled bool   `json:"port_security_enabled,omitempty"`
}

// ConnectionPointRecord ...
type ConnectionPointRecord struct {
	UUID                string `json:"uuid"`
	CPID                string `json:"cp_id"`
	CPType              string `json:"cp_type,omitempty"`
	VLDRef              string `json:"vld_ref,omitempty"`
	PortSecurityEnabled bool   `json:"port_security_enabled,omitempty"`
	VEthFaceName        string `json:"veth_face_name,omitempty"`
	BrName              string `json:"br_name,omitempty"`
	Properties          jsont  `json:"properties,omitempty"`
	Status              string `json:"status"`
}
