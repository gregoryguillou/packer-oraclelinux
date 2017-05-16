#!/bin/bash
#
# Update RPMs with the latest release
#
# sudo -n yum -y update
#
# Clean the configuration and switch to RHCK before you upload the
# OVF file to AWS...
#

# Set network to eth0 and remove links to HWADDR
sed -i '/HWADDR/d' /etc/sysconfig/network-scripts/ifcfg-eth0
sed -i '/UUID/d' /etc/sysconfig/network-scripts/ifcfg-eth0
cat /etc/sysconfig/network-scripts/ifcfg-eth0

# Update RPMs
cd /etc/yum.repos.d
curl -O http://public-yum.oracle.com/public-yum-ol6.repo
yum -y install yum-utils
yum-config-manager --enable ol7_UEKR4
yum-config-manager --disable ol7_UEKR3
yum -y update

# Set default Kernel to RHCK
KERNEL=$(rpm -q kernel --queryformat "%{INSTALLTIME} %{VERSION}-%{RELEASE}\n" \
          | grep "2.6.32" | sort -n | tail -n 1 | awk '{print $2}')
MENU=$[$(grep -P "kernel" /boot/grub/grub.conf |grep -v "#" |cat -n|grep "$KERNEL"|awk '{print $1}')-1]
sed -i s/default=.*/default=$MENU/ /boot/grub/grub.conf

# Install Cloud-Init
yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm
yum-config-manager --enable ol6_optional_latest
yum install -y cloud-init
sed -i 's/name: fedora/name: ec2-user/g' /etc/cloud/cloud.cfg
sed -i 's/gecos: Fedora Cloud User/gecos: EC2 Cloud User/g' /etc/cloud/cloud.cfg
sed -i 's/distro: fedora/distro: rhel/g' /etc/cloud/cloud.cfg
# sed -i 's/lock_passwd: true/lock_passwd: false/g' /etc/cloud/cloud.cfg

#
cat /etc/oracle-release

#
sed -i 's/Defaults\ \ \ \ requiretty/Defaults   !requiretty/' /etc/sudoers
sed -i 's/Defaults\ \ \ !visiblepw/Defaults    visiblepw/' /etc/sudoers

#
#systemctl disable kdump.service
chkconfig kdump off

#
passwd -l root

