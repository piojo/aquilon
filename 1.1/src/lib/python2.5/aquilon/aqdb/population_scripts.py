#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent- tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Functions to populate the tables with racks, chassis,
    machines, and interfaces """
from __future__ import with_statement

import sys
sys.path.append('../..')

import random

from aquilon.aqdb.utils.debug import ipshell
from db import meta, engine, Session


from location import *
from network import *
from service import *
from configuration import *
from hardware import *
from interfaces import *

cmnt = 'FAKE'

s=Session()
model  = s.query(Model).filter_by(name='hs21').one()
syslog = s.query(Service).filter_by(name='syslog').one()
prod   = s.query(Domain).filter_by(name='production').one()
stat   = s.query(Status).filter_by(name='prod').one()
nick=Session.query(Nic).filter_by(driver='tg3').one()

def n_of(n,string):
    """ generate n strings with sequential integer appended
        useful for generating lots of rack/node names, etc """
    while n > 0:
        yield ''.join([string,str(n)])
        n-=1

def n_of_rand_hex(n):
    """generate n random hex chars """
    while n > 0:
        yield random.choice('0123456789abcdef')
        n-=1

def make_interfaces():
    """ generate e0 and e1 with random hex fields for FAKE commented
        machine that has none. Theres a chance it might repeat but
        I'm not too worried about it, and wrapped in try/except anyway """

    for m in s.query(Machine).filter_by(comments=cmnt).all():
        if len(m.interfaces) == 0:
            for n in range(2):
                try:
                    pi=PhysicalInterface(
                        'e'+str(n),nick,random_mac(),m,
                    comments=cmnt)
                    s.save(pi)
                except Exception, e:
                    print e
                    s.rollback()
                    return
    try:
        s.commit()
    except Exception, e:
        print e
        s.close()
        return

def two_in_each():
    nodelist=[]

    for b in s.query(Building).all():
        racks = (Rack(r,'rack',fullname='rack %s'%r,
                      parent=b,comments=cmnt)
            for r in n_of(2,str(b.name)))

        for rack in racks:
            s.save(rack)
            chs = (Chassis(c,'chassis', fullname='chassis %s'%c,
                           parent=rack,comments=cmnt)
                for c in n_of(2,''.join([rack.name,'c'])))

        for ch in chs:
            s.save(ch)
            nodes = (Machine(ch,model,name=nodename,comments=cmnt)
                     for nodename in n_of(12,''.join([ch.name,'n'])))

        nodecount=0
        for node in nodes:
            try:
                s.save(node)
                nodelist.append(node)
            except Exception, e:
                print e
                s.rollback()
                return

    try:
        s.commit()
    except Exception, e:
        s.rollback()
        print e
        return


    print 'created %s nodes'%(len(nodelist))
    try:
        for node in nodelist:
            h=Host(node,name=node.name,status=stat, domain=prod,comments=cmnt)
            s.save(h)
            s.commit()
    except Exception, e:
        print e
        s.close()
        return
    print 'created %s hosts'%(len(nodelist))

""" To clear fake stuff:
    delete from physical_interface where interface_id in \
        (select id from interface where comments like '%FAKE%');

    delete from interface where comments like '%FAKE%';
    delete from host where comments like '%FAKE';
    delete from machine where comments like '%FAKE%';
    delete from rack where id in (select id from location where comments like '%FAKE%');
    delete from chassis where id in (select id from location where comments like '%FAKE%');
    delete from location where comments like '%FAKE%';

"""

def random_mac():
    mac=[]
    for i in range(4):
        byte=''
        for a in n_of_rand_hex(2):
            byte=''.join([byte,a])
        mac.append(byte)
    return ':'.join(mac)

def make_host(name, machine,**kw):
    try:
        m=s.query(Machine).filter_by(name=machine.name).one()
    except Exception,e:
        print e
        return
    try:
        h=Host(m,name=name)
    except Exception, e:
        s.rollback()
        print e
        return

    assert(h)
    configure_host(h)
    #s.delete(h)

def configure_host(host):
    a=s.query(Archetype).filter_by(name='aquilon').one()
    for svc in a.service_list.items:
        print 'finding an instance of %s for %s'%(svc.service,host)
        si_list=s.query(ServiceInstance).filter_by(service=svc.service).all()

        print si_list


if __name__ == '__main__':
    two_in_each()
    make_interfaces()