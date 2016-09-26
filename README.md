# packer-oraclelinux

Creates an Oracle Linux image with Packer/Virtualbox or Packet/VMWare Workstation. It configures cloud-init from EPEL7 so that you can easily use AWS VM import/export and and turn it into an AMI. It can easily be adapted in a number of ways to install CentOS/RHEL, to turn the image into other formats (VMWare, Openstack...) or to prepare Oracle Software in baked AMI. Have fun!

## Configuration

To use that project, make sure:
- Python3 is installed and in the PATH
- Packer is installed and the PACKER variable referenced it in ```project.properties```
- Virtualbox or VMWare Workstation Pro are installed
- You've downloaded the Oracle Linux ISO and OS_DISTRIBUTION in ```project.properties``` points to it

To configure the project, create a ```project.properties``` like below:

```
PACKER=/home/gregory/distribs/packer
OS_DISTRIBUTION=/home/gregory/distribs/V100082-01.iso
```

- ```PACKER``` references the Packer executable
- ```OS_DISTRIBUTION``` defines the location of the Oracle Linux ISO you've downloaded

## Building a VM

```kickstart-vm``` creates an instance and store it in the ```dist``` directory of the project. It requires 2 parameters below:
- ```-t``` defines the template name and it should be vbox-ol72 or vmware-ol72
- ```-n``` defines the VM name. You might want to use ```-n localhost```

Here is an example of how to create a VM:

```
./kickstart-vm.py -t vbox-ol72 -n locathost
```

