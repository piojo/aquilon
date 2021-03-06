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
""" Hub is a group of continents.
    Got that straight? A GROUP OF CONTINENTS.

    We are declaring what hubs are for Aquilon.
    It's no good arguing along the lines of "but, I think it means X,
    therefore your implementation isn't right". It doesn't mean X.
    We'll ensure that all meanings are described as much as possible.
    That's not complete yet. It doesn't change the fact that in Aquilon,
    it doesn't mean X.

    Move along.

    Nothing to see here.

    Really."""

from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location, Company


class Hub(Location):
    """ Hub is a subtype of location """
    __tablename__ = 'hub'
    __mapper_args__ = {'polymorphic_identity': 'hub'}

    valid_parents = [Company]

    id = Column(Integer, ForeignKey('location.id',
                                    name='hub_loc_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

hub = Hub.__table__  # pylint: disable=C0103
hub.info['unique_fields'] = ['name']
