#!/usr/bin/env python3
#
# Downloads all daca2 source code packages.
#
# Usage:
# $ ./daca2_download.py


import argparse
import glob
import os
import shutil
import stat
import subprocess
import sys
import time

from daca2_getpackages import getpackages
import donate_cpu_lib as lib


def handleRemoveReadonly(func, path, exc):
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)


def removeAll():
    count = 5
    while count > 0:
        count -= 1

        filenames = []
        filenames.extend(glob.glob('[#_A-Za-z0-9]*'))
        filenames.extend(glob.glob('.[A-Za-z]*'))

        try:
            for filename in filenames:
                if os.path.isdir(filename):
                    # pylint: disable=deprecated-argument - FIXME: onerror was deprecated in Python 3.12
                    shutil.rmtree(filename, onerror=handleRemoveReadonly)
                else:
                    os.remove(filename)
        # pylint: disable=undefined-variable
        except WindowsError as err:
            time.sleep(30)
            if count == 0:
                print('Failed to cleanup files/folders')
                print(err)
                sys.exit(1)
            continue
        except OSError as err:
            time.sleep(30)
            if count == 0:
                print('Failed to cleanup files/folders')
                print(err)
                sys.exit(1)
            continue
        count = 0


def accept_filename(filename:str, accept_proto: bool = False):
    if '.' not in filename:
        return False
    ext = filename[filename.rfind('.'):]
    if ext == '.proto' and accept_proto:
        return True
    return ext in ('.C', '.c', '.H', '.h', '.cc',
                   '.cpp', '.cxx', '.c++', '.hpp', '.tpp', '.t++')


def removeLargeFiles(path, accept_proto: bool = False):
    for g in glob.glob(path + '*'):
        if g == '.' or g == '..':
            continue
        if os.path.islink(g):
            continue
        if os.path.isdir(g):
            removeLargeFiles(g + '/', accept_proto)
        elif os.path.isfile(g):
            # remove large files
            statinfo = os.stat(g)
            if statinfo.st_size > 100000:
                os.remove(g)

            # remove non-source files
            elif not accept_filename(g, accept_proto):
                os.remove(g)


def downloadpackage(filepath, outpath, accept_proto: bool = False):
    # remove all files/folders
    removeAll()

    if not lib.download_package('.', filepath, None):
        print('Failed to download ' + filepath)
        return

    filename = filepath[filepath.rfind('/') + 1:]
    if filename.endswith('.gz'):
        subprocess.check_call(['tar', 'xzf', filename])
    elif filename.endswith('.xz'):
        subprocess.check_call(['tar', 'xJf', filename])
    elif filename.endswith('.bz2'):
        subprocess.check_call(['tar', 'xjf', filename])
    else:
        return

    removeLargeFiles('', accept_proto)

    for g in glob.glob('[#_A-Za-z0-9]*'):
        if os.path.isdir(g):
            subprocess.check_call(['tar', '-cJf', os.path.join(outpath, filename[:filename.rfind('.')] + '.xz'), g])
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloads all daca2 source code packages.')
    parser.add_argument('--outdir', default='~/daca2-packages/', help='output directory for downloaded packages')
    parser.add_argument('--protobuf', action='store_true', help='also download .proto files')
    args = parser.parse_args()

    workdir = os.path.expanduser(os.path.join(args.outdir, 'tmp/'))
    if not os.path.isdir(workdir):
        os.makedirs(workdir)
    os.chdir(workdir)

    try:
        packages = getpackages()
    except (RuntimeError, subprocess.CalledProcessError) as e:
        print(e)
        sys.exit(1)

    for package in packages:
        downloadpackage(package, os.path.expanduser(args.outdir), args.protobuf)

    # remove all files/folders
    removeAll()


