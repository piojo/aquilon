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
"""Module for testing the del disk command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelDisk(TestBrokerCommand):

    def test_100_del_ut3c1n3_sda(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3",
                        "--controller", "sata", "--size", "50"])

    def test_101_del_ut3c1n3_c0d0(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3",
                        "--disk", "c0d1"])

    def test_200_show_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Disk: sda 68 GB scsi", command)
        self.matchclean(out, "Disk: c0d1", command)

    # This should now list the 34 GB disk that was added previously...
    def test_200_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "harddisks", command)

    def test_300_del_unknown_controller(self):
        command = ["del", "disk", "--machine", "ut3c1n3",
                   "--controller", "controller-does-not-exist"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "controller-does-not-exist is not a valid controller type",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
