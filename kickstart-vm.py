#!/usr/bin/env python3
import json
import getopt, sys, os
import subprocess

def usage():
    print("""
KICKSTART-VM()                                                    KICKSTART-VM()

NAME
     kickstart-vm.py - build a Virtual Machine from an ISO

DESCRIPTION

     This Python scripts relies on packer.io and a type-2 hypervisor (Usually 
     Virtualbox but could be VMWare Workstation) as well as a Kickstart file
     to create and save a virtual machine OVA/VMDK.

SYNOPSIS

     kickstart-vm.py [-h] [-v] [-n {hostname}] [-t {template_name}]

OPTIONS

     -h, --help
     displays kickstart-vm.py usage and help

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

KICKSTART-VM()                                                    KICKSTART-VM()
          """);

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvn:t:", 
            ["help", "verbose", "hostname=", "template"]) 
    except getopt.GetoptError as err:
        print(err);
        usage();
        sys.exit(2);

    verbose = False;
    hostname="localhost";
    template="vbox-ol72";

    for o, a in opts:
        if o == "-v":
            verbose = True;
        elif o in ("-h", "--help"):
            usage();
            sys.exit();
        elif o in ("-n", "--hostname"):
            hostname = a;
        elif o in ("-t", "--template"):
            template = a;
        else:
            assert False;

    pid = os.getpid();
    os.environ["PID"] = str(pid)
    with open('project.properties') as f:
        for line in f:
            k, v = line.split('=')
            os.environ[k] = v.strip()

    if not os.path.exists(os.environ["PROJECT_HOME"]+"/tmp"):
        os.makedirs(os.environ["PROJECT_HOME"]+"/tmp")
    if not os.path.exists(os.environ["PROJECT_HOME"]+"/dist"):
        os.makedirs(os.environ["PROJECT_HOME"]+"/dist")
    if not os.path.exists(os.environ["PROJECT_HOME"]+"/tmp/"+str(pid)):
        os.makedirs(os.environ["PROJECT_HOME"]+"/tmp/"+str(pid))

    scripts=[];
    with open("templates/"+template+"/vm.json", "rt") as read_file:
        json_data = json.load(read_file)
        for i in range(1,3):
            print('script'+str(i)+':'+json_data['variables']['script'+str(i)])
            if os.stat(json_data['variables']['script'+str(i)]):
                scripts.append([json_data['variables']['script'+str(i)], 
                               os.path.basename(json_data['variables']['script'+str(i)])])
        for i in range(0,2):
            with open(scripts[i][0], "rt") as script_file:
                try:
                    os.stat("tmp/"+str(pid)+"/"+scripts[i][1])
                except IOError as e:
                    with open("tmp/"+str(pid)+"/"+scripts[i][1], "wt") as newscript_file:
                        for line in script_file:
                            newline=line.replace('{REPO_URL}', os.environ['REPO_URL'])
                            newline=newline.replace('{OS_DISTRIBUTION}', os.environ['OS_DISTRIBUTION'])
                            newscript_file.write(newline)

    with open("templates/"+template+"/vm.json", "rt") as read_file:
        with open("tmp/"+str(pid)+"/vm.json", "wt") as write_file:
            for line in read_file:
                newline=line.replace('{REPO_URL}', os.environ['REPO_URL'])
                newline=newline.replace('{OS_DISTRIBUTION}', os.environ['OS_DISTRIBUTION'])
                for i in range(0,2):
                    newline=newline.replace(scripts[i][0],"tmp/"+str(pid)+"/"+scripts[i][1])
                write_file.write(newline)

    with open("templates/"+template+"/ks.cfg", "rt") as read_file:
        with open("tmp/"+str(pid)+"/ks.cfg", "wt") as write_file:
            for line in read_file:
                write_file.write(line.replace('{hostname}', hostname));

    var_json = """{
  "vm_name": "{hostname}",
  "ks_file": "{pid}/ks.cfg"
}""";

    with open("tmp/"+str(pid)+"/vm.cfg", "wt") as write_file:
        for line in var_json.splitlines():
            write_file.write(line.replace('{hostname}', hostname).
                replace('{pid}', str(pid)) + "\n");

    p = subprocess.Popen([ os.environ["PACKER"], "build", 
        "-var-file=tmp/"+str(pid)+"/vm.cfg",  
        "tmp/"+str(pid)+"/vm.json"], shell=False , stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, bufsize=1);
    lines_iterator = iter(p.stdout.readline, b"");
    while p.poll() is None:
        for line in lines_iterator:
            nline = line.rstrip()
            print(nline.decode("latin"), end = "\r\n",flush =True)

    os.remove("tmp/"+str(pid)+"/ks.cfg")
    os.remove("tmp/"+str(pid)+"/vm.cfg")
    os.remove("tmp/"+str(pid)+"/vm.json")
    for i in range(0,2):
        try:
            os.remove("tmp/"+str(pid)+"/"+scripts[i][1])
        except IOError as e:
            print("tmp/"+str(pid)+"/"+scripts[i][1]+" already removed")
    os.rmdir("tmp/"+str(pid))

if __name__ == "__main__":
    main()

