#!/usr/bin/python3

import os
import requests

efi = '/sys/firmware/efi/efivars'
package_path = os.curdir + '/packages/'
luks_part_name = 'cryptLVM'
enc_vol_name = 'archVG'
encrypted_disk = """
+-----------------------------------------------------------------------+ +----------------+
| Logical volume 1      | Logical volume 2      | Logical volume 3      | | Boot partition |
|                       |                       |                       | |                |
| [SWAP]                | /                     | /home                 | | /boot          |
|                       |                       |                       | | 200MiB         |
| /dev/MyVolGroup/swap  | /dev/MyVolGroup/root  | /dev/MyVolGroup/home  | |                |
|_ _ _ _ _ _ _ _ _ _ _ _|_ _ _ _ _ _ _ _ _ _ _ _|_ _ _ _ _ _ _ _ _ _ _ _| | (may be on     |
|                                                                       | | other device)  |
|                         LUKS2 encrypted partition                     | |                |
|                           /dev/sda1                                   | | /dev/sdb1      |
+-----------------------------------------------------------------------+ +----------------+
"""


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
if input("Do you want to create your own disk layout? (y/n default: n): ") != 'y':
    print("Info: ")
    print(encrypted_disk)
    print("Steps: ")
    print("1) Select Disk")
    print("2) Create partition for encrypted LUKS")
    print("3) Create boot partition (200MiB)")
    os.system('fdisk ' + input('Enter disk: '))
    os.system('clear')
    print(os.system('fdisk -l'))
    luks_part = input("Enter LUKS partition: ")
    boot_part = input("Enter Boot partition: ")
    os.system('cryptsetup luksFormat ' + luks_part)
    os.system(f'cryptsetup open {luks_part} {luks_part_name}')
    os.system(f'pvcreate /dev/mapper/{luks_part_name}')
    os.system(f'vgcreate {enc_vol_name} /dev/mapper/{luks_part_name}')
else:
    print("Steps: ")
    print("1) Create partitions")
    print("2) Format partitions")
    print("3) exit")
    os.system('bash')
    print(os.system('fdisk -l'))
