#!/usr/bin/python3

import os
import requests

with open('arch.conf', 'r') as f:
    conf = {}
    for line in f:
        if not line.startswith('#'):
            line = line.split('=')
            if len(line) == 2:
                conf[line[0].strip()] = line[1].strip()

efi = '/sys/firmware/efi/efivars'
package_path = os.curdir + '/packages/'
tmpfs = """
tmpfs	/tmp	tmpfs	defaults,noatime,mode=1777	0	0
"""
encrypted_disk_msg = """
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
hooks = '(base udev autodetect modconf block filesystems keyboard keymap encrypt lvm2 fsck)'
hosts = f"""
127.0.0.1        localhost
::1              localhost
127.0.1.1        {conf['hostname']}
"""
luks_part = None
luks_part_name = None
enc_vol_name = None


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
os.system(f'timedatectl set-timezone {conf["timezone"]}')

installation_files = []

for file in os.listdir(package_path):
    file = package_path + file
    if os.path.isfile(file) and file.endswith(".apkgi"):
        installation_files.append(file)

base = installation_files.pop(installation_files.index(package_path + "base.apkgi"))

with open(package_path + 'base.apkgi', 'r') as f:
    base_pkgs = ''.join(x[1] + ' ' for x in read_pkg_file(f))
print(os.system('fdisk -l'))
if input("Do you want to create your own disk layout? (y/n default: n): ") != 'y':
    print("Info: ")
    print(encrypted_disk_msg)
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
os.system('arch-chroot /mnt')
os.system('bash')
os.system(f'ln -sf /usr/share/zoneinfo/{conf["timezone"]} /etc/localtime')
os.system('hwclock --systohc')
for i in conf['locales'].split(', '):
    os.system(f'echo {i} >> /etc/locale.gen')
os.system('locale-gen')
os.system(f'echo "LANG={conf["lang"]}" >> /etc/locale.conf')
os.system(f'echo "LANGUAGE={conf["language"]}" >> /etc/locale.conf')
os.system('echo "LC_ALL=C" >> /etc/locale.conf')
os.system(f'echo "KEYMAP={conf["keymap"]}" >> /etc/vconsole.conf')
os.system(f'echo "{conf["hostname"]}" >> /etc/hostname')
os.system(f'echo "{hosts}" >> /etc/hosts')
os.system(f'echo "{tmpfs}" >> /etc/fstab')
os.system('passwd')
os.system(f'useradd -m -G wheel -s /bin/zsh {conf["user"]}')
os.system('grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB')

if not luks_part:
    luks_part = input("Enter encrypted disk (ex. /dev/sda3, Enter for none): ")
if luks_part:
    if not luks_part_name:
        luks_part_name = input("Enter encrypted disk (ex. cryptLVM): ")
    if not enc_vol_name:
        enc_vol_name = input("Enter LVM path (ex. /dev/MyVolGroup/root): ")
    if luks_part_name and enc_vol_name:
        os.system('sed - i \'/^'"HOOKS"'/d\' /etc/mkinitcpio.conf')
        os.system(f'echo "HOOKS={hooks}" >> /etc/mkinitcpio.conf')
        os.system('mkinitcpio -P')
        os.system('sed - i \'/^'"GRUB_CMDLINE_LINUX"'/d\' /etc/default/grub')
        os.system(f'echo "GRUB_CMDLINE_LINUX="cryptdevice={luks_part}:{luks_part_name} root=/dev/{enc_vol_name}/root"" >> /etc/default/grub')
os.system('grub-mkconfig -o /boot/grub/grub.cfg')
os.system('exit')
os.system('umount -R /mnt')
os.system('reboot')
