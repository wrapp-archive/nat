High availability NAT with Serf
===============================

High availability management of EC2 VPC routes based on Serf. Serf keeps track
of when NAT instances come and go and will pass those events on to the
`nat-handler.py` script. When new NAT instances join the cluster (which could
also mean that the instance itself is joining some other cluster) script will
take its default route as specified in `/etc/nat.conf`. When NAT instances fail
or leave the cluster the script will take their default route so that all
routes are always being served by somebody.

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
