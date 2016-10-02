#!/usr/bin/python3
"""
History:
--------
    10/2/1016 - G.Guillou - Creation
"""
import getopt
import sys
import os
import binascii
import threading
import random
import time
import boto3
from boto3.s3.transfer import S3Transfer

def usage():
    """
    usage: displays the module help. Type createami.py -h for more details.
    """

    print("""
CREATEAMI()                                                         CREATEAMI()

NAME
    createami.py - Export an OVA file to AWS and turn it into an AMI

DESCRIPTION

    This script creates an AWS AMI from an OVA file

SYNOPSIS

     createami.py [-h] [-v] [-f {file}] [-b {bucket}] -k [-p {profile}]

OPTIONS

     -h, --help
     displays export-ami.py usage and help

     -v, --verbose
     runs in verbose mode

     -f {file}, --file={file}
     points to the OVA file to load into AWS

     -b {bucket}, --bucket={bucket}
     specifies the bucket to use as a staging to load the OVA into AWS

     -k, --keep
     let the OVA on the bucket; otherwise delete it once exported into an AMI

     -p {profile}, --profile={profile}
     defines the AWS CLI profile to use to connect to AWS. If none, the
     programm uses the default profile. As a result, ~/.aws/credentials
     must exist and be properly configured

PRE-REQUISITES

     A number of pre-requisites must be met, including the fact AWS Python
     SDK

HISTORY

     2016 -- written by Gregory P. Guillou (gregory.guillou@resetlogs.com)

CREATEAMI()                                                         CREATEAMI()
""")

class ProgressPercentage(object):
    """
    displays percentage of a S3 file upload; see S3Transferfor more
    informations.
    """
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

class ImportOVA:
    """
    provides methods to import an .ova file into an AMI.
    """

    def __init__(self, profile):
        self.key = ''.join([chr(random.randint(97, 122)) for i in range(0, 10)])
        self.profile=profile

    def createrole(self, bucket):
        """
        createrole: creates a role for AWS VM Import/Export to create an AMI
        """
        boto3.setup_default_session(profile_name=self.profile)
        client = boto3.client('iam')
        rolename = "VMImport4Key"+self.key

        policydocument = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": { "Service": "vmie.amazonaws.com" },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals":{
                    "sts:ExternalId": "vmimport"
                }
            }
        }]}"""
        client.create_role(
            RoleName=rolename,
            AssumeRolePolicyDocument=policydocument)

        policydocument = """{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "s3:ListBucket",
            "s3:GetBucketLocation"],
        "Resource": [
            "arn:aws:s3:::"""+bucket+""""]
    },{
        "Effect": "Allow",
        "Action": [
            "s3:GetObject"],
        "Resource": [
            "arn:aws:s3:::"""+bucket+"""/*"]
    },{
        "Effect": "Allow",
        "Action":[
            "ec2:ModifySnapshotAttribute",
            "ec2:CopySnapshot",
            "ec2:RegisterImage",
            "ec2:Describe*"],
        "Resource": "*"
    }]}"""
        client.put_role_policy(
            RoleName=rolename,
            PolicyName='VMImportS3andEC2Access'+self.key,
            PolicyDocument=policydocument)

        time.sleep(10)

        return rolename

    def deleterole(self):
        """
        deleterole: deletes the previously created role
        """
        boto3.setup_default_session(profile_name=self.profile)
        client = boto3.client('iam')
        rolename = "VMImport4Key"+self.key
        response = client.list_role_policies(
            RoleName=rolename)

        for policy in response["PolicyNames"]:
            client.delete_role_policy(
                RoleName=rolename,
                PolicyName=policy)

        client.delete_role(RoleName=rolename)

    def importvm(self, bucket, key):
        """
        Imports the VM from the bucket/key
        """
        rolename = None
        try:
            rolename = self.createrole(bucket)
            boto3.setup_default_session(profile_name=self.profile)
            ec2 = boto3.client('ec2')
            response = ec2.import_image(
                Description='Import OVA',
                DiskContainers=[{
                    'Description': 'Oracle Linux',
                    'Format': 'ova',
                    'UserBucket': {
                        'S3Bucket': bucket,
                        'S3Key': key
                    },
                }],
                RoleName=rolename)
            taskid = response["ImportTaskId"]
            status = "new"
            ami = "None"
            plot = ""
            while status != 'completed':
                response = ec2.describe_import_image_tasks(ImportTaskIds=[taskid])

                try:
                    ami = response["ImportImageTasks"][0]["ImageId"]
                except KeyError:
                    ami = "undefined"

                try:
                    progress = response["ImportImageTasks"][0]["Progress"]
                except KeyError:
                    progress = "100"

                try:
                    status = response["ImportImageTasks"][0]["StatusMessage"]
                except KeyError:
                    status = 'completed'

                sys.stdout.write(
                    "\r                                             " +
                    "                                               ")
                sys.stdout.write("\rImporting %s (%s) (%s%%) - %s%s" % (
                    ami, taskid, progress, status, plot))
                time.sleep(5)

                plot = plot + "."
                if plot == ".....":
                    plot = ""

            sys.stdout.write("\n")

            self.deleterole()
        except Exception:
            if rolename:
                self.deleterole()
            raise


def main():
    """
    main: examines call and perform the upload/VM import
    """
    profile = "default"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvf:b:p:k", [
            "help", "verbose", "file=", "bucket=", "keep", "profile="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    filename = "dist/localhost/localhost.ova"
    bucket = "resetlogs"
    keep = False

    for opt, arg in opts:
        if opt == "-v":
            pass
        elif opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-f", "--file"):
            filename = arg
        elif opt in ("-b", "--bucket"):
            bucket = arg
        elif opt in ("-k", "--keep"):
            keep = True
        elif opt in ("-p", "--profile"):
            profile = arg
        else:
            assert False

    pid = os.getpid()
    os.environ["PID"] = str(pid)

    importova = ImportOVA(profile)
    key = importova.key+'/vm.ova'

    boto3.setup_default_session(profile_name=profile)
    client = boto3.client('s3')
    if os.path.exists(filename):
        key = str(binascii.b2a_hex(os.urandom(6)))
        transfer = S3Transfer(client)
        transfer.upload_file(filename, bucket, key,
                             callback=ProgressPercentage(filename))
    else:
        print("Error: "+filename+" does not exist")

    importova.importvm(bucket, key)

    if not keep:
        client.delete_object(
            Bucket=bucket,
            Key=key)

if __name__ == "__main__":
    main()

