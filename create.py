#!/usr/bin/python3

import os
import common
import requests

conf = common.conf

luks_part = None
luks_part_name = None
enc_vol_name = None

# Check connection
try:
    requests.head("http://www.google.com/", timeout=1)
except requests.ConnectionError:
    raise Exception("No internet connection")

# Check EFI
if not os.path.isdir(common.efi):
    if input("Computer is not started with UEFI do you want to continue: (y/n default: n)") != 'y':
        exit()

# Set ntp
os.system('timedatectl set-ntp true')
os.system(f'timedatectl set-timezone {conf["timezone"]}')

installation_files = []

for file in os.listdir(common.package_path):
    file = common.package_path + file
    if os.path.isfile(file) and file.endswith(".apkgi"):
        installation_files.append(file)

base = installation_files.pop(installation_files.index(common.package_path + "base.apkgi"))

with open(common.package_path + 'base.apkgi', 'r') as f:
    base_pkgs = ''.join(x[1] + ' ' for x in common.read_pkg_file(f))
print(os.system('fdisk -l'))
if input("Do you want to create your own disk layout? (y/n default: n): ") != 'y':
    print("Info: ")
    print(common.encrypted_disk_msg)
    print("Steps: ")
    print("1) Select Disk")
    print("2) Create partition for encrypted LUKS")
    print("3) Create boot partition (200MiB)")
    os.system('fdisk ' + input('Enter disk: '))
    os.system('clear')
    print(os.system('fdisk -l'))
    luks_part = input("Enter LUKS partition (ex. /dev/sda2): ")
    boot_part = input("Enter Boot partition (ex. /dev/sda1): ")
    luks_part_name = input("Enter the name for LUKS partition (ex. cryptlvm): ")
    enc_vol_name = input("Enter the name for LVM group (ex. MyVolGroup): ")
    os.system('cryptsetup luksFormat ' + luks_part)
    os.system(f'cryptsetup open {luks_part} {luks_part_name}')
    os.system(f'pvcreate /dev/mapper/{luks_part_name}')
    os.system(f'vgcreate {enc_vol_name} /dev/mapper/{luks_part_name}')
    os.system('vgdisplay')
    size_root = input("Enter size of root (ex. 100G, see lvcreate): ")
    size_home = input("Enter size of home (ex. 100%FREE): ")
    os.system(f'lvcreate -L {size_root} {enc_vol_name} -n root')
    os.system(f'lvcreate -L {size_home} {enc_vol_name} -n home')
    os.system(f'mkfs.ext4 /dev/{enc_vol_name}/root')
    os.system(f'mkfs.ext4 /dev/{enc_vol_name}/home')
    os.system(f'mount /dev/{enc_vol_name}/root /mnt')
    os.system(f'mount --mkdir /dev/{enc_vol_name}/home /mnt/home')
    os.system(f'mkfs.fat -F32 {boot_part}')
    os.system(f'mount --mkdir {boot_part} /mnt/boot')
else:
    print("Steps: ")
    print("1) Create partitions")
    print("2) Format partitions")
    print("2) Mount partitions root -> /mnt")
    print("3) exit")
    os.system('bash')
    print(os.system('fdisk -l'))

os.system('pacman -Sy')
os.system('pacman -S reflector --noconfirm')
os.system('reflector --latest 5 --sort rate --protocol https --save /etc/pacman.d/mirrorlist')
os.system(f'pacstrap /mnt {base_pkgs}')
os.system('genfstab -U /mnt >> /mnt/etc/fstab')
os.system(f'echo "luks_part = {luks_part}" >> arch.conf')
os.system(f'echo "luks_part_name = {luks_part_name}" >> arch.conf')
os.system(f'echo "enc_vol_name = {enc_vol_name}" >> arch.conf')
os.system('mkdir /mnt/opt/arch-installation')
os.system('cp .* /mnt/opt/arch-installation')
os.system('arch-chroot /mnt')
