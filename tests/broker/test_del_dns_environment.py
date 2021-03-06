#!/usr/bin/env python
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
"""Module for testing the del dns environment command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelDnsEnvironment(TestBrokerCommand):

    def testdelutenv(self):
        command = ["del", "dns", "environment", "--dns_environment", "ut-env"]
        self.noouttest(command)

    def testdelnonexistant(self):
        command = ["del", "dns", "environment", "--dns_environment", "no-such-env"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Environment no-such-env not found.", command)

    def testdelinternal(self):
        command = ["del", "dns", "environment", "--dns_environment", "internal"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Environment internal is the default DNS "
                         "environment, therefore it cannot be deleted.",
                         command)

    def testshowutenv(self):
        command = ["show", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Environment ut-env not found.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDnsEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
