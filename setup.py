#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
#
# This file is part of Aquilon.
#
# See the LICENSE file for all the licensing information.
#
"""Basic setup.py for packaging Aquilon itself"""

import glob
import os
import shutil
import sys
from distutils.core import setup
from subprocess import Popen, PIPE
from distutils.command.install_scripts import install_scripts
from distutils.command.build import build

VERSIONFILE = "VERSION"

# distutils won't package anything under "build".  We cheat by
# creating a symlink and referring to it during all the packaging
# process.
try:
    os.symlink("build", "bootstrap")
except OSError:
    pass

class BuildExcept(Exception):
    pass

class install_init_d_stuff(install_scripts):
    """Renames the aqd.rh init script into aqd"""
    def run(self):
        shutil.move("etc/rc.d/init.d/aqd.rh", "etc/rc.d/init.d/aqd")
        os.unlink("etc/rc.d/init.d/aqd.ms")
        install_scripts.run(self)

def get_version():
    """Returns a version for the package, based on git-describe, or in the
    VERSION file."""
    try:
        with open(VERSIONFILE) as f:
            return f.readline().strip()
    except IOError:
        with open(VERSIONFILE, "w") as f:
            p = Popen("git describe".split(), stdout=f)
            if p.wait() == 0:
                return get_version()
            else:
                raise

def find_packages(path):
    """Finds all the Python packages under path"""
    n = len(path)+1
    l = []
    for dirpath, dirnames, filenames in os.walk(path):
        for d in dirnames:
            base = dirpath[n:].replace(os.path.sep, ".")
            base = base.strip()
            if base:
                m = '.'.join([base, d])
            else:
                m = d
            l.append(m)
    return l

all_packages = find_packages("lib")
all_packages.extend(find_packages("bootstrap/bootstrap_ms"))
all_scripts = glob.glob(os.path.join("bin", "a*"))
all_scripts.extend(glob.glob(os.path.join("bootstrap", "*.py")))

setup(name="aquilon",
      version=get_version(),
      description="Aquilon",
      long_description="""Aquilon looks cool""",
      license="Apache 2.0",
      author="Quattor collaboration",
      author_email="quattor-aquilon@lists.sourceforge.net",
      package_dir={'aquilon' : 'lib/aquilon',
                   'twisted' : 'lib/twisted',
                   'ms': 'bootstrap/bootstrap_ms/ms'},
      packages=all_packages,
      cmdclass = {"install_scripts" : install_init_d_stuff},
      data_files=[("/usr/share/aquilon/etc",
                   glob.glob("etc/*.conf*") + glob.glob("etc/*xml")),
                  ("/etc/init.d", ["etc/rc.d/init.d/aqd"]),
                  ("/etc/sysconfig", ["etc/sysconfig/aqd"]),
                  ("/etc/bash_completion.d", ["aq_bash_completion.sh"]),
                  ("/usr/share/aquilon/mako/raw",
                   glob.glob("lib/aquilon/worker/formats/mako/raw/*mako")),
                  ("/usr/share/html",
                   glob.glob("lib/aquilon/worker/formats/mako/raw/*mako")),
                  ("/usr/share/doc/man/man1", glob.glob("doc/man/man1/*1")),
                  ("/usr/share/aquilon/doc/html", glob.glob("doc/html/*"))],
      scripts=all_scripts,
      url="http://quattor.org")
