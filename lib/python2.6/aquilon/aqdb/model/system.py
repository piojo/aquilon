# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
""" DnsRecords are higher level constructs which can provide services """
from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.exceptions_ import InternalError, ArgumentError
from aquilon.aqdb.model import Base, DnsDomain, Network, DnsRecord
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.column_types import AqStr, IPV4

#TODO: enum type for system_type column
#_sys_types = ['host', 'switch', 'console_switch', 'chassis', 'manager',
#              'auxiliary' ]


class FutureARecord(DnsRecord):
    """FutureARecord is a placeholder to let us add name/IP addresses now.

    This will be done differently after the DNS revamp.

    """
    __tablename__ = 'future_a_record'
    __mapper_args__ = {'polymorphic_identity': 'future_a_record'}
    _class_label = 'DNS Record'

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                           name='FUTURE_A_RECORD_SYSTEM_FK',
                                           ondelete='CASCADE'),
                       primary_key=True)

    ip = Column(IPV4, nullable=False)

    # ON DELETE SET NULL and later passive_deletes=True helps refresh_network in
    # case of network splits/merges
    network_id = Column(Integer, ForeignKey('network.id',
                                            name='FUTURE_A_RECORD_NET_ID_FK',
                                            ondelete="SET NULL"),
                        nullable=True)

    network = relation(Network, backref=backref('interfaces',
                                                passive_deletes=True))

    def __format__(self, format_spec):
        if format_spec != "a":
            return super(FutureARecord, self).__format__(format_spec)
        return "%s [%s]" % (self.fqdn, self.ip)


farecord = FutureARecord.__table__  # pylint: disable-msg=C0103, E1101
farecord.primary_key.name = 'future_a_record_pk'
# TODO: remove this constraint
farecord.append_constraint(UniqueConstraint('ip', name='future_a_record_ip_uk'))

farecord.info['unique_fields'] = ['name', 'dns_domain']
farecord.info['extra_search_fields'] = ['ip']


class DynamicStub(FutureARecord):
    """
        DynamicStub is a hack to handle stand alone dns records for dynamic
        hosts prior to having a properly reworked set of tables for Dns
        information. It should not be used by anything other than to create host
        records for virtual machines using names similar to
        'dynamic-1-2-3-4.subdomain.ms.com'
    """
    __tablename__ = 'dynamic_stub'
    __mapper_args__ = {'polymorphic_identity': 'dynamic_stub'}
    _class_label = 'Dynamic Stub'

    dns_record_id = Column(Integer, ForeignKey('future_a_record.dns_record_id',
                                           name='dynamic_stub_farecord_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)


DynamicStub.__table__.primary_key.name = 'dynamic_stub_pk'


class ReservedName(DnsRecord):
    """
        ReservedName is a placeholder for a name that does not have an IP
        address.
    """

    __tablename__ = 'reserved_name'
    __mapper_args__ = {'polymorphic_identity': 'reserved_name'}
    _class_label = 'Reserved Name'

    dns_record_id = Column(Integer, ForeignKey('dns_record.id',
                                           name='reserved_name_dns_record_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    def __init__(self, **kwargs):
        if "ip" in kwargs and kwargs["ip"]:  # pragma: no cover
            raise ArgumentError("Reserved names must not have an IP address.")
        return super(ReservedName, self).__init__(**kwargs)


resname = ReservedName.__table__  # pylint: disable-msg=C0103, E1101
resname.primary_key.name = 'reserved_name_pk'
resname.info['unique_fields'] = ['name', 'dns_domain']
