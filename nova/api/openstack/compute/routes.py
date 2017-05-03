# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import functools

import nova.api.openstack
from nova.api.openstack.compute import admin_actions
from nova.api.openstack.compute import admin_password
from nova.api.openstack.compute import aggregates
from nova.api.openstack.compute import config_drive
from nova.api.openstack.compute import console_output
from nova.api.openstack.compute import create_backup
from nova.api.openstack.compute import deferred_delete
from nova.api.openstack.compute import evacuate
from nova.api.openstack.compute import extended_availability_zone
from nova.api.openstack.compute import extended_server_attributes
from nova.api.openstack.compute import extended_status
from nova.api.openstack.compute import extended_volumes
from nova.api.openstack.compute import extension_info
from nova.api.openstack.compute import flavor_access
from nova.api.openstack.compute import flavor_manage
from nova.api.openstack.compute import flavor_rxtx
from nova.api.openstack.compute import flavors
from nova.api.openstack.compute import flavors_extraspecs
from nova.api.openstack.compute import floating_ips
from nova.api.openstack.compute import hide_server_addresses
from nova.api.openstack.compute import keypairs
from nova.api.openstack.compute import lock_server
from nova.api.openstack.compute import migrate_server
from nova.api.openstack.compute import multinic
from nova.api.openstack.compute import pause_server
from nova.api.openstack.compute import remote_consoles
from nova.api.openstack.compute import rescue
from nova.api.openstack.compute import security_groups
from nova.api.openstack.compute import server_metadata
from nova.api.openstack.compute import server_usage
from nova.api.openstack.compute import servers
from nova.api.openstack.compute import shelve
from nova.api.openstack.compute import suspend_server
from nova.api.openstack import wsgi
import nova.conf


CONF = nova.conf.CONF


def _create_controller(main_controller, controller_list,
                      action_controller_list):
    """This is a helper method to create controller with a
    list of extended controller. This is for backward compatible
    with old extension interface. Finally, the controller for the
    same resource will be merged into single one controller.
    """

    controller = wsgi.ResourceV21(main_controller())
    for ctl in controller_list:
        controller.register_extensions(ctl())
    for ctl in action_controller_list:
        controller.register_actions(ctl())
    return controller


aggregates_controller = functools.partial(
    _create_controller, aggregates.AggregateController, [], [])


keypairs_controller = functools.partial(
    _create_controller, keypairs.KeypairController, [], [])


flavor_controller = functools.partial(_create_controller,
    flavors.FlavorsController,
    [
        flavor_rxtx.FlavorRxtxController,
        flavor_access.FlavorActionController
    ],
    [
        flavor_manage.FlavorManageController,
        flavor_access.FlavorActionController
    ]
)


flavor_access_controller = functools.partial(_create_controller,
    flavor_access.FlavorAccessController, [], [])


flavor_extraspec_controller = functools.partial(_create_controller,
    flavors_extraspecs.FlavorExtraSpecsController, [], [])


floating_ips_controller = functools.partial(_create_controller,
    floating_ips.FloatingIPController, [], [])


server_controller = functools.partial(_create_controller,
    servers.ServersController,
    [
        config_drive.ConfigDriveController,
        extended_availability_zone.ExtendedAZController,
        extended_server_attributes.ExtendedServerAttributesController,
        extended_status.ExtendedStatusController,
        extended_volumes.ExtendedVolumesController,
        hide_server_addresses.Controller,
        keypairs.Controller,
        security_groups.SecurityGroupsOutputController,
        server_usage.ServerUsageController,
    ],
    [
        admin_actions.AdminActionsController,
        admin_password.AdminPasswordController,
        console_output.ConsoleOutputController,
        create_backup.CreateBackupController,
        deferred_delete.DeferredDeleteController,
        evacuate.EvacuateController,
        floating_ips.FloatingIPActionController,
        lock_server.LockServerController,
        migrate_server.MigrateServerController,
        multinic.MultinicController,
        pause_server.PauseServerController,
        remote_consoles.RemoteConsolesController,
        rescue.RescueController,
        security_groups.SecurityGroupActionController,
        shelve.ShelveController,
        suspend_server.SuspendServerController
    ]
)


server_metadata_controller = functools.partial(_create_controller,
    server_metadata.ServerMetadataController, [], [])

