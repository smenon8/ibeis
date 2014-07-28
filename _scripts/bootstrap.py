#!/usr/bin/env python2.7
"""
git config --global push.default current
export CODE_DIR=~/code
mkdir $CODE_DIR
cd $CODE_DIR
git clone https://github.com/Erotemic/ibeis.git
cd ibeis
./_scripts/bootstrap.py
./_scripts/__install_prereqs__.sh
./super_setup.py --build --develop
./super_setup.py --build --develop
"""
import sys
import os
from os.path import dirname, realpath, join
from util_cplat_packages import make_prereq_script, APPLE, CENTOS, DEBIAN_FAMILY, print_sysinfo

DRYRUN = '--dry' in sys.argv or '--dryrun' in sys.argv

PREREQ_PKG_LIST = [
    'git',
    'gcc',  # need a C compiler for numpy
    'g++',
    'gfortran',  # need a fortran compiler for numpy (avoid mixing g77 and gfortran!)
    'cmake',
    'ffmpeg',  # need -dev / -devel versions of all these as well
    'libpng',
    'libjpg',
    'libtiff',
    'littlecms',
    'openjpeg',
    'jasper',
    'zlib',
    'freetype',
    'fftw3',
    'atlas',
    #'zmq',
    #libgeos-dev
]
#http://sourceforge.net/projects/matplotlib/files/matplotlib-toolkits/
'''
# Install mpl_toolkits.basemap
sudo apt-get install libgeos-dev -y
cd ~/tmp
wget http://downloads.sourceforge.net/project/matplotlib/matplotlib-toolkits/basemap-1.0.7/basemap-1.0.7.tar.gz
gunzip -c basemap-1.0.7.tar.gz | tar xvf -
cd basemap-1.0.7
sudo checkinstall sudo python setup.py install
python -c "from mpl_toolkits.basemap import Basemap"
'''

if APPLE:
    PREREQ_PKG_LIST.extend([
        'opencv',
        'libpng',
        'zlib',
        'freetype',
    ])

if DEBIAN_FAMILY:
    PREREQ_PKG_LIST.extend([
        'libfftw3-dev',
        #'libeigen3-dev',
        'libatlas-base-dev',  # ATLAS for numpy no UBUNTU
        #'libatlas3gf-sse2',  # ATLAS SSE2 for numpy no UBUNTU
        'libfreetype6-dev',  # for matplotlib
        #'libpng12-dev',
        #'libjpeg-dev',
        #'zlib1g-dev',
        'python-dev',
        'libopencv-dev',
        'python-opencv',
    ])

if CENTOS:
    pass

PREREQ_PYPKG_LIST = [
    'pip',
    'setuptools',
    'Pygments',
    'Cython'
    'requests',
    'colorama',
    'psutil',
    'functools32',
    'six',
    'dateutils',
    'pyreadline',
    'pyparsing',
    'sip',
    'pyqt4',
    'Pillow',
    'numpy',
    'scipy',
    'ipython',
    'tornado',
    'matplotlib',
    'scikit-learn',
    #'pandas',
    #'openpyxl',
    #'pyzmq',
]

# Need to do a distribute upgrade before matplotlib on Ubuntu?
# not sure if that will work yet

print_sysinfo()
#upgrade()
output = make_prereq_script(PREREQ_PKG_LIST, PREREQ_PYPKG_LIST)
if output == '':
    print('System has all prerequisites!')
elif not DRYRUN:
    script_dir = realpath(dirname(__file__))
    fpath = join(script_dir, '__install_prereqs__.sh')
    with open(fpath, 'w') as file_:
        file_.write(output)
    os.system('chmod +x ' + fpath)
    print('# wrote: %r' % fpath)
    #sudo python super_setup.py --build --develop


"""

python -c
sudo apt-get remove python-pip
sudo apt-get remove python-setuptools
sudo apt-get remove python-numpy
sudo apt-get remove python-scipy
sudo pip install numpy --upgrade
sudo pip install scipy --upgrade


# sudo pip install distribute --upgrade
sudo pip remove PIL
sudo pip remove pillow
sudo pip install pillow

"""
