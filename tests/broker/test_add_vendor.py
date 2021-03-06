#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the add vendor command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddVendor(TestBrokerCommand):

    def testaddexisting(self):
        command = "add vendor --vendor intel"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Vendor intel already exists", command)

    def testaddbadname(self):
        command = "add vendor --vendor oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --vendor.",
                         command)

    def testaddutvendor(self):
        command = ["add", "vendor", "--vendor", "utvendor",
                   "--comments", "Some vendor comments"]
        self.noouttest(command)

    def testverifyutvendor(self):
        command = "show vendor --vendor utvendor"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor", command)
        self.matchoutput(out, "Comments: Some vendor comments", command)

    def testverifyutvendorall(self):
        command = "show vendor --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Vendor: utvendor", command)
        self.matchoutput(out, "Vendor: intel", command)

    def testnotfoundvendor(self):
        command = "show vendor --vendor vendor-does-not-exist"
        self.notfoundtest(command.split(" "))

    def testaddutvirt(self):
        command = ["add", "vendor", "--vendor", "utvirt"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddVendor)
    unittest.TextTestRunner(verbosity=2).run(suite)
