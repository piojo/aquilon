# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq add tor_switch`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.rack import get_or_create_rack
from aquilon.server.dbwrappers.interface import get_or_create_interface
from aquilon.server.dbwrappers.hardware_entity import parse_primary_name
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model import Switch, Model


class CommandAddTorSwitch(BrokerCommand):

    required_parameters = ["tor_switch", "model"]

    def render(self, session, logger, tor_switch, label, model, vendor,
               rack, building, room, rackid, rackrow, rackcolumn,
               interface, mac, ip, serial, comments, **arguments):
        logger.client_info("add_tor_switch is deprecated, please use "
                           "add_switch instead.")
        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   machine_type='switch', compel=True)

        if dbmodel.machine_type not in ['switch']:
            raise ArgumentError("The add_tor_switch command cannot add "
                                "machines of type %s.  Try 'add machine'." %
                                dbmodel.machine_type)

        if rack:
            dblocation = get_location(session, rack=rack)
        elif ((building or room) and rackid is not None and
              rackrow is not None and rackcolumn is not None):
            dblocation = get_or_create_rack(session, rackid=rackid,
                                            rackrow=rackrow,
                                            rackcolumn=rackcolumn,
                                            building=building, room=room,
                                            comments="Created for tor_switch "
                                                     "%s" % tor_switch)
        else:
            raise ArgumentError("Need to specify an existing --rack or "
                                "provide --rackid, --rackrow and --rackcolumn "
                                "along with --building or --room.")

        dbdns_rec = parse_primary_name(session, tor_switch, ip)
        if not label:
            label = dbdns_rec.name

        dbtor_switch = Switch(label=label, switch_type='tor',
                              location=dblocation, model=dbmodel,
                              serial_no=serial, comments=comments)
        session.add(dbtor_switch)
        dbtor_switch.primary_name = dbdns_rec

        if interface or mac:
            dbinterface = get_or_create_interface(session, dbtor_switch,
                                                  name=interface, mac=mac,
                                                  interface_type='oa')

            if ip:
                dbinterface.vlans[0].addresses.append(ip)
            session.flush()

            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.add_host(dbinterface)
            except ProcessException, e:
                raise ArgumentError("Could not add ToR switch to DSDB: %s" % e)
        return
