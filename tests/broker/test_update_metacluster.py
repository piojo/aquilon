#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013,2014  Contributor
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
"""Module for testing the update metacluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestUpdateMetaCluster(TestBrokerCommand, PersonalityTestMixin):

    def test_000_add_personalities(self):
        self.create_personality("metacluster", "metacluster-test",
                                grn="grn:/ms/ei/aquilon/aqd")
    def test_100_updatenoop(self):
        default_max = self.config.get("archetype_metacluster",
                                      "max_members_default")
        self.noouttest(["update_metacluster", "--metacluster=utmc1",
                        "--max_members=%s" % default_max])

    def test_100_verifynoop(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        default_max = self.config.get("archetype_metacluster",
                                      "max_members_default")
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Max members: %s" % default_max, command)
        self.matchclean(out, "Comments", command)

    def test_100_updateutmc2(self):
        command = ["update_metacluster", "--metacluster=utmc2",
                   "--max_members=98",
                   "--comments", "MetaCluster with a new comment"]
        self.noouttest(command)

    def test_100_verifyutmc2(self):
        command = "show metacluster --metacluster utmc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc2", command)
        self.matchoutput(out, "Max members: 98", command)
        self.matchoutput(out, "Comments: MetaCluster with a new comment",
                         command)

    def test_100_failmetaclustermissing(self):
        command = "update metacluster --metacluster metacluster-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Metacluster metacluster-does-not-exist not found",
                         command)

    def test_100_failreducemaxmembers(self):
        command = ["update_metacluster", "--metacluster=utmc3",
                   "--max_members=-1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc3 has 0 clusters bound, "
                         "which exceeds the requested limit of -1.",
                         command)

    def test_100_failhabuilding(self):
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--high_availability"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc1 is over capacity regarding memory",
                         command)
        self.matchoutput(out, "but the limit is 0.", command)

    def test_100_ha(self):
        command = ["update_metacluster", "--metacluster", "utmc5",
                   "--high_availability"]
        self.noouttest(command)

    def test_100_failhacapacity(self):
        command = ["update_metacluster", "--metacluster", "utmc6",
                   "--high_availability"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Metacluster utmc6 is over capacity regarding memory",
                         command)

    def test_100_verifyutmc5(self):
        command = ["show", "metacluster", "--metacluster", "utmc5"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "Capacity limits: memory: 225590", command)
        self.matchoutput(out, "Resources used by VMs: memory: 106496", command)
        self.matchoutput(out, "High availability enabled: True", command)

    def test_100_verifyutmc6(self):
        command = ["show", "metacluster", "--metacluster", "utmc6"]
        (out, err) = self.successtest(command)
        self.matchoutput(out, "Capacity limits: memory: 451180", command)
        self.matchoutput(out, "Resources used by VMs: memory: 425984", command)
        self.matchoutput(out, "High availability enabled: False", command)

    # FIXME: Need tests for plenary templates

    def test_100_updatelocation(self):
        # moving cluster from bu: ut to city ny, a parent of it.
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--city", "ny"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "City: ny", command)

        # reverting this move
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--fix_location"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building: ut", command)

    def test_100_updatepersonality(self):
        # Change metacluster personality and revert it.
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--personality", "metacluster-test"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: metacluster-test", command)

        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--personality", "metacluster"]
        self.noouttest(command)

        command = ["show", "metacluster", "--metacluster", "utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: metacluster", command)

    def test_100_failupdatelocation(self):
        command = ["update_metacluster", "--metacluster", "utmc1",
                   "--building", "cards"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Building cards is not within a campus.", command)
        self.matchoutput(out, "ESX Cluster utecl1 has location Building ut.",
                         command)
        self.matchoutput(out, "ESX Cluster utecl2 has location Building ut.",
                         command)

    def test_800_cleanup(self):
        self.drop_personality("metacluster", "metacluster-test")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
