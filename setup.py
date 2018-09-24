#!/usr/bin/env python
from setuptools import setup
import setuptools


setuptools.setup(
  name             = "WxChallenge",
  description      = "For parsing WxChallenge data for grading",
  url              = "https://github.com/kwodzicki/WxChallenge",
  author           = "Kyle R. Wodzicki",
  author_email     = "krwodzicki@gmail.com",
  version          = "0.1.2",
  packages         = setuptools.find_packages(),
  install_requires = [ "bs4", "numpy", "pandas", "xlwt" ],
  scripts          = ['bin/WxChall_Daily_Update'],
  zip_safe = False
);
