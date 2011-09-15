# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
"""Contains the logic for `aq map grn`."""

from aquilon.aqdb.model import Grn, Host, Personality
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandMapGrn(BrokerCommand):

    def _update_dbobj(self, obj, grn):
        if grn in obj.grns:
            # TODO: should we throw an error here?
            return
        obj.grns.append(grn)

    def render(self, session, logger, grn, eon_id, hostname, list, personality,
               archetype, **arguments):
        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config)

        if hostname:
            objs = [hostname_to_host(session, hostname)]
        elif list:
            objs = []
            failed = []
            for host in list.splitlines():
                host = host.strip()
                if not host or host.startswith('#'):
                    continue
                try:
                    objs.append(hostname_to_host(session, host))
                except NotFoundException, nfe:
                    failed.append("%s: %s" % (host, nfe))
                except ArgumentError, ae:
                    failed.append("%s: %s" % (host, ae))
            if failed:
                raise ArgumentError("Invalid hosts in list:\n%s" %
                                    "\n".join(failed))
            if not objs:
                raise ArgumentError("Empty list.")
        elif personality:
            objs = [Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)]

        for obj in objs:
            self._update_dbobj(obj, dbgrn)

        session.flush()
        return