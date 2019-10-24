from enum import Enum


aroot = '/afos'
droot = '/dfos'
sroot = '/sfos'


global_actual_prefix = '/agfos'
global_desired_prefix = '/dgfos'
local_actual_prefix = '/alfos'
local_desired_prefix = '/dlfos'

local_constraint_actual_prefix = '/aclfos'
local_constaint_desired_prefix = '/dclfos'

default_system_id = '0'
default_tenant_id = '0'




class FDUState(Enum):

    '''
    States of FDUs
    '''
    DEFINE = 'DEFINE'
    CONFIGURE = 'CONFIGURE'
    CLEAN = 'CLEAN'
    RUN = 'RUN'
    STARTING = 'STARTING'
    STOP = 'STOP'
    RESUME = 'RESUME'
    PAUSE = 'PAUSE'
    SCALE = 'SCALE'
    TAKE_OFF = 'TAKE_OFF'
    LAND = 'LAND'
    MIGRATE = 'MIGRATE'
    UNDEFINE = 'UNDEFINE'
    ERROR = 'ERROR'


class ErrorCodes(Enum):
    '''
    FDUs error codes
    '''

    DEFINE_ERROR = 1
    CONFIGURE_ERROR = 2
    CLEAN_ERROR = 3
    RUN_ERROR = 4
    STOP_ERROR = 5
    PAUSE_ERROR = 6
    TAKE_OFF_ERROR = 8
    LAND_ERROR = 9
    MIGRATE_ERROR = 10
    UNDEFINE_ERROR = 0

    FDU_DESCRIPTOR_NOT_FOUND = 11
    NETWORK_DESCRIPTOR_NOT_FOUND = 22
    CONNECTION_POINT_DESCRIPTOR_NOT_FOUND = 33

    IMAGE_NOT_FOUND = 21
    COMPUTE_REQUIREMENTS_ERROR = 23
    HYPERVISOR_ERROR = 41








def create_path(tokens):
    return '/'.join(tokens)


def append_to_path(base, extention):
    return '{}/{}'.format(base, extention)
