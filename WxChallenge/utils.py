import os
import datetime

import numpy as np
from bs4 import BeautifulSoup

from urllib.request import urlopen

from .roster import fix_Roster_CSV

################################################################################
def getSemester( date ):
  return 'spring' if date.month < 8 else 'fall';

################################################################################
def generateKey( date ):
  sem = getSemester( date );
  return '{}:{}'.format(sem, date.year);
  
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
  '''
  Function to sort lists at the bottom of nested dictionaries
  '''
  try:                                                                          # Try to (for python2)
    for k, v in input.iteritems():                                              # Iterate over the key, value pairs in the input dictionary
      if isinstance(v, dict):                                                   # If the value is a dictionary instance
        nestedDictSort( v );                                                    # Call the function again on v
      else:                                                                     # Else, reached the bottom of the nesting
        input[k] = [x for _,x in sorted(zip(input['date'], v))];                # Sort the list based on the 'date' key that (should) be in the dictionary
  except:                                                                       # On exception (python3)
    for k, v in input.items():                                                  # Iterate over the key, value pairs in the input dictionary
      if isinstance(v, dict):                                                   # If the value is a dictionary instance
        nestedDictSort( v );                                                    # Call the function again on v
      else:                                                                     # Else, reached the bottom of the nesting
        input[k] = [x for _,x in sorted(zip(input['date'], v))];                # Sort the list based on the 'date' key that (should) be in the dictionary
  return input                                                                  # Return the dictionary

################################################################################
def unique_cols( input ):
  '''
  Function to get unique values from nested list of values
  '''
  out, seen = [], set();                                                        # Initialize out list and seen set
  seen_add = seen.add;                                                          # Set seen_add to add method of seen set; supposed to be faster
  types = [type(i) for i in input[0]];                                          # Get type of each 'column' in the input 
  for i in input:                                                               # Iterate over all lists in the input list
    tag = ':'.join( [str(j) for j in i] );                                      # Convert all values to string and join on colon
    if not (tag in seen or seen_add(tag)): out.append(tag);                     # If the value is NOT in seen set, then append to out
  return [ [t(j) for t, j in zip(types, i.split(':'))] for i in out];           # Split joined strings and convert back to original type and return result

################################################################################
def padReshape( input ):
  '''
  Function to pad and reshape data arrays so that there are 8 rows by
  n cities for the forecasts
  '''
  input = np.array(input);                                                      # Ensure that input is a numpy array
  if (input.size % 8) != 0:                                                     # If the input array does NOT have a length that is a multiple of 8
    input = np.pad(input, (0, 8-(input.size % 8),), 'constant');                # Pad the end of the array so that it IS a multiple of 8
  return np.reshape( input, (input.size//8, 8,) );                              # Reshape into an (8, ncity) array in fortran order

################################################################################
def tally_classes( filename ):
  '''
  Name:
     tally_classes
  Purpose:
     Function to determine number of, and which people, are in a given
     class based on the CSV roster downloaded from the WxChallenge websit.
  Inputs:
     filename : Full path to the file to reformat
  Outputs:
     Returns a dictionary containing dictionaries for each class, as well as
     all forecasters and all those not in classes, that has the number of
     students in the class and a list of the student names.
  Keywords:
     None.
  Author and history:
     Kyle R. Wodzicki     Created 19 Sep. 2018
  '''
  if not os.path.isfile( filename ): return False;                              # If the file does NOT exist, return false
  build_name = lambda first, last: ', '.join( [last, first] );                  # Lambda function to build the forecaster name
  split_row = lambda row: [i.strip() for i in row.split(',')];                  # Lambda function to split up rows from the CSV file
  
  if not fix_Roster_CSV( filename ):
    print( 'Failed to reformat CSV file!' );
    return False;
  lines    = open(filename, 'r').readlines();                                   # Read in data
  head     = lines.pop(0).split(',');                                           # Pop the header row off the list of lines
  classIDs, fnameID, lnameID = _get_CSV_Indices( head );                        # Determine some indexing variables

  classes = {'No Class' : {'count' : 0, 'students' : []}, 
             'All'      : {'count' : 0, 'students' : []} };                     # Dictionary to store info

  for line in lines:                                                            # Iterate over all lines
    tmp  = split_row( line );                                                   # Split up the row using the lambda function
    name = build_name( tmp[fnameID], tmp[lnameID] );                            # Build student name
    classes['All']['count']    += 1;                                            # Increment student count for 'All' tag
    classes['All']['students'].append( name );                                  # Append student name to the students list
    if sum( ['no class' in i.lower() for i in tmp] ) == len(classIDs):          # If all class ID fields are empty
      classes['No Class']['count']    += 1;                                     # Increment student count for 'No Class' tag
      classes['No Class']['students'].append( name );                           # Append student name to the students list
    else:                                                                       # Else, student is in at least one class
      for i in classIDs:                                                        # Iterate over the two class columns
        if 'no class' not in tmp[i].lower():                                    # If 'no class' NOT in the class name, then skip it
          if tmp[i] not in classes:                                             # If the class name is NOT in the classes dictionary
            classes[ tmp[i] ] = {'count' : 1, 'students' : [ name ] };          # Initialize sub dictionary
          else:                                                                 # Else
            classes[ tmp[i] ]['count']    += 1;                                 # Increment student count for the class tag
            classes[ tmp[i] ]['students'].append( name );                       # Append student name to the students list
    for tag in classes: classes[tag]['students'].sort();                        # Sort list of students in each sub-dictionary
  return classes;                                                               # Return the classes dictionaryimport logging


def getMonthInt( month ):
  """Get month integer from month name"""
  try:
    m = datetime.datetime.strptime(month,'%B').month
  except:
    m = datetime.datetime.strptime(month,'%b').month
  return m

def splitCityState(citySt):
  """
  Split City, ST string on comma
  
  Arguments:
    citySt (str) : Contains City, ST information
  
  Keyword arguments:
     None.
  
  Returns:
    tuple : City, state

  """
  citySt = citySt.split(',')
  if len(citySt) >= 2:
    return ','.join( citySt[:-1] ).strip(), citySt[-1].strip()
  return citySt[0].strip(), ''

getTemp = lambda x: int( x.split(u'\xb0')[0][1:] )                              # Lambda function to pull out temperature from string
getWind = lambda x: int( x.split()[0]  )                                                    # Lambda function to pull out wind from string
getPrec = lambda x: float( x.split('"')[0] )                                    # Lambda function to pull out precip from string


