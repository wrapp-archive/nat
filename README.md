High availability NAT with Serf
===============================

High availability management of EC2 VPC routes based on Serf. Serf keeps track
of when NAT instances come and go and will pass those events on to the
`nat-handler.py` script. When new NAT instances join the cluster (which could
also mean that the instance itself is joining some other cluster) script will
allow running instances to take the default route its eth0 interface where this
interface will always have a public ip which connects all instances to the internet.
However, when NAT instances fail or leave the cluster the script will replace the route
with any running instance eth0 interface. This ensures all
routes are always being served by some instance.


More on failover
=================
Each instance would have 3 network interfaces eth0, eth1 and eth2 to begin with where eth0
will always have a public ip and eth1 w.r.t all alive nat instances will have an elastic ip
attached to it. eth2 on the other hand is used during failover where any alive nat instance will associate the
elastic ip of a failed instance onto its own eth2 interface. When the failed instance comes back
up (or another instance in the same availability zone) it claims back the elastic ip onto its eth1 interface.
Thus in this way, during failovers, elastic ips are always served by some running instances.


The script only operates in quorum, that is, when it's in the same cluster as
at least half of all the NAT instances. Using quorum helps solve race conditions during netsplits.

If you have Serf setup you could simply run the following script to get going,
either from EC2 userdata or your favourite config automation tool.


```bash
#!/bin/bash -ex

export REGION=eu-west-1
export CIDR_BLOCK=10.0.0.0/16

cat > /etc/nat.conf <<EOF
{
    "eu-west-1a": "rtb-f426f091",
    "eu-west-1b": "rtb-f426f091",
    "eu-west-1c": "rtb-f426f091"
}
EOF

curl -sL https://raw.githubusercontent.com/wrapp/nat/master/setup.sh | bash -ex
```
