#!/usr/bin/env python

import sqlite3, os;
import numpy as np
from scipy.stats import linregress

from WxChallenge import __file__ as WxFile
_dir = os.path.dirname(os.path.abspath( WxFile ));
_sql_file = os.path.join(_dir, 'WxChall.sql');

roster  = '/Users/kwodzicki/Documents/TAMU/WxChallenge/2018_Fall/roster.csv'

def calcTrends( year, semester, roster ):
  lines   = open(roster,'r').readlines()[1:];
  
  db      = sqlite3.connect( _sql_file, detect_types=sqlite3.PARSE_DECLTYPES );
  cursor  = db.cursor();
  errID   = 17
  dateID  = -5
  
  whr = "SELECT * from forecasts WHERE name='{}' AND semester='{}' AND year={}"
  
  trends = []
  for line in lines:
    vals = line.split(',');
    if vals.count('No Class ID') != 2:
      forecaster = vals[0]
      cmd = whr.format( forecaster, semester, year )
      cursor.execute( cmd );
      data  = cursor.fetchall()
      if len(data) > 0:
        data.sort( key = lambda x: x[dateID] )
        errors = [ fcst[errID] for fcst in data ]
        x = np.arange( len(errors) )
        trends.append( (forecaster, linregress(x, errors), ) )
  cursor.close()
  trends.sort( key = lambda x: x[1].rvalue );
  return trends

def mostImproved( year, semester, roster ):
  lines  = open(roster,'r').readlines()[1:];
  trends = calcTrends( year, semester, roster )
  for trend in trends:
    if (trend[1].slope < 0) and (trend[1].rvalue < 0):
      for line in lines:
        if trend[0] in line:
          return line, trend
  return None

if __name__ == "__main__":
  import sys
  print( mostImproved( int(sys.argv[1]), sys.argv[2], sys.argv[3] ) )