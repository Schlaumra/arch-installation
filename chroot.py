#!/usr/bin/python3

import os

os.chdir('/opt/arch-installation/')

import common

conf = common.conf
luks_part = conf['luks_part']
luks_part_name = conf['luks_part_name']
enc_vol_name = conf['enc_vol_name']

installation_files = []


def install_aur_package(pkg_name):
    os.system(f'git clone https://aur.archlinux.org/{pkg_name}.git')
    os.chdir(pkg_name)
    os.system(f'sudo -u {conf["user"]} makepkg -si')


for file in os.listdir(common.package_path):
    file = common.package_path + file
    if os.path.isfile(file) and file.endswith(".apkgi"):
        installation_files.append(file)

base = installation_files.pop(installation_files.index(common.package_path + "base.apkgi"))

os.system(f'ln -sf /usr/share/zoneinfo/{conf["timezone"]} /etc/localtime')
os.system('hwclock --systohc')
for i in conf['locales'].split(', '):
    os.system(f'echo {i} >> /etc/locale.gen')
os.system('locale-gen')
os.system(f'echo "LANG={conf["lang"]}" >> /etc/locale.conf')
os.system(f'echo "LANGUAGE={conf["language"]}" >> /etc/locale.conf')
os.system('echo "LC_ALL=C" >> /etc/locale.conf')
os.system('nano /etc/locale.conf')
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
        os.system('sed -i \'/^'"HOOKS"'/d\' /etc/mkinitcpio.conf')
        os.system(f'echo "HOOKS={common.hooks}" >> /etc/mkinitcpio.conf')
        os.system('mkinitcpio -P')
        uuid = os.popen("blkid -o value -s UUID {luks_part}").read().strip()
        os.system(f'sed -i \'s/.*GRUB_CMDLINE_LINUX_DEFAULT.*/GRUB_CMDLINE_LINUX_DEFAULT="cryptdevice=UUID={uuid}:{luks_part_name} root=\/dev\/{enc_vol_name}\/root loglevel=3 quiet"/\' /etc/default/grub')
        os.system(f'sed -i \'s/.*GRUB_ENABLE_CRYPTODISK.*/GRUB_ENABLE_CRYPTODISK=y/\' /etc/default/grub')
        os.system('nano /etc/mkinitcpio.conf')
        os.system('nano /etc/default/grub')
os.system('grub-mkconfig -o /boot/grub/grub.cfg')
os.system('ls /boot')
os.system('ls /boot/grub')
input("Continue...")
os.system(f'sed -i \'s/.*ParallelDownloads.*/ParallelDownloads = {conf["ParallelDownloads"]}/\' /etc/pacman.conf')
os.system("sed -i 's/#\[multilib\]/\[multilib\]\\nInclude = \/etc\/pacman.d\/mirrorlist/' /etc/pacman.conf")
os.system('nano /etc/pacman.conf')
pkgs_pm = []
pkgs_aur = []
for i in installation_files:
    with open(i, 'r') as f:
        pkgs = common.read_pkg_file(f)
        for pkg in pkgs:
            if pkg[0] == 'PM':
                pkgs_pm.append(pkg[1])
            elif pkg[0] == 'AUR':
                pkgs_aur.append(pkg[1])
os.system('pacman -Syu --noconfirm')
os.system(f'pacman -S {" ".join(pkgs_pm)} --noconfirm')

old_path = os.getcwd()
os.mkdir('/opt/aur')
os.chdir('/opt/aur')
for pkg in pkgs_aur:
    install_aur_package(pkg)
os.chdir(old_path)
