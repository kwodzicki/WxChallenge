#!/usr/bin/env python
import os, shutil, sys, importlib
from setuptools import setup, find_packages;
from setuptools.command.install import install
from distutils.util import convert_path

pkg_name = "WxChallenge";
pkg_desc = "For parsing WxChallenge data for grading";
pkg_url  = "https://github.com/kwodzicki/WxChallenge";
sqlFile  = "WxChall.sql"
userHome = os.path.expanduser('~');

main_ns  = {};
ver_path = convert_path("{}/version.py".format(pkg_name));
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns);

"""sys.path.pop(0);                                                                # Pop off current directory from path
pkg_info = importlib.util.find_spec( pkg_name );                                # Look for the package; may be installed
if pkg_info:                                                                    # If the package is found
  pkg_dir = os.path.dirname( pkg_info.origin );                                 # Current package directory
  sqlPath = os.path.join( pkg_dir, sqlFile );                                   # Get current .sql file location
  if os.path.isfile( sqlPath ):                                                 # If the SQL file exists
    os.rename( sqlPath, os.path.join( userHome, sqlFile ) );                    # Move the file to the user's home directory

class CustomInstall( install ):
  def _post_install( self ):
    '''
    Purpose:
      Post-installation method for keeping config settings
    Inputs:
      None
    '''
    def find_module_path():
      '''Local function for determining package installation directory'''
      for p in sys.path:                                                        # Iterate over all system paths
        if os.path.isdir(p) and pkg_name in os.listdir(p):                      # If the path is a directory and the package name is in the directory list
          print(p, pkg_name)
          return os.path.join(p, pkg_name);                                     # Return path to package
    install_path = find_module_path();                                          # Find the package path
    sqlPath = os.path.join( userHome, sqlFile );                                # Path of backed up SQL file
    if os.path.isfile( sqlPath ):                                               # If the temprorary config file exists
      os.rename( sqlPath, os.path.join( install_path, sqlFile ) );              # Move file to package location
  def run( self ):
    install.run( self );
    self._post_install();
"""
  
setup(
  name                 = pkg_name,
  description          = pkg_desc,
  url                  = pkg_url,
  author               = "Kyle R. Wodzicki",
  author_email         = "krwodzicki@gmail.com",
  version              = main_ns['__version__'],
  packages             = setuptools.find_packages(),
  install_requires     = [ "bs4", "lxml", "numpy", "scipy", "pandas", "openpyxl" ],
  scripts              = ['bin/WxChall_Daily_Update',
                          'bin/WxChall_Semester_Update',
                          'bin/WxChall_Grades'],
  package_data         = {'WxChallenge' : [ sqlFile ]},
  include_package_date = True,
  zip_safe             = False,
);
