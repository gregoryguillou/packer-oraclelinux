# packer-oraclelinux

This packages demonstrates how to create an Oracle Linux OVA with Packer/Virtualbox to use with AWS EC2. It can easily be adapted to create any kind of images for Cloud Providers or VMWare/OracleVM

## Configuration

A few pre-requisites must be met in order for that project to work as expected. Among them:
- Python3 must be installed and in the PATH
- Packer must be installed 
- Virtualbox must be installer
- You must download the Oracle Linux 7.2 ISO file

the ```project.properties```. It must contain the 4 values below:

```
PROJECT_HOME=/home/gregory/project/packer-oraclelinux
PACKER=/home/gregory/distribs/packer
OS_DISTRIBUTION=/home/gregory/distribs/V100082-01.iso
REPO_URL=http://10.0.2.2/repo
```

## Building a VM

```vm-generate.py``` allows to create a VM. Use the 2 parameters below:
- ```-t vbox-ol72``` defines the template name
- ```-n``` allows to name the VM

The command below shows how to use the script:

```
./kickstart-vm.py -t vbox-ol72 -n purple
```

