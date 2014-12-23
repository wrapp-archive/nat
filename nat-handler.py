#!/usr/bin/env python

''' Serf handler for managing EC2 routes

This handler should be installed on NAT instances. It relies on Serf for
membership events from other NATs. When other NATs disappear from the cluster
this script will attempt to reroute their traffic onto the current instance. It
will only do this if it has quorum, that is, if a majority of the instances are
still available.

This script makes certain assumptions:

    * There is a json file called /etc/nat.conf that maps the default route
    table ID for each availability zone, as follows:

        {
            "eu-west-1a": "rtb-0e0ed06b",
            "eu-west-1b": "rtb-090ed06c",
            "eu-west-1c": "rtb-080ed06d"
        }

    * All NAT instances expose the role=nat tag in Serf.
    * All NAT instances expose the az tag in Serf, containing the availability
    zone in which it is running. For example, az=eu-west-1a.
    * The jq json processor program is available.

'''

import json
import os
import sys

from boto.vpc import connect_to_region
from boto.utils import get_instance_metadata
from subprocess import call


NAT_CONFIG = '/etc/nat.conf'


class Rerouter(object):
    def __init__(self, config):
        self.metadata = get_instance_metadata()
        self.config = config

    @property
    def current_instance_id(self):
        return self.metadata['instance-id']

    @property
    def current_az(self):
        return self.metadata['placement']['availability-zone']

    @property
    def current_region(self):
        return self.current_az[:-1]

    def take_route(self, az=None):
        az = az or self.current_az
        route_table_id = self.config[az]
        vpc = connect_to_region(self.current_region)
        vpc.replace_route(route_table_id, '0.0.0.0/0', instance_id=self.current_instance_id)

    __call__ = take_route


class Quorum(object):
    def __init__(self, config):
        self.config = config

    def quorum(self):
        ''' Returns True if the current nat belongs to the quorum. '''
        t = len(self.config)
        n = t - t / 2
        return self.alive(n)

    def alive(self, n):
        ''' Returns True if at least n nats are alive. '''
        cmd = "serf members -tag role=nat -status=alive -format json | jq '.members | length >= %s' | grep true" % n
        res = call(cmd, shell=True)
        return res == 0

    __call__ = quorum


class Member(object):
    def __init__(self, hostname, ip, role, tags):
        self.hostname = hostname
        self.ip = ip
        self.role = role
        self.tags = tags

    @property
    def az(self):
        return self.tags['az']

    @classmethod
    def parse_member(cls, row):
        ''' Parses serf row and returns (hostname, ip, role, tags). '''
        hostname, ip, role, tagstr  = row.strip().split('\t')
        tags = cls.parse_tags(tagstr)
        return cls(hostname, ip, role, tags)

    @classmethod
    def parse_tags(cls, tagstr):
        ''' Parses tag strings into a dicts: a=b,c=d -> {a: b, c: d} '''
        pairs = tagstr.split(',')
        return dict([x.split('=') for x in pairs])

    parse = parse_member


def main():
    with open(NAT_CONFIG) as f:
        config = json.load(f)

    event = os.environ['SERF_EVENT']
    quorum = Quorum(config)
    reroute = Rerouter(config)

    if quorum():
        if event == 'member-join':
            reroute()
        elif event in ['member-leave', 'member-failed']:
            members = map(Member.parse, sys.stdin.readlines())
            nats = [x for x in members if x.role == 'nat']
            for nat in nats:
                reroute(nat.az)


if __name__ == '__main__':
    main()
