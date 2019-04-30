#!/usr/bin/env python
import setuptools
from distutils.util import convert_path

main_ns  = {};
ver_path = convert_path("video_utils/version.py");
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns);
  
setuptools.setup(
  name                 = "WxChallenge",
  description          = "For parsing WxChallenge data for grading",
  url                  = "https://github.com/kwodzicki/WxChallenge",
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
