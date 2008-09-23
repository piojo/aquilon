#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq update machine --hostname`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.commands.update_machine import CommandUpdateMachine
from aquilon.server.dbwrappers.host import hostname_to_host


class CommandUpdateMachineHostname(CommandUpdateMachine):

    required_parameters = ["hostname"]

    @add_transaction
    @az_check
    def render(self, session, hostname, **arguments):
        dbhost = hostname_to_host(session, hostname)
        arguments['machine'] = dbhost.machine.name
        return CommandUpdateMachine.render(self, session=session, **arguments)


#if __name__=='__main__':