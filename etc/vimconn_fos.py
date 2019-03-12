# -*- coding: utf-8 -*-

##
# Copyright 2019 ADLINK Technology Inc..
# This file is part of 5GCity EU-H2020 Project
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
##

"""
vimconn implement an Abstract class for the vim connector plugins
 with the definition of the method to be implemented.


OSM VM:

./vm_manager.py define -b ubuntu16 --cpu 4 --ram 16384 --size 80 --name osmr4 --ssh-key ~/.ssh/id_rsa.pub --sriov 19:10:7
10.100.1.202


OSM RO docker

"CMD": ["/bin/sh", "-c", "#(nop) ", "CMD [\"/bin/sh\" \"-c\" \"/bin/RO/start.sh\"]"

'CMD": ["/bin/sh", "-c", "#(nop) ", "CMD [\"/bin/sh\" \"-c\" \"/bin/RO/start.sh\"]'


"""
__author__="Gabriele Baldoni"
__date__ ="$11-mar-2019 12:00:00$"

import logging
import random
import paramiko
import socket
import StringIO
import yaml
import sys
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fogfimapi import API

#Error variables
HTTP_Bad_Request = 400
HTTP_Unauthorized = 401
HTTP_Not_Found = 404
HTTP_Method_Not_Allowed = 405
HTTP_Request_Timeout = 408
HTTP_Conflict = 409
HTTP_Not_Implemented = 501
HTTP_Service_Unavailable = 503
HTTP_Internal_Server_Error = 500

class vimconnException(Exception):
    """Common and base class Exception for all vimconnector exceptions"""
    def __init__(self, message, http_code=HTTP_Bad_Request):
        Exception.__init__(self, message)
        self.http_code = http_code

class vimconnConnectionException(vimconnException):
    """Connectivity error with the VIM"""
    def __init__(self, message, http_code=HTTP_Service_Unavailable):
        vimconnException.__init__(self, message, http_code)

class vimconnUnexpectedResponse(vimconnException):
    """Get an wrong response from VIM"""
    def __init__(self, message, http_code=HTTP_Service_Unavailable):
        vimconnException.__init__(self, message, http_code)

class vimconnAuthException(vimconnException):
    """Invalid credentials or authorization to perform this action over the VIM"""
    def __init__(self, message, http_code=HTTP_Unauthorized):
        vimconnException.__init__(self, message, http_code)

class vimconnNotFoundException(vimconnException):
    """The item is not found at VIM"""
    def __init__(self, message, http_code=HTTP_Not_Found):
        vimconnException.__init__(self, message, http_code)

class vimconnConflictException(vimconnException):
    """There is a conflict, e.g. more item found than one"""
    def __init__(self, message, http_code=HTTP_Conflict):
        vimconnException.__init__(self, message, http_code)

class vimconnNotSupportedException(vimconnException):
    """The request is not supported by connector"""
    def __init__(self, message, http_code=HTTP_Service_Unavailable):
        vimconnException.__init__(self, message, http_code)

class vimconnNotImplemented(vimconnException):
    """The method is not implemented by the connected"""
    def __init__(self, message, http_code=HTTP_Not_Implemented):
        vimconnException.__init__(self, message, http_code)


