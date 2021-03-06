# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2013  Contributor
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
""" Maps service instances to locations. See class.__doc__ """

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import (Base, Location, Personality, Archetype,
                                ServiceInstance)

_TN  = 'personality_service_map'
_ABV = 'prsnlty_svc_map'

class PersonalityServiceMap(Base):
    """ Personality Service Map: mapping a service_instance to a location,
        qualified by a personality.The rows in this table assert that an
        instance is a valid useable default that clients of the given
        personality can choose as their provider during service
        autoconfiguration. """

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)

    service_instance_id = Column(Integer, ForeignKey('service_instance.id',
                                                name='%s_svc_inst_fk'%(_ABV)),
                          nullable=False)

    location_id = Column(Integer, ForeignKey('location.id',
                                                ondelete='CASCADE',
                                                name='%s_loc_fk'%(_ABV)),
                            nullable=False)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                  name='personality',
                                                  ondelete='CASCADE'),
                            nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now, nullable=False))
    comments = deferred(Column(String(255), nullable=True))

    location = relation(Location, backref='personality_service_maps')
    service_instance = relation(ServiceInstance, backref='personality_service_map')
    personality = relation(Personality, backref='maps', uselist=False)

    #Archetype probably shouldn't be exposed at this table/object: This isn't
    #intended for use with Archetype, but I'm not 100% sure yet
    #def _archetype(self):
    #    return self.personality.archetype
    #archetype = property(_archetype)

    def _service(self):
        return self.service_instance.service
    service = property(_service)

    def __repr__(self):
        return '<Personality Service Map %s for %s at %s %s >'%(
            self.service_instance.service, self.personality,
            self.location.location_type, self.location.name)

personality_service_map = PersonalityServiceMap.__table__
table = personality_service_map

personality_service_map.primary_key.name='prsnlty_svc_map_pk'

#TODO: reconsider the surrogate primary key?
personality_service_map.append_constraint(
    UniqueConstraint('personality_id', 'service_instance_id', 'location_id',
                     name='%s_loc_inst_uk'%(_ABV)))




