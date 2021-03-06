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
"""Contains the logic for `aq update machine`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Cpu, Chassis, ChassisSlot, Model, Cluster,
                                Machine, BundleResource, VirtualNasDisk,
                                VirtualLocalDisk, Filesystem, Share)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.hardware_entity import update_primary_ip
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.resources import (find_resource,
                                                 get_resource_holder)
from aquilon.worker.templates import (Plenary, PlenaryCollection,
                                      PlenaryHostData)
from aquilon.worker.processes import DSDBRunner


class CommandUpdateMachine(BrokerCommand):

    required_parameters = ["machine"]

    # handles clusters and hosts
    def get_metacluster(self, holder):
        if hasattr(holder, "metacluster"):
            return holder.metacluster

        # vmhost
        if holder.cluster:
            return holder.cluster.metacluster
        else:
            # TODO vlocal still has clusters, so this case not tested yet.
            return None

    def render(self, session, logger, machine, model, vendor, serial,
               chassis, slot, clearchassis, multislot,
               vmhost, cluster, allow_metacluster_change,
               cpuname, cpuvendor, cpuspeed, cpucount, memory, ip, uri,
               **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))
        if dbmachine.vm_container:
            plenaries.append(Plenary.get_plenary(dbmachine.vm_container))
        if dbmachine.host:
            # Using PlenaryHostData directly, to avoid warnings if the host has
            # not been configured yet
            plenaries.append(PlenaryHostData.get_plenary(dbmachine.host))

        if clearchassis:
            del dbmachine.chassis_slot[:]

        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            dbmachine.location = dbchassis.location
            if slot is None:
                raise ArgumentError("Option --chassis requires --slot "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)
        elif slot is not None:
            dbchassis = None
            for dbslot in dbmachine.chassis_slot:
                if dbchassis and dbslot.chassis != dbchassis:
                    raise ArgumentError("Machine in multiple chassis, please "
                                        "use --chassis argument.")
                dbchassis = dbslot.chassis
            if not dbchassis:
                raise ArgumentError("Option --slot requires --chassis "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            loc_clear_chassis = False
            for dbslot in dbmachine.chassis_slot:
                dbcl = dbslot.chassis.location
                if dbcl != dblocation:
                    if chassis or slot is not None:
                        raise ArgumentError("{0} conflicts with chassis {1!s} "
                                            "location {2}."
                                            .format(dblocation, dbslot.chassis,
                                                    dbcl))
                    else:
                        loc_clear_chassis = True
            if loc_clear_chassis:
                del dbmachine.chassis_slot[:]
            dbmachine.location = dblocation

            if dbmachine.host:
                for vm in dbmachine.host.virtual_machines:
                    plenaries.append(Plenary.get_plenary(vm))
                    vm.location = dblocation

        if model or vendor:
            # If overriding model, should probably overwrite default
            # machine specs as well.
            if not model:
                model = dbmachine.model.name
            if not vendor:
                vendor = dbmachine.model.vendor.name
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)
            if not dbmodel.model_type.isMachineType():
                raise ArgumentError("The update_machine command cannot update "
                                    "machines of type %s." %
                                    dbmodel.model_type)
            # We probably could do this by forcing either cluster or
            # location data to be available as appropriate, but really?
            # Failing seems reasonable.
            if dbmodel.model_type != dbmachine.model.model_type and \
               (dbmodel.model_type.isVirtualMachineType() or
                dbmachine.model.model_type.isVirtualMachineType()):
                raise ArgumentError("Cannot change machine from %s to %s." %
                                    (dbmachine.model.model_type,
                                     dbmodel.model_type))

            old_nic_model = dbmachine.model.nic_model
            new_nic_model = dbmodel.nic_model
            if old_nic_model != new_nic_model:
                for iface in dbmachine.interfaces:
                    if iface.model == old_nic_model:
                        iface.model = new_nic_model

            dbmachine.model = dbmodel

        if cpuname or cpuvendor or cpuspeed is not None:
            dbcpu = Cpu.get_unique(session, name=cpuname, vendor=cpuvendor,
                                   speed=cpuspeed, compel=True)
            dbmachine.cpu = dbcpu

        if cpucount is not None:
            dbmachine.cpu_quantity = cpucount
        if memory is not None:
            dbmachine.memory = memory
        if serial:
            dbmachine.serial_no = serial

        if ip:
            update_primary_ip(session, logger, dbmachine, ip)

        if uri and not dbmachine.model.model_type.isVirtualAppliance():
            raise ArgumentError("URI can be specified only for virtual "
                                "appliances and the model's type is %s" %
                                dbmachine.model.model_type)

        if uri:
            dbmachine.uri = uri

        # FIXME: For now, if a machine has its interface(s) in a portgroup
        # this command will need to be followed by an update_interface to
        # re-evaluate the portgroup for overflow.
        # It would be better to have --pg and --autopg options to let it
        # happen at this point.
        if cluster or vmhost:
            if not dbmachine.vm_container:
                raise ArgumentError("Cannot convert a physical machine to "
                                    "virtual.")

            old_holder = dbmachine.vm_container.holder.holder_object
            resholder = get_resource_holder(session, hostname=vmhost,
                                            cluster=cluster, compel=False)
            new_holder = resholder.holder_object

            if self.get_metacluster(new_holder) != self.get_metacluster(old_holder) \
               and not allow_metacluster_change:
                raise ArgumentError("Current {0:l} does not match "
                                    "new {1:l}."
                                    .format(self.get_metacluster(old_holder),
                                            self.get_metacluster(new_holder)))

            plenaries.append(Plenary.get_plenary(old_holder))
            plenaries.append(Plenary.get_plenary(new_holder))

            dbmachine.vm_container.holder = resholder

            for dbdisk in dbmachine.disks:
                if isinstance(dbdisk, VirtualNasDisk):
                    old_share = dbdisk.share
                    if isinstance(old_share.holder, BundleResource):
                        resourcegroup = old_share.holder.resourcegroup.name
                    else:
                        resourcegroup = None

                    new_share = find_resource(Share, new_holder, resourcegroup, old_share.name,
                                           error=ArgumentError)

                    # If the shares are registered at the metacluster level and both
                    # clusters are in the same metacluster, then there will be no
                    # real change here
                    if new_share != old_share:
                        old_share.disks.remove(dbdisk)
                        new_share.disks.append(dbdisk)

                if isinstance(dbdisk, VirtualLocalDisk):
                    old_filesystem = dbdisk.filesystem

                    new_filesystem = find_resource(Filesystem, new_holder, None,
                                                   old_filesystem.name,
                                                   error=ArgumentError)

                    if new_filesystem != old_filesystem:
                        old_filesystem.disks.remove(dbdisk)
                        new_filesystem.disks.append(dbdisk)

            if isinstance(new_holder, Cluster):
                dbmachine.location = new_holder.location_constraint
            else:
                # vmhost
                dbmachine.location = new_holder.hardware_entity.location

        session.flush()

        # Check if the changed parameters still meet cluster capacity
        # requiremets
        if dbmachine.cluster:
            dbmachine.cluster.validate()
            if allow_metacluster_change:
                dbmachine.cluster.metacluster.validate()
        if dbmachine.host and dbmachine.host.cluster:
            dbmachine.host.cluster.validate()

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.

        with plenaries.get_key():
            plenaries.stash()
            try:
                plenaries.write(locked=True)

                dsdb_runner = DSDBRunner(logger=logger)
                dsdb_runner.update_host(dbmachine, oldinfo)
                dsdb_runner.commit_or_rollback("Could not update machine in DSDB")
            except:
                plenaries.restore_stash()
                raise

        return

    def adjust_slot(self, session, logger,
                    dbmachine, dbchassis, slot, multislot):
        for dbslot in dbmachine.chassis_slot:
            # This update is a noop, ignore.
            # Technically, this could be a request to trim the list down
            # to just this one slot - in that case --clearchassis will be
            # required.
            if dbslot.chassis == dbchassis and dbslot.slot_number == slot:
                return
        if len(dbmachine.chassis_slot) > 1 and not multislot:
            raise ArgumentError("Use --multislot to support a machine in more "
                                "than one slot, or --clearchassis to remove "
                                "current chassis slot information.")
        if not multislot:
            slots = ", ".join([str(dbslot.slot_number) for dbslot in
                               dbmachine.chassis_slot])
            logger.info("Clearing {0:l} out of {1:l} slot(s) "
                        "{2}".format(dbmachine, dbchassis, slots))
            del dbmachine.chassis_slot[:]
        q = session.query(ChassisSlot)
        q = q.filter_by(chassis=dbchassis, slot_number=slot)
        dbslot = q.first()
        if dbslot:
            if dbslot.machine:
                raise ArgumentError("{0} slot {1} already has machine "
                                    "{2}.".format(dbchassis, slot,
                                                  dbslot.machine.label))
        else:
            dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
        dbmachine.chassis_slot.append(dbslot)

        return
