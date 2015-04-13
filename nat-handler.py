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

    or as follows:

        {
            "eu-west-1a": {
                "route_table_id": "rtb-0e0ed06b",
                "elastic_ip_allocation_id": "eipalloc-cc618fa9"
            },
            "eu-west-1b": {
                "route_table_id": "rtb-090ed06c",
                "elastic_ip_allocation_id": "eipalloc-c5618fa0",
            },
            "eu-west-1c": {
                "route_table_id": "rtb-080ed06d",
                "elastic_ip_allocation_id": "eipalloc-c4618fa1",
            }
        }

    * All NAT instances expose the role=nat tag in Serf.
    * All NAT instances expose the az tag in Serf, containing the availability
    zone in which it is running. For example, az=eu-west-1a.
    * The jq json processor program is available.

'''

import json
import os
import sys

from boto.ec2 import connect_to_region as connect_to_ec2
from boto.vpc import connect_to_region as connect_to_vpc
from boto.utils import get_instance_metadata
from subprocess import call


NAT_CONFIG = '/etc/nat.conf'


class Config(object):
    def __init__(self, config_dict):
        self.config_dict = config_dict

    def num_zones(self):
        return len(self.config_dict)

    def route_table_id(self, az):
        entry = self.config_dict[az]
        if isinstance(entry, dict):
            return entry['route_table_id']
        return entry

    def elastic_ip_allocation_id(self, az):
        entry = self.config_dict[az]
        if isinstance(entry, dict):
            return entry.get('elastic_ip_allocation_id')
        return None



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

    def take_route(self, az):
        route_table_id = self.config.route_table_id(az)
        vpc = connect_to_vpc(self.current_region)
        vpc.replace_route(route_table_id, '0.0.0.0/0', instance_id=self.current_instance_id)

    def take_elastic_ip(self, az):
        elastic_ip_allocation_id = self.config.elastic_ip_allocation_id(az)
        if elastic_ip_allocation_id:
            ec2 = connect_to_ec2(self.current_region)
            ec2.associate_address(
                    self.current_instance_id, allocation_id=elastic_ip_allocation_id)

    def __call__(self, az=None):
        az = az or self.current_az
        self.take_route(az)
        self.take_elastic_ip(az)



class Quorum(object):
    def __init__(self, config):
        self.config = config

    def quorum(self):
        ''' Returns True if the current nat belongs to the quorum. '''
        t = self.config.num_zones()
        n = t - t / 2
        return self.alive(n)

    def alive(self, n):
        ''' Returns True if at least n nats are alive. '''
        cmd = "serf members -tag role=nat -status=alive -format json | jq '.members | length >= %s' | grep true" % n
        res = call(cmd, shell=True)
        return res == 0

    __call__ = quorum



class SerfMember(object):
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
        config = Config(json.load(f))

    event = os.environ['SERF_EVENT']
    quorum = Quorum(config)
    reroute = Rerouter(config)

    if quorum():
        if event == 'member-join':
            reroute()
        elif event in ['member-leave', 'member-failed']:
            members = map(SerfMember.parse, sys.stdin.readlines())
            nats = [x for x in members if x.role == 'nat']
            for nat in nats:
                reroute(nat.az)


if __name__ == '__main__':
    main()
