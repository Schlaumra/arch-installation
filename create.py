#!/usr/bin/python3

import os
import requests

efi = '/sys/firmware/efi/efivars'
package_path = '/packages'

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

print(os.curdir + package_path)
exit()
for file in os.listdir(os.curdir + package_path):
    if os.path.isfile(file) and file.endswith(".apkgi"):
        installation_files.append(file)

base = installation_files.pop(installation_files.index("base.apkgi"))

with open('packages/base.apkgi', 'r') as f:
    for line in f:
        line = line.strip()
        print("line", line)
        pkg = line.split("\t")
        print("srcpkg", pkg)
