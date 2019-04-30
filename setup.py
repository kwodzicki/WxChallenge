#!/usr/bin/env python
import os, shutil, sys, importlib
from setuptools import setup, find_packages;
from setuptools.command.install import install
from distutils.util import convert_path

pkg_name = "WxChallenge";
pkg_desc = "For parsing WxChallenge data for grading";
pkg_url  = "https://github.com/kwodzicki/WxChallenge";

main_ns  = {};
ver_path = convert_path("{}/version.py".format(pkg_name));
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns);
  
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
  package_data         = {'WxChallenge' : ['WxChall.sql']},
  include_package_date = True,
  zip_safe             = False,
);
