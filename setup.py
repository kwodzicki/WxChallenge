#!/usr/bin/env python
from setuptools import setup
import setuptools


setuptools.setup(
  name                 = "WxChallenge",
  description          = "For parsing WxChallenge data for grading",
  url                  = "https://github.com/kwodzicki/WxChallenge",
  author               = "Kyle R. Wodzicki",
  author_email         = "krwodzicki@gmail.com",
  version              = "0.2.6",
  packages             = setuptools.find_packages(),
  install_requires     = [ "bs4", "lxml", "numpy", "pandas", "openpyxl" ],
  scripts              = ['bin/WxChall_Daily_Update',
                          'bin/WxChall_Semester_Update',
                          'bin/WxChall_Grades'],
  package_data         = {'WxChallenge' : ['WxChall.sql']},
  include_package_date = True,
  zip_safe             = False,
);