class vimconnector():
    """Abstract base class for all the VIM connector plugins
    These plugins must implement a vimconnector class derived from this
    and all these privated methods
    """
    def __init__(self, uuid, name, tenant_id, tenant_name, url, url_admin=None, user=None, passwd=None, log_level=None,
                 config={}, persitent_info={}):
        """Constructor of VIM
        Params:
            'uuid': id asigned to this VIM
            'name': name assigned to this VIM, can be used for logging
            'tenant_id', 'tenant_name': (only one of them is mandatory) VIM tenant to be used
            'url_admin': (optional), url used for administrative tasks
            'user', 'passwd': credentials of the VIM user
            'log_level': provider if it should use a different log_level than the general one
            'config': dictionary with extra VIM information. This contains a consolidate version of general VIM config
                    at creation and particular VIM config at teh attachment
            'persistent_info': dict where the class can store information that will be available among class
                    destroy/creation cycles. This info is unique per VIM/credential. At first call it will contain an
                    empty dict. Useful to store login/tokens information for speed up communication

        Returns: Raise an exception is some needed parameter is missing, but it must not do any connectivity
            check against the VIM
        """
        self.id        = uuid
        self.name      = name
        self.url       = url
        self.url_admin = url_admin
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.user      = user
        self.passwd    = passwd
        self.config    = config
        self.availability_zone = None
        self.arch = config.get('arch', 'x86_64')
        self.hv = config.get('hypervisor', 'LXD')
        self.fdu_node_map = {}
        self.logger = logging.getLogger('openmano.vim')
        if log_level:
            self.logger.setLevel( getattr(logging, log_level) )
        if not self.url_admin:  #try to use normal url
            self.url_admin = self.url

        self.fos_api = API(locator=self.url)

    def __getitem__(self,index):
        if index=='tenant_id':
            return self.tenant_id
        if index=='tenant_name':
            return self.tenant_name
        elif index=='id':
            return self.id
        elif index=='name':
            return self.name
        elif index=='user':
            return self.user
        elif index=='passwd':
            return self.passwd
        elif index=='url':
            return self.url
        elif index=='url_admin':
            return self.url_admin
        elif index=="config":
            return self.config
        else:
            raise KeyError("Invalid key '%s'" %str(index))

    def __setitem__(self,index, value):
        if index=='tenant_id':
            self.tenant_id = value
        if index=='tenant_name':
            self.tenant_name = value
        elif index=='id':
            self.id = value
        elif index=='name':
            self.name = value
        elif index=='user':
            self.user = value
        elif index=='passwd':
            self.passwd = value
        elif index=='url':
            self.url = value
        elif index=='url_admin':
            self.url_admin = value
        else:
            raise KeyError("Invalid key '%s'" %str(index))

    @staticmethod
    def _create_mimemultipart(content_list):
        """Creates a MIMEmultipart text combining the content_list
        :param content_list: list of text scripts to be combined
        :return: str of the created MIMEmultipart. If the list is empty returns None, if the list contains only one
        element MIMEmultipart is not created and this content is returned
        """
        if not content_list:
            return None
        elif len(content_list) == 1:
            return content_list[0]
        combined_message = MIMEMultipart()
        for content in content_list:
            if content.startswith('#include'):
                format = 'text/x-include-url'
            elif content.startswith('#include-once'):
                format = 'text/x-include-once-url'
            elif content.startswith('#!'):
                format = 'text/x-shellscript'
            elif content.startswith('#cloud-config'):
                format = 'text/cloud-config'
            elif content.startswith('#cloud-config-archive'):
                format = 'text/cloud-config-archive'
            elif content.startswith('#upstart-job'):
                format = 'text/upstart-job'
            elif content.startswith('#part-handler'):
                format = 'text/part-handler'
            elif content.startswith('#cloud-boothook'):
                format = 'text/cloud-boothook'
            else:  # by default
                format = 'text/x-shellscript'
            sub_message = MIMEText(content, format, sys.getdefaultencoding())
            combined_message.attach(sub_message)
        return combined_message.as_string()

    def _create_user_data(self, cloud_config):
        """
        Creates a script user database on cloud_config info
        :param cloud_config: dictionary with
            'key-pairs': (optional) list of strings with the public key to be inserted to the default user
            'users': (optional) list of users to be inserted, each item is a dict with:
                'name': (mandatory) user name,
                'key-pairs': (optional) list of strings with the public key to be inserted to the user
            'user-data': (optional) can be a string with the text script to be passed directly to cloud-init,
                or a list of strings, each one contains a script to be passed, usually with a MIMEmultipart file
            'config-files': (optional). List of files to be transferred. Each item is a dict with:
                'dest': (mandatory) string with the destination absolute path
                'encoding': (optional, by default text). Can be one of:
                    'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                'content' (mandatory): string with the content of the file
                'permissions': (optional) string with file permissions, typically octal notation '0644'
                'owner': (optional) file owner, string with the format 'owner:group'
            'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk)
        :return: config_drive, userdata. The first is a boolean or None, the second a string or None
        """
        config_drive = None
        userdata = None
        userdata_list = []
        if isinstance(cloud_config, dict):
            if cloud_config.get("user-data"):
                if isinstance(cloud_config["user-data"], str):
                    userdata_list.append(cloud_config["user-data"])
                else:
                    for u in cloud_config["user-data"]:
                        userdata_list.append(u)
            if cloud_config.get("boot-data-drive") != None:
                config_drive = cloud_config["boot-data-drive"]
            if cloud_config.get("config-files") or cloud_config.get("users") or cloud_config.get("key-pairs"):
                userdata_dict = {}
                # default user
                if cloud_config.get("key-pairs"):
                    userdata_dict["ssh-authorized-keys"] = cloud_config["key-pairs"]
                    userdata_dict["users"] = [{"default": None, "ssh-authorized-keys": cloud_config["key-pairs"]}]
                if cloud_config.get("users"):
                    if "users" not in userdata_dict:
                        userdata_dict["users"] = ["default"]
                    for user in cloud_config["users"]:
                        user_info = {
                            "name": user["name"],
                            "sudo": "ALL = (ALL)NOPASSWD:ALL"
                        }
                        if "user-info" in user:
                            user_info["gecos"] = user["user-info"]
                        if user.get("key-pairs"):
                            user_info["ssh-authorized-keys"] = user["key-pairs"]
                        userdata_dict["users"].append(user_info)

                if cloud_config.get("config-files"):
                    userdata_dict["write_files"] = []
                    for file in cloud_config["config-files"]:
                        file_info = {
                            "path": file["dest"],
                            "content": file["content"]
                        }
                        if file.get("encoding"):
                            file_info["encoding"] = file["encoding"]
                        if file.get("permissions"):
                            file_info["permissions"] = file["permissions"]
                        if file.get("owner"):
                            file_info["owner"] = file["owner"]
                        userdata_dict["write_files"].append(file_info)
                userdata_list.append("#cloud-config\n" + yaml.safe_dump(userdata_dict, indent=4,
                                                                        default_flow_style=False))
            userdata = self._create_mimemultipart(userdata_list)
            self.logger.debug("userdata: %s", userdata)
        elif isinstance(cloud_config, str):
            userdata = cloud_config
        return config_drive, userdata

    def check_vim_connectivity(self):
        """Checks VIM can be reached and user credentials are ok.
        Returns None if success or raised vimconnConnectionException, vimconnAuthException, ...
        """
        return None
        #raise vimconnNotImplemented( "Should have implemented this" )

    def new_tenant(self,tenant_name,tenant_description):
        """Adds a new tenant to VIM with this name and description, this is done using admin_url if provided
        "tenant_name": string max lenght 64
        "tenant_description": string max length 256
        returns the tenant identifier or raise exception
        """
        raise vimconnNotImplemented( "Should have implemented this" )

    def delete_tenant(self,tenant_id,):
        """Delete a tenant from VIM
        tenant_id: returned VIM tenant_id on "new_tenant"
        Returns None on success. Raises and exception of failure. If tenant is not found raises vimconnNotFoundException
        """
        raise vimconnNotImplemented( "Should have implemented this" )

    def get_tenant_list(self, filter_dict={}):
        """Obtain tenants of VIM
        filter_dict dictionary that can contain the following keys:
            name: filter by tenant name
            id: filter by tenant uuid/id
            <other VIM specific>
        Returns the tenant list of dictionaries, and empty list if no tenant match all the filers:
            [{'name':'<name>, 'id':'<id>, ...}, ...]
        """
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_network(self, net_name, net_type, ip_profile=None, shared=False, vlan=None):
        """Adds a tenant network to VIM
        Params:
            'net_name': name of the network
            'net_type': one of:
                'bridge': overlay isolated network
                'data':   underlay E-LAN network for Passthrough and SRIOV interfaces
                'ptp':    underlay E-LINE network for Passthrough and SRIOV interfaces.
            'ip_profile': is a dict containing the IP parameters of the network
                'ip_version': can be "IPv4" or "IPv6" (Currently only IPv4 is implemented)
                'subnet_address': ip_prefix_schema, that is X.X.X.X/Y
                'gateway_address': (Optional) ip_schema, that is X.X.X.X
                'dns_address': (Optional) comma separated list of ip_schema, e.g. X.X.X.X[,X,X,X,X]
                'dhcp_enabled': True or False
                'dhcp_start_address': ip_schema, first IP to grant
                'dhcp_count': number of IPs to grant.
            'shared': if this network can be seen/use by other tenants/organization
            'vlan': in case of a data or ptp net_type, the intended vlan tag to be used for the network
        Returns the network identifier on success or raises and exception on failure
        """
        self.logger.debug('Args: {}'.format(locals()))
        net_uuid = '{}'.format(uuid.uuid4())
        desc = {
            'uuid':net_uuid,
            'name':net_name,
            'net_type':'ELAN'
            }
        self.fos_api.network.add_network(desc)
        return net_uuid
        # raise vimconnNotImplemented( "Should have implemented this" )

    def get_network_list(self, filter_dict={}):
        """Obtain tenant networks of VIM
        Params:
            'filter_dict' (optional) contains entries to return only networks that matches ALL entries:
                name: string  => returns only networks with this name
                id:   string  => returns networks with this VIM id, this imply returns one network at most
                shared: boolean >= returns only networks that are (or are not) shared
                tenant_id: sting => returns only networks that belong to this tenant/project
                ,#(not used yet) admin_state_up: boolean => returns only networks that are (or are not) in admin state active
                #(not used yet) status: 'ACTIVE','ERROR',... => filter networks that are on this status
        Returns the network list of dictionaries. each dictionary contains:
            'id': (mandatory) VIM network id
            'name': (mandatory) VIM network name
            'status': (mandatory) can be 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'network_type': (optional) can be 'vxlan', 'vlan' or 'flat'
            'segmentation_id': (optional) in case network_type is vlan or vxlan this field contains the segmentation id
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no network map the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        res = []

        net_from_fos = self.fos_api.network.list()
        for n in net_from_fos:
            osm_net = {
                'id':n.get('uuid'),
                'name':n.get('name'),
                'status':'ACTIVE'
            }
            res.append(osm_net)
        return res

    def get_network(self, net_id):
        """Obtain network details from the 'net_id' VIM network
        Return a dict that contains:
            'id': (mandatory) VIM network id, that is, net_id
            'name': (mandatory) VIM network name
            'status': (mandatory) can be 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        Raises an exception upon error or when network is not found
        """
        self.logger.debug('Args: {}'.format(locals()))
        res = [x for x in self.get_network_list() if x.get('id') == net_id]
        if len(res) == 0:
            raise vimconnNotFoundException("Network not found" )
        return res[0]

    def delete_network(self, net_id):
        """Deletes a tenant network from VIM
        Returns the network identifier or raises an exception upon error or when network is not found
        """
        raise vimconnNotImplemented( "Should have implemented this" )

    def refresh_nets_status(self, net_list):
        """Get the status of the networks
        Params:
            'net_list': a list with the VIM network id to be get the status
        Returns a dictionary with:
            'net_id':         #VIM id of this network
                status:     #Mandatory. Text with one of:
                    #  DELETED (not found at vim)
                    #  VIM_ERROR (Cannot connect to VIM, authentication problems, VIM response error, ...)
                    #  OTHER (Vim reported other status not understood)
                    #  ERROR (VIM indicates an ERROR status)
                    #  ACTIVE, INACTIVE, DOWN (admin down),
                    #  BUILD (on building process)
                error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR
                vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)
            'net_id2': ...
        """
        self.logger.debug('Args: {}'.format(locals()))
        r = {}
        for n in net_list:
            osm_n = self.get_network(n)
            r.update({
                osm_n.get('id'):{'status':osm_n.get('status')}
            })
        return r

    def get_flavor(self, flavor_id):
        """Obtain flavor details from the VIM
        Returns the flavor dict details {'id':<>, 'name':<>, other vim specific }
        Raises an exception upon error or if not found
        """
        self.logger.debug('Args: {}'.format(locals()))
        r = self.fos_api.flavor.get(flavor_id)
        if r is None:
            raise vimconnNotFoundException( "Flavor not found" )
        return {'id':r.get('uuid'), 'name':r.get('name'), 'fos':r}

    def get_flavor_id_from_data(self, flavor_dict):
        """Obtain flavor id that match the flavor description
        Params:
            'flavor_dict': dictionary that contains:
                'disk': main hard disk in GB
                'ram': meomry in MB
                'vcpus': number of virtual cpus
                #TODO: complete parameters for EPA
        Returns the flavor_id or raises a vimconnNotFoundException
        """
        self.logger.debug('Args: {}'.format(locals()))
        flvs = self.fos_api.flavor.list()
        r = [x.get('uuid') for x in flvs if (x.get('cpu_min_count') == flavor_dict.get('vcpus') and x.get('ram_size_mb') == flavor_dict.get('ram') and x.get('storage_size_gb') == flavor_dict.get('disk'))]
        if len(r) == 0:
            raise vimconnNotImplemented( "Should have implemented this" )
        return r[0]

    def new_flavor(self, flavor_data):
        """Adds a tenant flavor to VIM
            flavor_data contains a dictionary with information, keys:
                name: flavor name
                ram: memory (cloud type) in MBytes
                vpcus: cpus (cloud type)
                extended: EPA parameters
                  - numas: #items requested in same NUMA
                        memory: number of 1G huge pages memory
                        paired-threads|cores|threads: number of paired hyperthreads, complete cores OR individual threads
                        interfaces: # passthrough(PT) or SRIOV interfaces attached to this numa
                          - name: interface name
                            dedicated: yes|no|yes:sriov;  for PT, SRIOV or only one SRIOV for the physical NIC
                            bandwidth: X Gbps; requested guarantee bandwidth
                            vpci: requested virtual PCI address
                disk: disk size
                is_public:
                 #TODO to concrete
        Returns the flavor identifier"""
        self.logger.debug('Args: {}'.format(locals()))
        flv_id = '{}'.format(uuid.uuid4())
        desc = {
            'uuid':flv_id,
            'name':flavor_data.get('name'),
            'cpu_arch': self.arch,
            'cpu_min_count': flavor_data.get('vcpus'),
            'cpu_min_freq': 0.0,
            'ram_size_gb':flavor_data.get('ram'),
            'storage_size_gb':flavor_data.get('disk')
        }
        self.fos_api.flavor.add(desc)
        return flv_id


    def delete_flavor(self, flavor_id):
        """Deletes a tenant flavor from VIM identify by its id
        Returns the used id or raise an exception"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_image(self, image_dict):
        """ Adds a tenant image to VIM. imge_dict is a dictionary with:
            name: name
            disk_format: qcow2, vhd, vmdk, raw (by default), ...
            location: path or URI
            public: "yes" or "no"
            metadata: metadata of the image
        Returns the image id or raises an exception if failed
        """
        self.logger.debug('Args: {}'.format(locals()))
        img_id = '{}'.format(uuid.uuid4())
        desc = {
            'name':image_dict.get('name'),
            'uuid':img_id,
            'uri':image_dict.get('location')
        }
        self.fos_api.image.add(desc)
        return img_id
        #raise vimconnNotImplemented( "Should have implemented this" )

    def delete_image(self, image_id):
        """Deletes a tenant image from VIM
        Returns the image_id if image is deleted or raises an exception on error"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def get_image_id_from_path(self, path):

        """Get the image id from image path in the VIM database.
           Returns the image_id or raises a vimconnNotFoundException
        """
        self.logger.debug('Args: {}'.format(locals()))
        imgs = self.fos_api.image.list()
        res = [x.get('uuid') for x in imgs if x.get('uri')==path]
        if len(res) == 0:
            raise vimconnNotFoundException("Image with this path was not found")
        return res[0]

        #raise vimconnNotImplemented( "Should have implemented this" )

    def get_image_list(self, filter_dict={}):
        """Obtain tenant images from VIM
        Filter_dict can be:
            name: image name
            id: image uuid
            checksum: image checksum
            location: image path
        Returns the image list of dictionaries:
            [{<the fields at Filter_dict plus some VIM specific>}, ...]
            List can be empty
        """
        self.logger.debug('Args: {}'.format(locals()))
        r = []
        fimgs = self.fos_api.image.list()
        for i in fimgs:
            img_info = {
                'name':i.get('name'),
                'id':i.get('uuid'),
                'checksum':i.get('checksum'),
                'location':i/get('uri'),
                'fos':i
            }
            r.append(img_info)
        return r
        #raise vimconnNotImplemented( "Should have implemented this" )

    def new_vminstance(self, name, description, start, image_id, flavor_id, net_list, cloud_config=None, disk_list=None,
        availability_zone_index=None, availability_zone_list=None):
        """Adds a VM instance to VIM
        Params:
            'start': (boolean) indicates if VM must start or created in pause mode.
            'image_id','flavor_id': image and flavor VIM id to use for the VM
            'net_list': list of interfaces, each one is a dictionary with:
                'name': (optional) name for the interface.
                'net_id': VIM network id where this interface must be connect to. Mandatory for type==virtual
                'vpci': (optional) virtual vPCI address to assign at the VM. Can be ignored depending on VIM capabilities
                'model': (optional and only have sense for type==virtual) interface model: virtio, e1000, ...
                'mac_address': (optional) mac address to assign to this interface
                'ip_address': (optional) IP address to assign to this interface
                #TODO: CHECK if an optional 'vlan' parameter is needed for VIMs when type if VF and net_id is not provided,
                    the VLAN tag to be used. In case net_id is provided, the internal network vlan is used for tagging VF
                'type': (mandatory) can be one of:
                    'virtual', in this case always connected to a network of type 'net_type=bridge'
                     'PCI-PASSTHROUGH' or 'PF' (passthrough): depending on VIM capabilities it can be connected to a data/ptp network ot it
                           can created unconnected
                     'SR-IOV' or 'VF' (SRIOV with VLAN tag): same as PF for network connectivity.
                     'VFnotShared'(SRIOV without VLAN tag) same as PF for network connectivity. VF where no other VFs
                            are allocated on the same physical NIC
                'bw': (optional) only for PF/VF/VFnotShared. Minimal Bandwidth required for the interface in GBPS
                'port_security': (optional) If False it must avoid any traffic filtering at this interface. If missing
                                or True, it must apply the default VIM behaviour
                After execution the method will add the key:
                'vim_id': must be filled/added by this method with the VIM identifier generated by the VIM for this
                        interface. 'net_list' is modified
            'cloud_config': (optional) dictionary with:
                'key-pairs': (optional) list of strings with the public key to be inserted to the default user
                'users': (optional) list of users to be inserted, each item is a dict with:
                    'name': (mandatory) user name,
                    'key-pairs': (optional) list of strings with the public key to be inserted to the user
                'user-data': (optional) can be a string with the text script to be passed directly to cloud-init,
                    or a list of strings, each one contains a script to be passed, usually with a MIMEmultipart file
                'config-files': (optional). List of files to be transferred. Each item is a dict with:
                    'dest': (mandatory) string with the destination absolute path
                    'encoding': (optional, by default text). Can be one of:
                        'b64', 'base64', 'gz', 'gz+b64', 'gz+base64', 'gzip+b64', 'gzip+base64'
                    'content' (mandatory): string with the content of the file
                    'permissions': (optional) string with file permissions, typically octal notation '0644'
                    'owner': (optional) file owner, string with the format 'owner:group'
                'boot-data-drive': boolean to indicate if user-data must be passed using a boot drive (hard disk)
            'disk_list': (optional) list with additional disks to the VM. Each item is a dict with:
                'image_id': (optional). VIM id of an existing image. If not provided an empty disk must be mounted
                'size': (mandatory) string with the size of the disk in GB
            availability_zone_index: Index of availability_zone_list to use for this this VM. None if not AV required
            availability_zone_list: list of availability zones given by user in the VNFD descriptor.  Ignore if
                availability_zone_index is None
        Returns a tuple with the instance identifier and created_items or raises an exception on error
            created_items can be None or a dictionary where this method can include key-values that will be passed to
            the method delete_vminstance and action_vminstance. Can be used to store created ports, volumes, etc.
            Format is vimconnector dependent, but do not use nested dictionaries and a value of None should be the same
            as not present.
        """
        self.logger.debug('Args: {}'.format(locals()))
        fdu_uuid = '{}'.format(uuid.uuid4())

        flv = self.fos_api.flavor.get(flavor_id)
        img =  self.fos_api.image.get(image_id)


        created_items = {
            'fdu_id':'',
            'node_id':'',
            'connection_points':[]
            }

        fdu_desc = {
            'name':name,
            'uuid':fdu_uuid,
            'computation_requirements':flv,
            'image':img,
            'hypervisor':self.hv,
            'migration_kind':'LIVE',
            'interfaces':[],
            'io_ports':[],
            'connection_points':[],
            'depends_on':[]
        }

        nets = []
        cps = []
        intf_id = 0
        for n in net_list:
            cp_id = '{}'.format(uuid.uuid4())
            pair_id = n.get('net_id')

            cp_d = {
                'uuid':cp_id,
                'pair_id':pair_id
            }
            intf_d = {
                'name':n.get('name','eth{}'.format(intf_id)),
                'is_mgmt':False,
                'if_type':'INTERNAL',
                'virtual_interface':{
                    'intf_type':n.get('model','VIRTIO'),
                    'vpci':n.get('vpci','0:0:0'),
                    'bandwidth':n.get('bw', 10)
                }
            }
            if n.get('mac_address', None) is not None:
                intf_d.update({'mac_address':n.get('mac_address')})

            created_items.get('connection_points').append(cp_id)
            fdu_desc.get('connection_points').append(cp_d)
            fdu_desc.get('interfaces').append(intf_d)

            intf_id = intf_id + 1

        if cloud_config is not None:
            configuration = {
                    'conf_type':'CLOUD_INIT'
                }
            if cloud_config.get('user-data') is not None:
                configuration.update({'script':cloud_config.get('user-data')})
            if cloud_config.get('key-pairs') is not None:
                configuration.update({'ssh_keys':cloud_config.get('key-pairs')})

            if 'script' in configuration:
                fdu_desc.update({'configuration':configuration})

        ### NODE Selection ###
        # Infrastructure info
        #   nodes dict with
        #        uuid -> node uuid
        #        computational capabilities -> cpu, ram, and disk available
        #        hypervisors -> list of available hypervisors (eg. KVM, LXD, BARE)
        #
        #

        # UPDATING AVAILABLE INFRASTRUCTURE
        nodes = []
        for n in self.fos_api.node.list():
            n_info = self.fos_api.node.info(n)
            n_plugs = []
            for p in self.fos_api.node.plugins():
                n_plugs.append(self.fos_api.plugin.info(n,p))

            n_cpu_number =  len(n_info.get('cpu'))
            n_cpu_arch = n_info.get('cpu')[0].get('arch')
            n_cpu_freq = n_info.get('cpu')[0].get('frequency')
            n_ram = n_info.get('ram').get('size')
            n_disk_size = sorted(list(filter(lambda x: 'sda' in x['local_address'], n_info.get('disk'))), key= lambda k: k['dimension'])[0].get('dimension')

            hvs = []
            for p in n_plugs:
                if p.get('type') == 'runtime':
                    hvs.append(p.get('name'))

            ni = {
                'uuid':n,
                'computational_capabilities':{
                    'cpu_count':n_cpu_number,
                    'cpu_arch':n_cpu_arch,
                    'cpu_freq':n_cpu_freq,
                    'ram_size':n_ram,
                    'disk_size':n_disk_size
                },
                'hypervisors':hvs
            }
            nodes.append(ni)

        # NODE SELECTION
        compatible_nodes = []
        for n in nodes:
            if fdu_desc.get('hypervisor') in n.get('hvs'):
                n_comp = n.get('computational_capabilities')
                f_comp = fdu_desc.get('computation_requirements')
                if f_comp.get('cpu_arch') == n_comp.get('cpu_arch'):
                    if f_comp.get('cpu_min_count') <= n_comp.get('cpu_count') and f_comp.get('ram_size_mb') <= n_comp.get('ram_size'):
                        if f_comp.get('disk_size') <= n_comp.get('disk_size'):
                            compatible_nodes.append(n)

        if len(compatible_nodes) == 0:
            raise vimconnConflictException("No available nodes")
        selected_node = random.choice(compatible_nodes)

        created_items.update({'fdu_id':fdu_uuid, 'node_id': selected_node.get('uuid')})

        self.fos_api.fdu.onboard(fdu_desc)
        self.fos_api.fdu.define(fdu_uuid, selected_node.get('uuid'), wait=True)
        self.fos_api.fdu.configure(fdu_uuid, selected_node.get('uuid'), wait=True)
        if start:
            self.fos_api.fdu.run(fdu_uuid, selected_node.get('uuid'), wait=True)

        self.fdu_node_map.update({fdu_uuid: selected_node.get('uuid')})
        return (fdu_uuid, created_items)
        #raise vimconnNotImplemented( "Should have implemented this" )

    def get_vminstance(self,vm_id):
        """Returns the VM instance information from VIM"""
        self.logger.debug('Args: {}'.format(locals()))

        fdus = self.fos_api.fdu.list()
        for f in fdus:
            if f.get('uuid') == vm_id:
                return f
        raise vimconnNotFoundException('VM not found!')

        #raise vimconnNotImplemented( "Should have implemented this" )

    def delete_vminstance(self, vm_id, created_items=None):
        """
        Removes a VM instance from VIM and each associate elements
        :param vm_id: VIM identifier of the VM, provided by method new_vminstance
        :param created_items: dictionary with extra items to be deleted. provided by method new_vminstance and/or method
            action_vminstance
        :return: None or the same vm_id. Raises an exception on fail
        """
        self.logger.debug('Args: {}'.format(locals()))
        nid =  created_items.get('node_id')
        self.fos_api.fdu.stop(vm_id, nid, wait=True)
        self.fos_api.fdu.clean(vm_id, nid, wait=True)
        self.fos_api.fdu.undefine(vm_id, nid, wait=True)
        self.fos_api.fdu.offload(vm_id)
        return vm_id

        #raise vimconnNotImplemented( "Should have implemented this" )

    def refresh_vms_status(self, vm_list):
        """Get the status of the virtual machines and their interfaces/ports
           Params: the list of VM identifiers
           Returns a dictionary with:
                vm_id:          #VIM id of this Virtual Machine
                    status:     #Mandatory. Text with one of:
                                #  DELETED (not found at vim)
                                #  VIM_ERROR (Cannot connect to VIM, VIM response error, ...)
                                #  OTHER (Vim reported other status not understood)
                                #  ERROR (VIM indicates an ERROR status)
                                #  ACTIVE, PAUSED, SUSPENDED, INACTIVE (not running),
                                #  BUILD (on building process), ERROR
                                #  ACTIVE:NoMgmtIP (Active but any of its interface has an IP address
                                #
                    error_msg:  #Text with VIM error message, if any. Or the VIM connection ERROR
                    vim_info:   #Text with plain information obtained from vim (yaml.safe_dump)
                    interfaces: list with interface info. Each item a dictionary with:
                        vim_info:         #Text with plain information obtained from vim (yaml.safe_dump)
                        mac_address:      #Text format XX:XX:XX:XX:XX:XX
                        vim_net_id:       #network id where this interface is connected, if provided at creation
                        vim_interface_id: #interface/port VIM id
                        ip_address:       #null, or text with IPv4, IPv6 address
                        compute_node:     #identification of compute node where PF,VF interface is allocated
                        pci:              #PCI address of the NIC that hosts the PF,VF
                        vlan:             #physical VLAN used for VF
        """
        self.logger.debug('Args: {}'.format(locals()))

        fos2osm_status = {
            'DEFINE':'OTHER',
            'CONFIGURE':'INACTIVE',
            'RUN':'ACTIVE',
            'PAUSE':'PAUSED',
            'ERROR':'ERROR'
        }

        r = {}
        for vm in vm_list:
            desc = self.fos_api.fdu.info(vm)
            i = {}
            nid = self.fdu_node_map.get(vm)
            if nid is None:
                raise vimconnNotFoundException('VM has no node associated!!')

            vm_info = self.fos_api.fdu.instance_info(vm, nid)
            osm_status = fos2osm_status.get(vm_info.get('status'))
            i.update({'status':osm_status})
            if vm_info.get('status') == 'ERROR':
                i.update({'error_msg':vm_info.get('error_code')})
            i.update({'vim_info':vm_info})
            r.update({vm:i})
        return r


        #raise vimconnNotImplemented( "Should have implemented this" )

    def action_vminstance(self, vm_id, action_dict, created_items={}):
        """
        Send and action over a VM instance. Returns created_items if the action was successfully sent to the VIM.
        created_items is a dictionary with items that
        :param vm_id: VIM identifier of the VM, provided by method new_vminstance
        :param action_dict: dictionary with the action to perform
        :param created_items: provided by method new_vminstance is a dictionary with key-values that will be passed to
            the method delete_vminstance. Can be used to store created ports, volumes, etc. Format is vimconnector
            dependent, but do not use nested dictionaries and a value of None should be the same as not present. This
            method can modify this value
        :return: None, or a console dict
        """
        self.logger.debug('Args: {}'.format(locals()))
        nid = self.fdu_node_map(vm_id)
        if nid is None:
            raise vimconnNotFoundException('No node for this VM')
        fdu_info = self.fos_api.fdu.instance_info(vm_id, nid)
        if "start" in action_dict:
            if fdu_info.get('status') == 'CONFIGURE':
                self.fos_api.fdu.run(vm_id, nid, wait=True)
            elif fdu_info.get('status') == 'PAUSE':
                self.fos_api.fdu.resume(vm_id, nid, wait=True)
            else:
                raise vimconnConflictException("Cannot start from this state")
        elif "pause" in action_dict:
            if fdu_info.get('status') == 'RUN':
                self.fos_api.fdu.pause(vm_id, nid, wait=True)
            else:
                raise vimconnConflictException("Cannot pause from this state")
        elif "resume" in action_dict:
            if fdu_info.get('status') == 'PAUSE':
                self.fos_api.fdu.resume(vm_id, nid, wait=True)
            else:
                raise vimconnConflictException("Cannot resume from this state")
        elif "shutoff" in action_dict or "shutdown" or "forceOff" in action_dict:
            if fdu_info.get('status') == 'RUN':
                self.fos_api.fdu.stop(vm_id, nid, wait=True)
            else:
                raise vimconnConflictException("Cannot shutoff from this state")
        elif "terminate" in action_dict:
            if fdu_info.get('status') == 'RUN':
                self.fos_api.fdu.stop(vm_id, nid, wait=True)
                self.fos_api.fdu.clean(vm_id, nid, wait=True)
                self.fos_api.fdu.undefine(vm_id, nid, wait=True)
                self.fos_api.fdu.offload(vm_id)
            elif fdu_info.get('status') == 'CONFIGURE':
                self.fos_api.fdu.clean(vm_id, nid, wait=True)
                self.fos_api.fdu.undefine(vm_id, nid, wait=True)
                self.fos_api.fdu.offload(vm_id)
            elif fdu_info.get('status') == 'PAUSE':
                self.fos_api.fdu.resume(vm_id, nid, wait=True)
                self.fos_api.fdu.stop(vm_id, nid, wait=True)
                self.fos_api.fdu.clean(vm_id, nid, wait=True)
                self.fos_api.fdu.undefine(vm_id, nid, wait=True)
                self.fos_api.fdu.offload(vm_id)
            else:
                raise vimconnConflictException("Cannot terminate from this state")
        elif "rebuild" in action_dict:
            raise vimconnNotImplemented("Rebuild not implememnted")
        elif "reboot" in action_dict:
            if fdu_info.get('status') == 'RUN':
                self.fos_api.fdu.stop(vm_id, nid, wait=True)
                self.fos_api.fdu.start(vm_id, nid, wait=True)
            else:
                raise vimconnConflictException("Cannot reboot from this state")

        #raise vimconnNotImplemented( "Should have implemented this" )


    def get_vminstance_console(self, vm_id, console_type="vnc"):
        """
        Get a console for the virtual machine
        Params:
            vm_id: uuid of the VM
            console_type, can be:
                "novnc" (by default), "xvpvnc" for VNC types,
                "rdp-html5" for RDP types, "spice-html5" for SPICE types
        Returns dict with the console parameters:
                protocol: ssh, ftp, http, https, ...
                server:   usually ip address
                port:     the http, ssh, ... port
                suffix:   extra text, e.g. the http path and query string
        """
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_classification(self, name, ctype, definition):
        """Creates a traffic classification in the VIM
        Params:
            'name': name of this classification
            'ctype': type of this classification
            'definition': definition of this classification (type-dependent free-form text)
        Returns the VIM's classification ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_classification(self, classification_id):
        """Obtain classification details of the VIM's classification with ID='classification_id'
        Return a dict that contains:
            'id': VIM's classification ID (same as classification_id)
            'name': VIM's classification name
            'type': type of this classification
            'definition': definition of the classification
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when classification is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_classification_list(self, filter_dict={}):
        """Obtain classifications from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the classifications on and only return those that match ALL:
                id:   string => returns classifications with this VIM's classification ID, which implies a return of one classification at most
                name: string => returns only classifications with this name
                type: string => returns classifications of this type
                definition: string => returns classifications that have this definition
                tenant_id: string => returns only classifications that belong to this tenant/project
        Returns a list of classification dictionaries, each dictionary contains:
            'id': (mandatory) VIM's classification ID
            'name': (mandatory) VIM's classification name
            'type': type of this classification
            'definition': definition of the classification
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no classification matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def delete_classification(self, classification_id):
        """Deletes a classification from the VIM
        Returns the classification ID (classification_id) or raises an exception upon error or when classification is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def new_sfi(self, name, ingress_ports, egress_ports, sfc_encap=True):
        """Creates a service function instance in the VIM
        Params:
            'name': name of this service function instance
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            'sfc_encap': boolean stating whether this specific instance supports IETF SFC Encapsulation
        Returns the VIM's service function instance ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_sfi(self, sfi_id):
        """Obtain service function instance details of the VIM's service function instance with ID='sfi_id'
        Return a dict that contains:
            'id': VIM's sfi ID (same as sfi_id)
            'name': VIM's sfi name
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when service function instance is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_sfi_list(self, filter_dict={}):
        """Obtain service function instances from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfis on and only return those that match ALL:
                id:   string  => returns sfis with this VIM's sfi ID, which implies a return of one sfi at most
                name: string  => returns only service function instances with this name
                tenant_id: string => returns only service function instances that belong to this tenant/project
        Returns a list of service function instance dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sfi ID
            'name': (mandatory) VIM's sfi name
            'ingress_ports': set of ingress ports (VIM's port IDs)
            'egress_ports': set of egress ports (VIM's port IDs)
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sfi matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def delete_sfi(self, sfi_id):
        """Deletes a service function instance from the VIM
        Returns the service function instance ID (sfi_id) or raises an exception upon error or when sfi is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def new_sf(self, name, sfis, sfc_encap=True):
        """Creates (an abstract) service function in the VIM
        Params:
            'name': name of this service function
            'sfis': set of service function instances of this (abstract) service function
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
        Returns the VIM's service function ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_sf(self, sf_id):
        """Obtain service function details of the VIM's service function with ID='sf_id'
        Return a dict that contains:
            'id': VIM's sf ID (same as sf_id)
            'name': VIM's sf name
            'sfis': VIM's sf's set of VIM's service function instance IDs
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when sf is not found
        """

    def get_sf_list(self, filter_dict={}):
        """Obtain service functions from the VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfs on and only return those that match ALL:
                id:   string  => returns sfs with this VIM's sf ID, which implies a return of one sf at most
                name: string  => returns only service functions with this name
                tenant_id: string => returns only service functions that belong to this tenant/project
        Returns a list of service function dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sf ID
            'name': (mandatory) VIM's sf name
            'sfis': VIM's sf's set of VIM's service function instance IDs
            'sfc_encap': boolean stating whether this service function supports IETF SFC Encapsulation
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sf matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def delete_sf(self, sf_id):
        """Deletes (an abstract) service function from the VIM
        Returns the service function ID (sf_id) or raises an exception upon error or when sf is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )


    def new_sfp(self, name, classifications, sfs, sfc_encap=True, spi=None):
        """Creates a service function path
        Params:
            'name': name of this service function path
            'classifications': set of traffic classifications that should be matched on to get into this sfp
            'sfs': list of every service function that constitutes this path , from first to last
            'sfc_encap': whether this is an SFC-Encapsulated chain (i.e using NSH), True by default
            'spi': (optional) the Service Function Path identifier (SPI: Service Path Identifier) for this path
        Returns the VIM's sfp ID on success or raises an exception on failure
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_sfp(self, sfp_id):
        """Obtain service function path details of the VIM's sfp with ID='sfp_id'
        Return a dict that contains:
            'id': VIM's sfp ID (same as sfp_id)
            'name': VIM's sfp name
            'classifications': VIM's sfp's list of VIM's classification IDs
            'sfs': VIM's sfp's list of VIM's service function IDs
            'status': 'ACTIVE', 'INACTIVE', 'DOWN', 'BUILD', 'ERROR', 'VIM_ERROR', 'OTHER'
            'error_msg': (optional) text that explains the ERROR status
            other VIM specific fields: (optional) whenever possible
        Raises an exception upon error or when sfp is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def get_sfp_list(self, filter_dict={}):
        """Obtain service function paths from VIM
        Params:
            'filter_dict' (optional): contains the entries to filter the sfps on, and only return those that match ALL:
                id:   string  => returns sfps with this VIM's sfp ID , which implies a return of one sfp at most
                name: string  => returns only sfps with this name
                tenant_id: string => returns only sfps that belong to this tenant/project
        Returns a list of service function path dictionaries, each dictionary contains:
            'id': (mandatory) VIM's sfp ID
            'name': (mandatory) VIM's sfp name
            'classifications': VIM's sfp's list of VIM's classification IDs
            'sfs': VIM's sfp's list of VIM's service function IDs
            other VIM specific fields: (optional) whenever possible using the same naming of filter_dict param
        List can be empty if no sfp matches the filter_dict. Raise an exception only upon VIM connectivity,
            authorization, or some other unspecific error
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def delete_sfp(self, sfp_id):
        """Deletes a service function path from the VIM
        Returns the sfp ID (sfp_id) or raises an exception upon error or when sf is not found
        """
        raise vimconnNotImplemented( "SFC support not implemented" )

    def inject_user_key(self, ip_addr=None, user=None, key=None, ro_key=None, password=None):
        """
        Inject a ssh public key in a VM
        Params:
            ip_addr: ip address of the VM
            user: username (default-user) to enter in the VM
            key: public key to be injected in the VM
            ro_key: private key of the RO, used to enter in the VM if the password is not provided
            password: password of the user to enter in the VM
        The function doesn't return a value:
        """
        if not ip_addr or not user:
            raise vimconnNotSupportedException("All parameters should be different from 'None'")
        elif not ro_key and not password:
            raise vimconnNotSupportedException("All parameters should be different from 'None'")
        else:
            commands = {'mkdir -p ~/.ssh/', 'echo "%s" >> ~/.ssh/authorized_keys' % key,
                        'chmod 644 ~/.ssh/authorized_keys', 'chmod 700 ~/.ssh/'}
            client = paramiko.SSHClient()
            try:
                if ro_key:
                    pkey = paramiko.RSAKey.from_private_key(StringIO.StringIO(ro_key))
                else:
                    pkey = None
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip_addr, username=user, password=password, pkey=pkey, timeout=10)
                for command in commands:
                    (i, o, e) = client.exec_command(command, timeout=10)
                    returncode = o.channel.recv_exit_status()
                    output = o.read()
                    outerror = e.read()
                    if returncode != 0:
                        text = "run_command='{}' Error='{}'".format(command, outerror)
                        raise vimconnUnexpectedResponse("Cannot inject ssh key in VM: '{}'".format(text))
                        return
            except (socket.error, paramiko.AuthenticationException, paramiko.SSHException) as message:
                raise vimconnUnexpectedResponse(
                    "Cannot inject ssh key in VM: '{}' - {}".format(ip_addr, str(message)))
                return


#NOT USED METHODS in current version

    def host_vim2gui(self, host, server_dict):
        """Transform host dictionary from VIM format to GUI format,
        and append to the server_dict
        """
        raise vimconnNotImplemented( "Should have implemented this" )

    def get_hosts_info(self):
        """Get the information of deployed hosts
        Returns the hosts content"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def get_hosts(self, vim_tenant):
        """Get the hosts and deployed instances
        Returns the hosts content"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def get_processor_rankings(self):
        """Get the processor rankings in the VIM database"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_host(self, host_data):
        """Adds a new host to VIM"""
        """Returns status code of the VIM response"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_external_port(self, port_data):
        """Adds a external port to VIM"""
        """Returns the port identifier"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_external_network(self,net_name,net_type):
        """Adds a external network to VIM (shared)"""
        """Returns the network identifier"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def connect_port_network(self, port_id, network_id, admin=False):
        """Connects a external port to a network"""
        """Returns status code of the VIM response"""
        raise vimconnNotImplemented( "Should have implemented this" )

    def new_vminstancefromJSON(self, vm_data):
        """Adds a VM instance to VIM"""
        """Returns the instance identifier"""
        raise vimconnNotImplemented( "Should have implemented this" )