# NOTE(alex_xu): This is structure of this route list as below:
# (
#     ('Route path': {
#         'HTTP method: [
#             'Controller',
#             'The method of controller is used to handle this route'
#         ],
#         ...
#     }),
#     ...
# )
#
# Also note that this is ordered tuple. For example, the '/servers/detail'
# should be in the front of '/servers/{id}', otherwise the request to
# '/servers/detail' always matches to '/servers/{id}' as the id is 'detail'.
ROUTE_LIST = (
    # NOTE: '/os-volumes_boot' is a clone of '/servers'. We may want to
    # deprecate it in the future.
    ('/flavors', {
        'GET': [flavor_controller, 'index'],
        'POST': [flavor_controller, 'create']
    }),
    ('/flavors/detail', {
        'GET': [flavor_controller, 'detail']
    }),
    ('/flavors/{id}', {
        'GET': [flavor_controller, 'show'],
        'DELETE': [flavor_controller, 'delete']
    }),
    ('/flavors/{id}/action', {
        'POST': [flavor_controller, 'action']
    }),
    ('/flavors/{flavor_id}/os-extra_specs', {
        'GET': [flavor_extraspec_controller, 'index'],
        'POST': [flavor_extraspec_controller, 'create']
    }),
    ('/flavors/{flavor_id}/os-extra_specs/{id}', {
        'GET': [flavor_extraspec_controller, 'show'],
        'PUT': [flavor_extraspec_controller, 'update'],
        'DELETE': [flavor_extraspec_controller, 'delete']
    }),
    ('/flavors/{flavor_id}/os-flavor-access', {
        'GET': [flavor_access_controller, 'index']
    }),
    ('/os-aggregates', {
        'GET': [aggregates_controller, 'index'],
        'POST': [aggregates_controller, 'create']
    }),
    ('/os-aggregates/{id}', {
        'GET': [aggregates_controller, 'show'],
        'PUT': [aggregates_controller, 'update'],
        'DELETE': [aggregates_controller, 'delete']
    }),
    ('/os-aggregates/{id}/action', {
        'POST': [aggregates_controller, 'action'],
    }),
    ('/os-floating-ips', {
        'GET': [floating_ips_controller, 'index'],
        'POST': [floating_ips_controller, 'create']
    }),
    ('/os-floating-ips/{id}', {
        'GET': [floating_ips_controller, 'show'],
        'DELETE': [floating_ips_controller, 'delete']
    }),
    ('/os-keypairs', {
        'GET': [keypairs_controller, 'index'],
        'POST': [keypairs_controller, 'create']
    }),
    ('/os-keypairs/{id}', {
        'GET': [keypairs_controller, 'show'],
        'DELETE': [keypairs_controller, 'delete']
    }),
    ('/os-volumes_boot', {
        'GET': [server_controller, 'index'],
        'POST': [server_controller, 'create']
    }),
    ('/os-volumes_boot/detail', {
        'GET': [server_controller, 'detail']
    }),
    ('/os-volumes_boot/{id}', {
        'GET': [server_controller, 'show'],
        'PUT': [server_controller, 'update'],
        'DELETE': [server_controller, 'delete']
    }),
    ('/os-volumes_boot/{id}/action', {
        'POST': [server_controller, 'action']
    }),
    ('/servers', {
        'GET': [server_controller, 'index'],
        'POST': [server_controller, 'create']
    }),
    ('/servers/detail', {
        'GET': [server_controller, 'detail']
    }),
    ('/servers/{id}', {
        'GET': [server_controller, 'show'],
        'PUT': [server_controller, 'update'],
        'DELETE': [server_controller, 'delete']
    }),
    ('/servers/{id}/action', {
        'POST': [server_controller, 'action']
    }),
    ('/servers/{server_id}/metadata', {
        'GET': [server_metadata_controller, 'index'],
        'POST': [server_metadata_controller, 'create'],
        'PUT': [server_metadata_controller, 'update_all'],
    }),
    ('/servers/{server_id}/metadata/{id}', {
        'GET': [server_metadata_controller, 'show'],
        'PUT': [server_metadata_controller, 'update'],
        'DELETE': [server_metadata_controller, 'delete'],
    }),
)


class APIRouterV21(nova.api.openstack.APIRouterV21):
    """Routes requests on the OpenStack API to the appropriate controller
    and method. The URL mapping based on the plain list `ROUTE_LIST` is built
    at here. The stevedore based API loading will be replaced by this.
    """
    def __init__(self):
        self._loaded_extension_info = extension_info.LoadedExtensionInfo()
        super(APIRouterV21, self).__init__()

        for path, methods in ROUTE_LIST:
            for method, controller_info in methods.items():
                # TODO(alex_xu): In the end, I want to create single controller
                # instance instead of create controller instance for each
                # route.
                controller = controller_info[0]()
                action = controller_info[1]
                self.map.create_route(path, method, controller, action)

    def _register_extension(self, ext):
        return self.loaded_extension_info.register_extension(ext.obj)

    @property
    def loaded_extension_info(self):
        return self._loaded_extension_info
