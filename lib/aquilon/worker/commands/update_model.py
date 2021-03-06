# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013  Contributor
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
"""Contains the logic for `aq update model`."""


from sqlalchemy.orm.session import object_session

from aquilon.aqdb.types import NicType
from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (Vendor, Model, Cpu, MachineSpecs, Machine, Disk,
                                HardwareEntity, Interface)
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandUpdateModel(BrokerCommand):

    required_parameters = ["model", "vendor"]

    # Quick hash of the arguments this method takes to the corresponding
    # aqdb label.
    argument_lookup = {'cpuname': 'name', 'cpuvendor': 'vendor',
                       'cpuspeed': 'speed', 'cpunum': 'cpu_quantity',
                       'memory': 'memory', 'disktype': 'disk_type',
                       'diskcontroller': 'controller_type',
                       'disksize': 'disk_capacity', 'nics': 'nic_count',
                       'nicmodel': 'name', 'nicvendor': 'vendor'}

    def render(self, session, logger, model, vendor, newmodel, newvendor,
               comments, leave_existing, **arguments):
        for (arg, value) in arguments.items():
            # Cleaning the strings isn't strictly necessary but allows
            # for simple equality checks below and removes the need to
            # call refresh().
            if arg in ['newmodel', 'newvendor',
                       'cpuname', 'cpuvendor', 'disktype', 'diskcontroller',
                       'nicmodel', 'nicvendor']:
                if value is not None:
                    arguments[arg] = value.lower().strip()

        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   compel=True)

        if leave_existing and (newmodel or newvendor):
            raise ArgumentError("Cannot update model name or vendor without "
                                "updating any existing machines.")

        fix_existing = not leave_existing
        dbmachines = set()

        # The sub-branching here is a little difficult to read...
        # Basically, there are three different checks to handle
        # setting a new vendor, a new name, or both.
        if newvendor:
            dbnewvendor = Vendor.get_unique(session, newvendor, compel=True)
            if newmodel:
                Model.get_unique(session, name=newmodel, vendor=dbnewvendor,
                                 preclude=True)
            else:
                Model.get_unique(session, name=dbmodel.name,
                                 vendor=dbnewvendor, preclude=True)
            dbmodel.vendor = dbnewvendor
        if newmodel:
            if not newvendor:
                Model.get_unique(session, name=newmodel, vendor=dbmodel.vendor,
                                 preclude=True)
            dbmodel.name = newmodel
        if newvendor or newmodel:
            q = session.query(Machine).filter_by(model=dbmodel)
            dbmachines.update(q.all())

        # For now, can't update model_type.  There are too many spots
        # that special case things like aurora_node or virtual_machine to
        # know that the transistion is safe.  If there is enough need we
        # can always add those transitions later.
        if arguments['machine_type'] is not None:
            raise UnimplementedError("Cannot (yet) change a model's "
                                     "machine type.")

        if comments:
            dbmodel.comments = comments
            # The comments also do not affect the templates.

        cpu_args = ['cpuname', 'cpuvendor', 'cpuspeed']
        cpu_info = dict([(self.argument_lookup[arg], arguments[arg])
                         for arg in cpu_args])
        cpu_values = [v for v in cpu_info.values() if v is not None]
        nic_args = ['nicmodel', 'nicvendor']
        nic_info = dict([(self.argument_lookup[arg], arguments[arg])
                         for arg in nic_args])
        nic_values = [v for v in nic_info.values() if v is not None]
        spec_args = ['cpunum', 'memory', 'disktype', 'diskcontroller',
                     'disksize', 'nics']
        specs = dict([(self.argument_lookup[arg], arguments[arg])
                      for arg in spec_args])
        spec_values = [v for v in specs.values() if v is not None]

        if not dbmodel.machine_specs:
            if cpu_values or nic_values or spec_values:
                # You can't add a non-machine model with machine_specs
                # thus we only need to check here if you try and update
                if not dbmodel.model_type.isMachineType():
                    raise ArgumentError("Machine specfications are only valid"
                                        " for machine types")
                if not cpu_values or len(spec_values) < len(spec_args):
                    raise ArgumentError("Missing required parameters to store "
                                        "machine specs for the model.  Please "
                                        "give all CPU, disk, RAM, and NIC "
                                        "count information.")
                dbcpu = Cpu.get_unique(session, compel=True, **cpu_info)
                if nic_values:
                    dbnic = Model.get_unique(session, compel=True,
                                             model_type=NicType.Nic, **nic_info)
                else:
                    dbnic = Model.default_nic_model(session)
                dbmachine_specs = MachineSpecs(model=dbmodel, cpu=dbcpu,
                                               nic_model=dbnic, **specs)
                session.add(dbmachine_specs)

        # Anything below that updates specs should have been verified above.

        if cpu_values:
            dbcpu = Cpu.get_unique(session, compel=True, **cpu_info)
            self.update_machine_specs(model=dbmodel, dbmachines=dbmachines,
                                      attr='cpu', value=dbcpu,
                                      fix_existing=fix_existing)

        for arg in ['memory', 'cpunum']:
            if arguments[arg] is not None:
                self.update_machine_specs(model=dbmodel, dbmachines=dbmachines,
                                          attr=self.argument_lookup[arg],
                                          value=arguments[arg],
                                          fix_existing=fix_existing)

        if arguments['disktype']:
            if fix_existing:
                raise ArgumentError("Please specify --leave_existing to "
                                    "change the model disktype.  This cannot "
                                    "be converted automatically.")
            dbmodel.machine_specs.disk_type = arguments['disktype']

        for arg in ['diskcontroller', 'disksize']:
            if arguments[arg] is not None:
                self.update_disk_specs(model=dbmodel, dbmachines=dbmachines,
                                       attr=self.argument_lookup[arg],
                                       value=arguments[arg],
                                       fix_existing=fix_existing)

        if nic_values:
            dbnic = Model.get_unique(session, compel=True, **nic_info)
            self.update_interface_specs(model=dbmodel, dbmachines=dbmachines,
                                        value=dbnic, fix_existing=fix_existing)

        if arguments['nics'] is not None:
            dbmodel.machine_specs.nic_count = arguments['nics']

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        for dbmachine in dbmachines:
            plenaries.append(Plenary.get_plenary(dbmachine))
        plenaries.write()

        return

    def update_machine_specs(self, model, dbmachines,
                             attr=None, value=None, fix_existing=False):
        session = object_session(model)
        if fix_existing:
            oldattr = getattr(model.machine_specs, attr)
            filters = {'model': model, attr: oldattr}
            q = session.query(Machine).filter_by(**filters)
            for dbmachine in q.all():
                setattr(dbmachine, attr, value)
                dbmachines.add(dbmachine)

        setattr(model.machine_specs, attr, value)

    def update_disk_specs(self, model, dbmachines,
                          attr=None, value=None, fix_existing=False):
        session = object_session(model)
        if fix_existing:
            oldattr = getattr(model.machine_specs, attr)
            # disk_capacity => capacity
            disk_attr = attr.replace('disk_', '')
            filters = {disk_attr: oldattr}
            q = session.query(Disk)
            q = q.filter_by(**filters)
            q = q.join('machine')
            q = q.filter_by(model=model)
            for dbdisk in q.all():
                setattr(dbdisk, disk_attr, value)
                dbmachines.add(dbdisk.machine)

        setattr(model.machine_specs, attr, value)

    def update_interface_specs(self, model, dbmachines, value=None,
                               fix_existing=False):
        session = object_session(model)
        if fix_existing:
            old_nic_model = model.machine_specs.nic_model
            q = session.query(Interface)
            # Skip interfaces where the model was set explicitely to something
            # other than the default
            q = q.filter(Interface.model == old_nic_model)
            q = q.join(HardwareEntity)
            q = q.filter(HardwareEntity.model == model)
            for dbiface in q.all():
                dbiface.model = value
                dbmachines.add(dbiface.hardware_entity)

        model.machine_specs.nic_model = value
