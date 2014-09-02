#!/usr/bin/python
#  Copyright (c) 2014. Florian Mahon <florian@faivre-et-mahon.ch>
#
#  This file is part of backup-website.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details. You should have received a
#  copy of the GNU General Public License along with this program.
#  If not, see <http://www.gnu.org/licenses/>.

import sys
import subprocess
import os
import time
import shutil
import tarfile
import json

MYSQLDUMP = "mysqldump"

__author__ = 'florian@faivre-et-mahon.ch'

def main():
    checkCommandLineInstalled(MYSQLDUMP)
    with open(os.getenv('HOME')+'/.bckst/config.json', 'r') as infile:
        configuration = json.load(infile)
        infile.close()

    current_directory = os.getcwd()
    for site in configuration['sites']:
        backup_site(configuration['destination'], site)

    os.chdir(current_directory)


def backup_site(dest, site):
    print('create working directory')
    working_diretory = create_working_directory_and_remove_old(dest, site)

    print('backup file')
    create_tar_with_filedata(site, working_diretory)

    print('dumb databases')
    dump_database(site['databases'], working_diretory)

    with open(working_diretory+'/manifest.json', 'w') as outfile:
        json.dump(site, outfile, sort_keys=True, indent=4, ensure_ascii=False)
        outfile.close()

    print('build finaly tarfile')
    for root, dirs, files in os.walk(working_diretory):
        tar = tarfile.open(dest + '/'+buildtime()+'-bck-'+site['name']+'.tar.gz', 'w:gz')
        for name in files:
            print("- add file "+name)
            tar.add(working_diretory+'/'+name, arcname=name)
        tar.close()

    shutil.rmtree(path=working_diretory)

def create_working_directory_and_remove_old(dest, site):
    working_diretory = dest + '/' + buildtime() + '-' + site['name']
    try:
        shutil.rmtree(working_diretory)
    except:
        pass
    os.makedirs(working_diretory)

    return working_diretory

def dump_database(dbs, directory):
    for db in dbs:
        fd = open(directory+'/'+db['name']+'.sql', 'w+')
        subprocess.Popen([MYSQLDUMP,
                        '--user='+db['user'],
                        '--password='+db['pass'],
                        '--host='+db['host'],
                        db['name']], stdout=fd).communicate()
        fd.close()

def create_tar_with_filedata(site, working_diretory):
    tar_filename = working_diretory + '/' + site['name'] + '.tar.gz'
    tar = tarfile.open(tar_filename, 'w:gz')
    try:
        tar.add(site['file_location'], arcname='')
    except:
        pass
    tar.close()


def buildtime():
    return time.strftime('%Y%m%d-%H%M%S', time.gmtime())

def checkCommandLineInstalled(name):
    result = True
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            result = False
        else:
            raise
    if not result:
        print("please install " + name)
        sys.exit(-1)


if __name__ == '__main__':
    main()
