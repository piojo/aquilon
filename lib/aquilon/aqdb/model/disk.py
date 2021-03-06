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
""" Polymorphic representation of disks which may be local or san """

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, Machine
from aquilon.aqdb.column_types import AqStr, Enum

# FIXME: this list should not be hardcoded here
controller_types = ['cciss', 'ide', 'sas', 'sata', 'scsi', 'flash',
                    'fibrechannel']

_TN = 'disk'


class Disk(Base):
    """
        Base Class for polymorphic representation of disk or disk-like resources
    """
    __tablename__ = _TN
    _instance_label = 'device_name'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    disk_type = Column(String(64), nullable=False)
    capacity = Column(Integer, nullable=False)
    device_name = Column(AqStr(128), nullable=False, default='sda')
    controller_type = Column(Enum(64, controller_types), nullable=False)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='disk_machine_fk',
                                            ondelete='CASCADE'),
                        nullable=False)

    bootable = Column(Boolean(name="%s_bootable_ck" % _TN), nullable=False,
                      default=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    machine = relation(Machine, innerjoin=True,
                       backref=backref('disks', cascade='all'))

    __table_args__ = (UniqueConstraint(machine_id, device_name,
                                       name='disk_mach_dev_name_uk'),)
    __mapper_args__ = {'polymorphic_on': disk_type,
                       'with_polymorphic': '*'}

    def __repr__(self):
        # The default __repr__() is too long
        return "<%s %s (%s) of machine %s, %d GB>" % \
            (self._get_class_label(), self.device_name, self.controller_type,
             self.machine.label, self.capacity)

disk = Disk.__table__  # pylint: disable=C0103
disk.info['unique_fields'] = ['machine', 'device_name']


class LocalDisk(Disk):
    __mapper_args__ = {'polymorphic_identity': 'local'}
