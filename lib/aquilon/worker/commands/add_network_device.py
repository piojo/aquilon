# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq add network_device`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import NetworkDevice, Model
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import grab_address
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.interface import (get_or_create_interface,
                                                 assign_address,
                                                 check_netdev_iftype)
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.templates import Plenary


class CommandAddNetworkDevice(BrokerCommand):

    required_parameters = ["network_device", "model", "type",
                           "ip", "interface", "iftype"]

    def render(self, session, logger, network_device, label, model, type, ip,
               interface, iftype, mac, vendor, serial, comments, **arguments):
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   compel=True)

        if not dbmodel.model_type.isNetworkDeviceType():
            raise ArgumentError("This command can only be used to "
                                "add network devices.")

        dblocation = get_location(session, compel=True, **arguments)

        dbdns_rec, newly_created = grab_address(session, network_device, ip,
                                                allow_restricted_domain=True,
                                                allow_reserved=True,
                                                preclude=True)
        if not label:
            label = dbdns_rec.fqdn.name
            try:
                NetworkDevice.check_label(label)
            except ArgumentError:
                raise ArgumentError("Could not deduce a valid hardware label "
                                    "from the network device name.  Please specify "
                                    "--label.")

        # FIXME: What do the error messages for an invalid enum (switch_type)
        # look like?
        dbnetdev = NetworkDevice(label=label, switch_type=type,
                                 location=dblocation, model=dbmodel,
                                 serial_no=serial, comments=comments)
        session.add(dbnetdev)
        dbnetdev.primary_name = dbdns_rec

        check_netdev_iftype(iftype)

        dbinterface = get_or_create_interface(session, dbnetdev,
                                              name=interface, mac=mac,
                                              interface_type=iftype)
        dbnetwork = get_net_id_from_ip(session, ip)
        # TODO: should we call check_ip_restrictions() here?
        assign_address(dbinterface, ip, dbnetwork, logger=logger)

        session.flush()

        plenary = Plenary.get_plenary(dbnetdev, logger=logger)
        with plenary.get_key():
            plenary.stash()
            try:
                plenary.write(locked=True)
                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbnetdev, None)
                dsdb_runner.commit_or_rollback("Could not add network device to DSDB")
            except:
                plenary.restore_stash()
                raise

        return
