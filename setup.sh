#!/bin/bash -ex

apt-get update

INSTANCE_ID=`curl -sL http://169.254.169.254/latest/meta-data/instance-id`

# Enable ip forwarding and masquerading
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
chmod 600 /etc/sysctl.conf
sysctl -p
iptables -t nat -A POSTROUTING -s $CIDR_BLOCK -o eth0 -j MASQUERADE

# Disable source destination check
apt-get install -y awscli
aws ec2 modify-instance-attribute --region $REGION --instance-id $INSTANCE_ID --no-source-dest-check

# Install the Serf NAT handler
curl -sL https://raw.githubusercontent.com/wrapp/nat/master/nat-handler.py > /usr/local/bin/nat-handler.py
chmod a+x /usr/local/bin/nat-handler.py

# Install jq
apt-get install -y jq

# Configure Serf to identify itself as NAT and to run the nat handler on member events.
serfconf=/etc/serf.conf
tmpconf=/tmp/serf.conf
cat $serfconf  | jq '.event_handlers += ["member-join,member-leave,member-failed=/usr/local/bin/nat-handler.py"]' > $tmpconf && mv $tmpconf $serfconf
cat $serfconf  | jq '. += {"tags": {"role": "nat"}}' > $tmpconf && mv $tmpconf $serfconf
service serf restart
