from bs4 import BeautifulSoup;
import numpy as np;
# from time import sleep;
# from random import random;

# Handle both Python2 and Python3
try:
  from urllib import urlopen;
except:
  from urllib.request import urlopen;

################################################################################
def getSemester( date ):
  return 'spring' if date.month < 8 else 'fall';

################################################################################
def updateSchedule( sched, info ):
  '''
  sched is a dictionary and info is a 5-element list (or tuple)
  containing (in order) [city, state, identifier, start date, end date]
  start date and end date are datetime instances!
  '''
  sem     = getSemester( info['end'] )
  semYear = '{}:{}'.format(sem, info['end'].year)
  if semYear not in sched: sched[semYear] = {};
  sched[semYear][info['ident']] = info;
  return sched;

################################################################################
def checkURL(url):
  '''Method to check if url exists'''
  try:                                                                          # Try to...
    req = urlopen(url);                                                         # Open the url
  except:                                                                       # On exception...
    return False;                                                               # Return False
  if req.getcode() != 200: return False;                                        # If the code does NOT equal 200, then return False
  try:                                                                          # Try to...
    data = req.read();                                                          # Read the data from the website
  except:                                                                       # On exception...
    return False;                                                               # Return False
  req.close();                                                                  # Close the request
  return BeautifulSoup(data, 'lxml');                                           # Parse the html data using the lxml format?

################################################################################
def nestedDictSort( input ):
  try:
    for k, v in input.iteritems():
      if isinstance(v, dict):
        nestedDictSort( v );
      else:
        input[k] = [x for _,x in sorted(zip(input['date'], v))];
  except:
    for k, v in input.items():
      if isinstance(v, dict):
        nestedDictSort( v );
      else:
        input[k] = [x for _,x in sorted(zip(input['date'], v))];
  return input

def padReshape( input ):
  input = np.array(input);
  if (input.size % 8) != 0:
    input = np.pad(input, (0, 8-(input.size % 8),), 'constant')
  return np.reshape( input, (8, input.size//8,), order='f' );

def scoring( fcs, verbose = False ):
  '''
  Function for calculating score for the competition
  Inputs:
    fcs   : Must be a dictionary returned by get_forecasts method of
             WxChall_SQLite. SHOULD ONLY CONTAIN ONE SEMESTER OF DATA.
  '''
  if 'CLIMO0' in fcs['xxx'][8] and 'CLIMO_' in fcs['xxx'][8]:                   # If both climatologies are present
    climo = np.array( [fcs['xxx'][8]['CLIMO0']['err_total'], 
                       fcs['xxx'][8]['CLIMO_']['err_total']] ).max(axis=0);     # Use the maximum value between the two; help the students
  elif 'CLIMO0' in fcs['xxx'][8] and 'CLIMO_' not in fcs['xxx'][8]:             # If only one climo present
    climo = np.array( fcs['xxx'][8]['CLIMO0']['err_total'] );                   # Use the climo
  elif 'CLIMO0' not in fcs['xxx'][8] and 'CLIMO_' in fcs['xxx'][8]:             # If only one climo present
    climo = np.array( fcs['xxx'][8]['CLIMO_']['err_total'] );                   # Use the climo
  else:                                                                         # Else
    climo = None;                                                               # Set climo to None;
  
  climo = padReshape( climo );                                                  # Pad and reshape the climatology
  first = True;
  for sch in fcs:                                                               # Iterate over all schools in the fcs dictionary
    if sch == 'xxx': continue;                                                  # Skip xxx school
    for cat in fcs[sch]:                                                        # Iterate over categories
      for name in fcs[sch][cat]:                                                # Iterate over names
        tmp    = fcs[sch][cat][name];                                           # Temporary data for school, category, forecaster
        if first and verbose:
          seen = set()
          seen_add = seen.add
          sites = [x for x in tmp['identifier'] if not (x in seen or seen_add(x))]
          text  = ['{:6}'.format(s) for s in sites]
          text  = ['Forecaster'] + text + ['{:6}'.format('Avg.')]
          print(  ' '.join( text ) );
          first = False;
        err    = padReshape( tmp['err_total'] );                                # Pad and reshape the forecaster error points
        missed = padReshape( [t != '' for t in tmp['type']] );                  # Pad and reshape the missed forecast flag; missed is either climo (C) or guidance (G); i.e., not ''
        score  = 100 - np.clip(missed.sum(axis=0)-2, 0, None)*14.286;           # Compute score for missing; give them 2 free misses a week, after that subtract 14.286 (1/7th of 100) for every missed day
        if climo is not None: 
          score -= ((err > climo) & (missed == 0)).sum(axis=0)*6;       # If climo is set, determine number of times that forecaster actually forecasted (missed == 0) and did NOT beat climo; multiply this number by 6 and subtract from score

        tmp['score'] = score;                                                   # Append the score to the forecaster dictionary
        if verbose: 
          text = ['{:6.2f}'.format(s) for s in score]
          text = ['{:10}'.format(name)] + text + ['{:6.2f}'.format(score.mean())]
          print( ' '.join( text ) );
  return fcs;