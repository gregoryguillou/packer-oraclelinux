#!/usr/bin/python3
"""
creates an OVA from an ISO with Packer
"""
import json
import getopt
import sys
import os
import subprocess

def usage():
    """
    prints module help
    """
    print("""
KICKSTARTVM()                                                      KICKSTARTVM()

NAME
     kickstartvm.py - build a Virtual Machine from an ISO

DESCRIPTION

     This Python scripts relies on packer.io and a type-2 hypervisor (Usually 
     Virtualbox but could be VMWare Workstation) as well as a Kickstart file
     to create and save a virtual machine OVA/VMDK.

SYNOPSIS

     kickstartvm.py [-h] [-v] [-n {hostname}] [-t {template_name}]

OPTIONS

     -h, --help
     displays kickstartvm.py usage and help

     -v, --verbose
     runs in verbose mode

     -n {hostname}, --hostname={hostname}
     set the guest hostname by replacing the {hostname} string in the kickstart
     file.

     -t {template_name}, --template={template_name}
     Use the associated template directory to generate the virtual machine; all
     the properties, including the virtualization engine, VM structure and 
     installed components are part of that template directory.

PRE-REQUISITES

     Packer.io 0.10.1+ as well as a type-2 hypervisor, aka Virtualbox, VMWare
     Workstation Pro must be installed and part of the current PATH in order
     for the script to work as expected. Your host must also be connected to the
     Internet; this is because the latest RPMs are updated from
     http://public-yum.oracle.com and some components, like Cloud-init must be
     downloaded

HISTORY

     2016 -- written by Gregory P. Guillou (gregory.guillou@resetlogs.com)

KICKSTARTVM()                                                      KICKSTARTVM()
          """)

def genkickstart(hostname, pid, template):
    """
    generates a kickstart file
    """
    with open("templates/"+template+"/ks.cfg", "rt") as read_file:
        with open("tmp/"+str(pid)+"/ks.cfg", "wt") as write_file:
            for line in read_file:
                write_file.write(line.replace('{hostname}', hostname))

def genvmjson(pid, template):
    """
    generates VM JSON file
    """
    scripts = []
    with open("templates/"+template+"/vm.json", "rt") as read_file:
        json_data = json.load(read_file)
        for i in range(1, 3):
            print('script'+str(i)+':'+json_data['variables']['script'+str(i)])
            if os.stat(json_data['variables']['script'+str(i)]):
                scripts.append([json_data['variables']['script'+str(i)],
                                os.path.basename(json_data['variables']['script'+str(i)])])
        for i in range(0, 2):
            with open(scripts[i][0], "rt") as script_file:
                try:
                    os.stat("tmp/"+str(pid)+"/"+scripts[i][1])
                except IOError:
                    with open("tmp/"+str(pid)+"/"+scripts[i][1], "wt") as newscript_file:
                        for line in script_file:
                            newline = line.replace('{OS_DISTRIBUTION}',
                                                   os.environ['OS_DISTRIBUTION'])
                            newscript_file.write(newline)

    with open("templates/"+template+"/vm.json", "rt") as read_file:
        with open("tmp/"+str(pid)+"/vm.json", "wt") as write_file:
            for line in read_file:
                newline = line.replace('{OS_DISTRIBUTION}', os.environ['OS_DISTRIBUTION'])
                for i in range(0, 2):
                    newline = newline.replace(scripts[i][0], "tmp/"+str(pid)+"/"+scripts[i][1])
                write_file.write(newline)

    return scripts

def genconfig(hostname, pid):
    """
    generates a Packer configuration file
    """
    var_json = """{
  "vm_name": "{hostname}",
  "ks_file": "{pid}/ks.cfg"
}"""

    with open("tmp/"+str(pid)+"/vm.cfg", "wt") as write_file:
        for line in var_json.splitlines():
            write_file.write(line.replace('{hostname}', hostname).replace(
                '{pid}', str(pid)) + "\n")

def processvm(pid, scripts):
    """
    runs Packer
    """
    process = subprocess.Popen([os.environ["PACKER"], "build",
                                "-var-file=tmp/"+str(pid)+"/vm.cfg",
                                "tmp/"+str(pid)+"/vm.json"],
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               bufsize=1)
    lines_iterator = iter(process.stdout.readline, b"")
    while process.poll() is None:
        for line in lines_iterator:
            nline = line.rstrip()
            print(nline.decode("latin"), end="\r\n", flush=True)

    os.remove("tmp/"+str(pid)+"/ks.cfg")
    os.remove("tmp/"+str(pid)+"/vm.cfg")
    os.remove("tmp/"+str(pid)+"/vm.json")
    for i in range(0, 2):
        try:
            os.remove("tmp/"+str(pid)+"/"+scripts[i][1])
        except IOError:
            print("tmp/"+str(pid)+"/"+scripts[i][1]+" already removed")
    os.rmdir("tmp/"+str(pid))

def main():
    """
    kicks off Packer with the right options
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvn:t:", [
            "help", "verbose", "hostname=", "template"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    hostname = "localhost"
    template = "vbox-ol72"

    for opt, arg in opts:
        if opt == "-v":
            pass
        elif opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-n", "--hostname"):
            hostname = arg
        elif opt in ("-t", "--template"):
            template = arg
        else:
            assert False

    pid = os.getpid()
    os.environ["PID"] = str(pid)
    os.environ["PROJECT_HOME"] = os.path.dirname(os.path.realpath(__file__))
    with open('project.properties') as myfile:
        for line in myfile:
            key, value = line.split('=')
            os.environ[key] = value.strip()

    if not os.path.exists(os.environ["PROJECT_HOME"]+"/tmp"):
        os.makedirs(os.environ["PROJECT_HOME"]+"/tmp")
    if not os.path.exists(os.environ["PROJECT_HOME"]+"/dist"):
        os.makedirs(os.environ["PROJECT_HOME"]+"/dist")
    if not os.path.exists(os.environ["PROJECT_HOME"]+"/tmp/"+str(pid)):
        os.makedirs(os.environ["PROJECT_HOME"]+"/tmp/"+str(pid))

    scripts = genvmjson(pid, template)
    genkickstart(hostname, pid, template)
    genconfig(hostname, pid)

    processvm(pid, scripts)

if __name__ == "__main__":
    main()

