#!/usr/bin/python3

import os
import common

conf = common.conf
luks_part = conf['luks_part']
luks_part_name = conf['luks_part_name']
enc_vol_name = conf['enc_vol_name']

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
os.system(f'echo "{common.hosts}" >> /etc/hosts')
os.system(f'echo "{common.tmpfs}" >> /etc/fstab')
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
        os.system(f'echo "HOOKS={common.hooks}" >> /etc/mkinitcpio.conf')
        os.system('mkinitcpio -P')
        os.system('sed - i \'/^'"GRUB_CMDLINE_LINUX"'/d\' /etc/default/grub')
        os.system(f'echo "GRUB_CMDLINE_LINUX="cryptdevice={luks_part}:{luks_part_name} root=/dev/{enc_vol_name}/root"" >> /etc/default/grub')
os.system('grub-mkconfig -o /boot/grub/grub.cfg')
os.system('exit')
os.system('umount -R /mnt')
os.system('reboot')
