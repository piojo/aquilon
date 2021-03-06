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
""" Disk for share """

import re

from sqlalchemy import Column, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relation, backref, column_property, validates
from sqlalchemy.sql import select, func

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Disk, Share, Filesystem

address_re = re.compile(r"\d+:\d+$")
_TN = 'disk'


class VirtualDisk(Disk):
    # We need to know the bus address of each disk.
    # This isn't really nullable, but single-table inheritance means
    # that the base class will end up with the column and the base class
    # wants it to be nullable. We enforce this via __init__ instead.
    address = Column(AqStr(128), nullable=True)

    snapshotable = Column(Boolean(name="%s_snapshotable_ck" % _TN),
                          nullable=True)

    @validates('address')
    def validate_address(self, key, value):  # pylint: disable=W0613
        if not address_re.match(value):
            raise ArgumentError(r"Disk address '%s' is not valid, it must "
                                r"match \d+:\d+ (e.g. 0:0)." % value)
        return value

    def __init__(self, **kw):
        if 'address' not in kw or kw['address'] is None:
            raise ValueError("Address is mandatory for virtual disks.")
        super(VirtualDisk, self).__init__(**kw)


class VirtualNasDisk(VirtualDisk):
    share_id = Column(Integer, ForeignKey('share.id', name='%s_share_fk' % _TN,
                                          ondelete='CASCADE'),
                      nullable=True)

    share = relation(Share, innerjoin=True,
                     backref=backref('disks', cascade='all'))

    __extra_table_args__ = (Index('%s_share_idx' % _TN, share_id),)
    __mapper_args__ = {'polymorphic_identity': 'virtual_disk'}

    def __repr__(self):
        return "<%s %s (%s) of machine %s, %d GB, provided by %s>" % \
            (self._get_class_label(), self.device_name,
             self.controller_type, self.machine.label, self.capacity,
             (self.share.name if self.share else "no_share"))

# The formatter code is interested in the count of disks/machines, and it is
# cheaper to query the DB than to load all entities into memory
Share.disk_count = column_property(
    select([func.count()],
           VirtualNasDisk.share_id == Share.id)
    .label("disk_count"), deferred=True)

Share.machine_count = column_property(
    select([func.count(func.distinct(VirtualNasDisk.machine_id))],
           VirtualNasDisk.share_id == Share.id)
    .label("machine_count"), deferred=True)


class VirtualLocalDisk(VirtualDisk):
    filesystem_id = Column(Integer, ForeignKey('filesystem.id',
                                               name='%s_filesystem_fk' % _TN,
                                               ondelete='CASCADE'),
                           nullable=True)

    filesystem = relation(Filesystem, innerjoin=True,
                          backref=backref('disks', cascade='all'))

    __extra_table_args__ = (Index('%s_filesystem_idx' % _TN, filesystem_id),)
    __mapper_args__ = {'polymorphic_identity': 'virtual_localdisk'}

    def __repr__(self):
        return "<%s %s (%s) of machine %s, %d GB, provided by %s>" % \
            (self._get_class_label(), self.device_name,
             self.controller_type, self.machine.label, self.capacity,
             (self.filesystem.name if self.filesystem else "no_filesystem"))

Filesystem.virtual_disk_count = column_property(
    select([func.count()],
           VirtualLocalDisk.filesystem_id == Filesystem.id)
    .label("virtual_disk_count"), deferred=True)
