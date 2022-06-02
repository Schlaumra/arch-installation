import os

with open('arch.conf', 'r') as f:
    conf = {}
    for line in f:
        if not line.startswith('#'):
            line = line.split('=')
            if len(line) == 2:
                conf[line[0].strip()] = line[1].strip()

hosts = f"""
127.0.0.1        localhost
::1              localhost
127.0.1.1        {conf['hostname']}
"""

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


def read_pkg_file(f):
    for line in f:
        line = line.lstrip()
        if not line.startswith("#"):
            line = line.strip()
            pkg = line.split()
            if len(pkg) == 2:
                yield pkg


def install_aur_package(pkg_name):
    os.system(f'git clone https://aur.archlinux.org/{pkg_name}.git')
    os.chdir(pkg_name)
    os.system(f'sudo -u {conf["user"]} makepkg -si')
