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
""" Load testing dependencies onto sys.path via ms.version """
import ms.version

ms.version.addpkg('setuptools', '0.6c11')
ms.version.addpkg('coverage', '3.6')
ms.version.addpkg('argparse', '1.2.1')
ms.version.addpkg('nose', '1.1.2')
ms.version.addpkg('lxml', '2.3.2')
ms.version.addpkg('ipaddr', '2.1.9')
ms.version.addpkg('dateutil', '1.5')
ms.version.addpkg('unittest2', '0.5.1-ms1')
