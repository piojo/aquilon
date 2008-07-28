#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del service`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.service import get_service
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.sy.host_list import HostList
from aquilon.aqdb.svc.service_map import ServiceMap
from aquilon.server.templates import (PlenaryService, PlenaryServiceInstance)


class CommandDelService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    def render(self, session, service, instance, **arguments):
        # This should fail nicely if the service is required for an archetype.
        dbservice = get_service(session, service)
        if not instance:
            if dbservice.instances:
                raise ArgumentError("Cannot remove service with instances defined.")
            plenary_info = PlenaryService(dbservice)
            plenary_info.remove
            session.delete(dbservice)
            return
        try:
            dbhl = session.query(HostList).filter_by(name=instance).one()
        except InvalidRequestError, e:
            raise NotFoundException(
                    "Could not find instance %s: %s"
                    % (instance, e))
        dbsi = session.query(ServiceInstance).filter_by(
                host_list=dbhl, service=dbservice).first()

        if dbsi:
            if dbsi.client_count > 0:
                raise ArgumentError("instance has clients and cannot be deleted.")

            # Check the service map and remove any mappings
            for dbmap in session.query(ServiceMap).filter_by(service_instance=dbsi).all():
                session.delete(dbmap)

            plenary_info = PlenaryServiceInstance(dbservice, dbsi)
            plenary_info.remove
            session.delete(dbsi)
            session.flush()
            session.refresh(dbservice)
            
        # FIXME: Cascade to relevant objects...
        return


#if __name__=='__main__':
