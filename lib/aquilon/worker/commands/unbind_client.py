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
"""Contains the logic for `aq unbind client`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Service
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_bound_service)
from aquilon.worker.templates import (Plenary, PlenaryCollection,
                                      PlenaryServiceInstanceServer)


class CommandUnbindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, logger, hostname, service, **arguments):
        dbhost = hostname_to_host(session, hostname)
        for srv in dbhost.archetype.services + dbhost.personality.services:
            if srv.name == service:
                raise ArgumentError("Cannot unbind a required service. "
                                    "Perhaps you want to rebind?")

        dbservice = Service.get_unique(session, service, compel=True)
        si = get_host_bound_service(dbhost, dbservice)
        if si:
            logger.info("Removing client binding")
            dbhost.services_used.remove(si)
            session.flush()

            plenaries = PlenaryCollection(logger=logger)
            plenaries.append(Plenary.get_plenary(dbhost))
            plenaries.append(PlenaryServiceInstanceServer.get_plenary(si))
            plenaries.write()

        return
