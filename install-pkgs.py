#!/usr/bin/python
import os

import common

installation_files = []

for file in os.listdir(common.package_path):
    file = common.package_path + file
    if os.path.isfile(file) and file.endswith(".apkgi"):
        installation_files.append(file)

base = installation_files.pop(installation_files.index(common.package_path + "base.apkgi"))

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
print(" ".join(pkgs_pm))
input("Install...")
os.system(f'pacman -S {" ".join(pkgs_pm)}')

old_path = os.getcwd()
os.mkdir('/opt/aur')
os.system(f'chown -R {common.conf["user"]} /opt/aur')
os.chdir('/opt/aur')
for pkg in pkgs_aur:
    common.install_aur_package(pkg)
os.chdir(old_path)