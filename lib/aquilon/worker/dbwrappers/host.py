# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Wrappers to make getting and using hosts simpler."""

from sqlalchemy.orm import joinedload

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.aqdb.model import (HardwareEntity, DnsEnvironment, DnsDomain,
                                DnsRecord)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from collections import defaultdict
from types import ListType


def hostname_to_host(session, hostname):
    # When the user asked for a host, returning "machine not found" does not
    # feel to be the right error message, even if it is technically correct.
    # It's a little tricky though: we don't want to suppress "dns domain not
    # found"
    parse_fqdn(session, hostname)
    try:
        dbmachine = HardwareEntity.get_unique(session, hostname, compel=True)
    except NotFoundException:
        raise NotFoundException("Host %s not found." % hostname)

    if not dbmachine.host:
        raise NotFoundException("{0} does not have a host "
                                "assigned.".format(dbmachine))
    return dbmachine.host


def hostlist_to_hosts(session, hostlist):
    dbdns_env = DnsEnvironment.get_unique_or_default(session)
    failed = []
    dbhosts = []
    dns_domains = {}
    for host in hostlist:
        if "." not in host:
            failed.append("%s: Not an FQDN." % host)
            continue
        short, dns_domain = host.split(".", 1)
        try:
            if dns_domain not in dns_domains:
                dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                    compel=True)

                dns_domains[dns_domain] = dbdns_domain

            dbdns_rec = DnsRecord.get_unique(session, name=short,
                                             dns_domain=dns_domains[dns_domain],
                                             dns_environment=dbdns_env,
                                             query_options=[joinedload('hardware_entity')],
                                             compel=True)
            if not dbdns_rec.hardware_entity or \
               not dbdns_rec.hardware_entity.host:
                raise NotFoundException("Host %s not found." % host)
            dbhosts.append(dbdns_rec.hardware_entity.host)

        except NotFoundException, err:
            failed.append("%s: %s" % (host, err))
            continue
        except ArgumentError, err:
            failed.append("%s: %s" % (host, err))
            continue

    if failed:
        raise ArgumentError("Invalid hosts in list:\n%s" %
                            "\n".join(failed))

    if not dbhosts:
        raise ArgumentError("Empty list.")
    return dbhosts


def get_host_bound_service(dbhost, dbservice):
    for si in dbhost.services_used:
        if si.service == dbservice:
            return si
    return None


def check_hostlist_size(command, config, hostlist):

    if not hostlist:
        return

    default_max_size = config.getint("broker", "default_max_list_size")
    max_size_opt = "%s_max_list_size" % command
    if config.has_option("broker", max_size_opt):
        if config.get("broker", max_size_opt) != '':
            hostlist_max_size = config.getint("broker", max_size_opt)
        else:
            hostlist_max_size = 0
    else:
        hostlist_max_size = default_max_size

    if not hostlist_max_size:
        return

    if len(hostlist) > hostlist_max_size:
        raise ArgumentError("The number of hosts in list {0:d} can not be "
                            "more than {1:d}".format(len(hostlist), hostlist_max_size))
    return


def validate_branch_author(dbhosts):
    branches = defaultdict(ListType)
    authors = defaultdict(ListType)
    for dbhost in dbhosts:
        branches[dbhost.branch].append(dbhost)
        authors[dbhost.sandbox_author].append(dbhost)

    if len(branches) > 1:
        keys = branches.keys()
        branch_sort = lambda x, y: cmp(len(branches[x]), len(branches[y]))
        keys.sort(cmp=branch_sort)
        stats = ["{0:d} hosts in {1:l}".format(len(branches[branch]), branch)
                 for branch in keys]
        raise ArgumentError("All hosts must be in the same domain or "
                            "sandbox:\n%s" % "\n".join(stats))
    if len(authors) > 1:
        keys = authors.keys()
        author_sort = lambda x, y: cmp(len(authors[x]), len(authors[y]))
        keys.sort(cmp=author_sort)
        stats = ["%s hosts with sandbox author %s" %
                 (len(authors[author]), author.name) for author in keys]
        raise ArgumentError("All hosts must be managed by the same "
                            "sandbox author:\n%s" % "\n".join(stats))

    return (branches.popitem()[0], authors.popitem()[0])
