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
"""Filesystem Resource formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import Filesystem


class FilesystemFormatter(ResourceFormatter):
    def extra_details(self, fs, indent=""):
        details = []
        details.append(indent + "  Block Device: %s" % fs.blockdev)
        details.append(indent + "  FSType: %s" % fs.fstype)
        details.append(indent + "  Mount at boot: %s" % fs.mount)
        details.append(indent + "  Mountopts: %s" % fs.mountoptions)
        details.append(indent + "  Mountpoint: %s" % fs.mountpoint)
        details.append(indent + "  Dump Freq: %d" % fs.dumpfreq)
        details.append(indent + "  Fsck Pass: %d" % fs.passno)
        details.append(indent + "  Virtual Disk Count: %d" % fs.virtual_disk_count)
        return details

    def format_proto(self, fs, container):
        skeleton = container.resources.add()
        self.add_resource_data(skeleton, fs)
        skeleton.fsdata.mount = fs.mount
        skeleton.fsdata.fstype = str(fs.fstype)
        skeleton.fsdata.blockdevice = str(fs.blockdev)
        skeleton.fsdata.mountpoint = str(fs.mountpoint)
        skeleton.fsdata.opts = str(fs.mountoptions)
        skeleton.fsdata.freq = fs.dumpfreq
        skeleton.fsdata.passno = fs.passno

ObjectFormatter.handlers[Filesystem] = FilesystemFormatter()
