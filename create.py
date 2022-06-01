#!/usr/bin/python3

import os
import requests

efi = '/sys/firmware/efi/efivars'
package_path = os.curdir + '/packages/'


def read_pkg_file(f):
    for line in f:
        line = line.lstrip()
        if not line.startswith("#"):
            line = line.strip()
            pkg = line.split("\t")
            if len(pkg) == 2:
                yield pkg

# Check connection
try:
    requests.head("http://www.google.com/", timeout=1)
except requests.ConnectionError:
    raise Exception("No internet connection")

# Check EFI
if not os.path.isdir(efi):
    if input("Computer is not started with UEFI do you want to continue: (y/n default: n)") != 'y':
        exit()

# Set ntp
os.system('timedatectl set-ntp true')

installation_files = []

for file in os.listdir(package_path):
    file = package_path + file
    if os.path.isfile(file) and file.endswith(".apkgi"):
        installation_files.append(file)

base = installation_files.pop(installation_files.index(package_path + "base.apkgi"))

with open(package_path + 'base.apkgi', 'r') as f:
    print([x for x in read_pkg_file(f)])

print(os.system('fdisk -l'))
os.system('fdisk ' + input('Enter disk'))
