
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


def create_path(tokens):
    return '/'.join(tokens)


def append_to_path(base, extention):
    return '{}/{}'.format(base, extention)
