#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the update personality command."""


import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestUpdatePersonality(TestBrokerCommand):

    def testinvalidfunction(self):
        """ Verify that the list of built-in functions is restricted """
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "locals()"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name 'locals' is not defined", command)

    def testinvalidtype(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "memory - 100"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The function should return a dictonary.", command)

    def testinvaliddict(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': 'bar'}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The function should return a dictionary with all "
                         "keys being strings, and all values being numbers.",
                         command)

    def testmissingmemory(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'foo': 5}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The memory constraint is missing from the returned "
                         "dictionary.", command)

    def testnotenoughmemory(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': memory / 4}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Validation failed for the following clusters:",
                         command)
        self.matchoutput(out,
                         "ESX Cluster utecl1 is over capacity regarding memory",
                         command)

    def testupdatecapacity(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_capacity_function", "{'memory': (memory - 1500) * 0.94}"]
        self.noouttest(command)

    def testupdateovercommit(self):
        command = ["update_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster",
                   "--vmhost_overcommit_memory", 1.04]
        self.noouttest(command)

    def testverifyupdatecapacity(self):
        command = ["show_personality", "--personality", "vulcan-1g-desktop-prod",
                   "--archetype", "esx_cluster"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "VM host capacity function: {'memory': (memory - 1500) * 0.94}",
                         command)
        self.matchoutput(out, "VM host overcommit factor: 1.04", command)

    def testupdateclusterrequirement(self):
        command = ["update_personality", "--personality=vulcan-1g-desktop-prod",
                   "--archetype=esx_cluster",
                   "--cluster"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The personality vulcan-1g-desktop-prod is in use", command)

        command = ["add_personality", "--archetype=aquilon", "--grn=grn:/ms/ei/aquilon/aqd",
                   "--personality=unused", "--host_environment=infra"]
        self.successtest(command)

        command = ["update_personality", "--personality", "unused",
                   "--archetype=aquilon", "--cluster"]
        out = self.successtest(command)

        command = ["del_personality", "--personality", "unused",
                   "--archetype=aquilon"]
        out = self.successtest(command)

    def testupdateconfigoverride01(self):

        command = ["add_personality", "--archetype=aquilon", "--grn=grn:/ms/ei/aquilon/aqd",
                   "--personality=testovrpersona/dev", "--host_environment=dev"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "override", command)

        command = ["cat", "--archetype=aquilon", "--personality=testovrpersona/dev"]
        out = self.commandtest(command)
        self.matchclean(out, 'override', command)

    def testupdateconfigoverride02(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--config_override"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Config override: enabled", command)

        command = ["cat", "--archetype=aquilon", "--personality=testovrpersona/dev"]
        out = self.commandtest(command)
        self.matchoutput(out, 'include { "features/personality/config_override/config" }',
                         command)

    def testupdateconfigoverride03(self):
        command = ["update_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon", "--noconfig_override"]
        self.successtest(command)

        command = ["show_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchclean(out, "override", command)

        command = ["cat", "--archetype=aquilon", "--personality=testovrpersona/dev"]
        self.matchclean(out, 'override', command)

    def testupdateconfigoverride04(self):
        command = ["del_personality", "--personality=testovrpersona/dev",
                   "--archetype=aquilon"]
        out = self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
