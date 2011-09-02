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
"""Wrappers to make getting and using systems simpler."""


from aquilon.exceptions_ import (ArgumentError, IncompleteError,
                                 NotFoundException)
from aquilon.aqdb.model import (Resource, Cluster, Host,
                                ClusterResource, HostResource)
from aquilon.worker.templates.resource import PlenaryResource
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.locks import lock_queue, CompileKey


def get_resource_holder(session, hostname, cluster, compel=True):
    who = None
    if hostname is not None:
        dbhost = hostname_to_host(session, hostname)
        who = dbhost.resholder
        if who is None:
            if compel:
                raise NotFoundException("host %s has no resources" %
                                        dbhost.fqdn)
            dbhost.resholder = HostResource(host=dbhost)
            session.add(dbhost.resholder)
            session.flush()
            who = dbhost.resholder

    if cluster is not None:
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        who = dbcluster.resholder
        label = "cluster %s" % dbcluster.name
        if who is None:
            if compel:
                raise NotFoundException("cluster %s has no resources" %
                                    dbcluster.name)
            dbcluster.resholder = ClusterResource(cluster=dbcluster)
            session.add(dbcluster.resholder)
            session.flush()
            who = dbcluster.resholder

    return who

def del_resource(session, logger, dbresource):
    if dbresource.holder.holder_type == 'host':
        holder_plenary = PlenaryHost(dbresource.holder.host)
        domain = dbresource.holder.host.branch.name
    if dbresource.holder.holder_type == 'cluster':
        holder_plenary = PlenaryCluster(dbresource.holder.cluster)
        domain = dbresource.holder.cluster.branch.name
    plenary = PlenaryResource(dbresource, logger=logger)

    session.delete(dbresource)
    session.flush()

    key = CompileKey.merge([plenary.get_remove_key(),
                            holder_plenary.get_write_key()])
    try:
        lock_queue.acquire(key)
        plenary.stash()
        plenary.remove(locked=True)
        try:
            holder_plenary.write(locked=True)
        except IncompleteError, e:
            holder_plenary.cleanup(domain, locked=True)
    except:
        holder_plenary.restore_stash()
        plenary.restore_stash()
        raise
    finally:
        lock_queue.release(key)

    return

def add_resource(session, logger, holder, dbresource, **args):
    dbresource.holder = holder
    session.add(dbresource)
    session.flush()
    session.refresh(dbresource)
    res_plenary = PlenaryResource(dbresource, logger=logger)

    if holder.holder_type == 'host':
        holder_plenary = PlenaryHost(holder.host)
        domain = holder.host.branch.name
    if holder.holder_type == 'cluster':
        holder_plenary = PlenaryCluster(holder.cluster)
        domain = holder.cluster.branch.name

    key = CompileKey.merge([res_plenary.get_write_key(),
                            holder_plenary.get_write_key()])
    try:
        lock_queue.acquire(key)
        res_plenary.write(locked=True)
        try:
            holder_plenary.write(locked=True)
        except IncompleteError, e:
            holder_plenary.cleanup(domain, locked=True)
    except:
        res_plenary.restore_stash()
        holder_plenary.restore_stash()
        raise
    finally:
        lock_queue.release(key)

    return


