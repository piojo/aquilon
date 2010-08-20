#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_capacity_function", "locals()"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name 'locals' is not defined", command)

    def testinvalidtype(self):
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_capacity_function", "memory - 100"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The function should return a dictonary.", command)

    def testinvaliddict(self):
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_capacity_function", "{'memory': 'bar'}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The function should return a dictionary with all "
                         "keys being strings, and all values being numbers.",
                         command)

    def testmissingmemory(self):
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_capacity_function", "{'foo': 5}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The memory constraint is missing from the returned "
                         "dictionary.", command)

    def testnotenoughmemory(self):
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_capacity_function", "{'memory': memory / 4}"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Validation failed for the following clusters:",
                         command)
        self.matchoutput(out,
                         "ESX Cluster utecl1 is over capacity regarding memory",
                         command)

    def testupdatecapacity(self):
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_capacity_function", "{'memory': (memory - 1500) * 0.94}"]
        self.noouttest(command)

    def testupdateovercommit(self):
        command = ["update", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost",
                   "--vmhost_overcommit_memory", 1.04]
        self.noouttest(command)

    def testverifyupdatecapacity(self):
        command = ["show", "personality", "--personality", "esx_desktop",
                   "--archetype", "vmhost"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "VM host capacity function: {'memory': (memory - 1500) * 0.94}",
                         command)
        self.matchoutput(out, "VM host overcommit factor: 1.04", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)