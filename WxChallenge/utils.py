from bs4 import BeautifulSoup;
import numpy as np;
import os;
import xlwt;

# Handle both Python2 and Python3
try:
  from urllib import urlopen;
except:
  from urllib.request import urlopen;


xls_cols = ['ID', 'Day', 'Absent', 'Worse Climo']
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
def _get_CSV_Indices( header ):
  '''
  Name:
     _get_CSV_Indices
  Purpose:
     A function to determine the index location (i.e., which column) of 
     class IDs and first and last names in the WxChallenge CSV file.
  Inputs:
     header  : A string, or list, that contains header information
  Outputs:
     classIDs  : List with all indices for class ID columns
     fnameID   : Index for the column containing first names
     lnameID   : Index for the column containing last names
  Keywords:
     None.
  Author and History:
     Kyle R. Wodzicki     Created 21 Sep. 2018
  '''
  if type(header) is not list: 
    header = header.split(',');
    if len(header) == 1:
      raise Exception('Header is NOT comma separated values OR list of values!');
  
  classIDs, fnameID, lnameID = [], None, None;
  for i in range(len(header)):                                                  # Iterate over all columns in the header
    if 'class' in header[i].lower():                                            # If 'class' is in the header name
      classIDs.append( i );                                                     # Append i to the classIDs list
    elif 'first_name' in header[i].lower():                                     # If 'first_name' is in the header name
      fnameID = i;                                                              # Set index for first name
    elif 'last_name' in header[i].lower():                                      # If 'last_name' is in the header name
      lnameID = i;                                                              # Set index for last name
  if len(classIDs) == 0 and fnameID is None and lnameID is None:
    raise Exception();
  else:
    return classIDs, fnameID, lnameID;

################################################################################
def fix_Roster_CSV( filename ):
  '''
  Name:
     fix_Roster_CSV
  Purpose:
     Function to reformat the 'csv' roster from the WChallenge website.
  Inputs:
     filename : Full path to the file to reformat
  Outputs:
     Fixes formatting within the file; i.e., overwrites the file.
  Keywords:
     None.
  Author and history:
     Kyle R. Wodzicki     Created 18 Sep. 2018
     
     Updated on 21 Sep. 2018 by Kyle R. Wodzicki
       Sorts the rows of the CSV based on last name
  '''
  joinLine = lambda line: '{}\n'.format( ','.join(line) );
  if not os.path.isfile( filename ): return False;                              # If the file does NOT exist, return false
  fid  = open( filename, 'r+' );                                                # Open file in r+ mode
  data = fid.readline();                                                        # Read the first line from the file
  line = fid.tell();                                                            # Get the current position in the file
  fid.seek(0, 2);                                                               # Seek to the end of the file
  if fid.tell() == line:                                                        # If the current position (i.e., the end of the file) is the same as the position after reading a line, then read in all the data and must fix
    fid.seek(0, 0);                                                             # Seek to beginning of file
    head  = data.split()[0].split(',');                                         # First list of values on space split is header, split header on coma 
    nCol  = len(head);                                                          # Number of columns in the data
    data  = data.split(',');                                                    # Split all data on comma
    lines = [];                                                                 # Empty array to store lines; this so can sort by last name
    i     = 0;                                                                  # Counter for the while loop
    while i < len(data):                                                        # While i is less than the length of data
      id  = i+nCol-1;                                                           # Index for last column of row
      tmp = data[ id ].split();                                                 # Split what should be the last column on space; the last column is separated from next row by space
      if len(tmp) == 2:                                                         # If two values obtained from split
        data[ id ] = tmp[0];                                                    # Place the first split value into the last column of the current row
        data.insert( id+1, tmp[1] );                                            # Insert second value of the split into the data list as first value of next row into the data list
      sub = [ val.strip() for val in data[i:i+nCol] ];                          # Iterate over all values from i to i+nCol and strip off any preceding/trailing spaces and save new sub list for the row in sub
      lines.append( sub );                                                      # Join the line on comma, append carriage return, and append to lines list
      i += nCol;                                                                # Increment i by nCol
    classIDs, fnameID, lnameID = _get_CSV_Indices( head );                      # Determine some indexing variables
    lines = sorted( lines[1:], key = lambda val: val[lnameID] );                # Sort the list of lines (in place) by last name
    fid.write( joinLine( head ) );                                              # Write header information to file
    for line in lines: fid.write( joinLine( line ) );                           # Join the sub list using comma, append a return character (\n), and write to the input file
    fid.truncate();
  fid.close();                                                                  # Close the file
  return True;                                                                  # Return True

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
  return classes;                                                               # Return the classes dictionary

################################################################################
def scoring( fcs, verbose = False, spreadsheet = None ):
  '''
  Function for calculating score for the competition
  Inputs:
    fcs   : Must be a dictionary returned by get_forecasts method of
             WxChall_SQLite. SHOULD ONLY CONTAIN ONE SEMESTER OF DATA.
  Keywords:
    verbose:  Set to True to print tables of scores.
    spreadsheet: Set to full path to save spreadsheet to
  '''
  if spreadsheet:
    book = xlwt.Workbook(encoding="utf-8")
  else:
    book = None;

  climo_, climo0 = None, None;
  consen, consen_ntl = None, None;
  for fcster in fcs:                                                            # Iterate over all forecasters in the fcs list
    if fcster.name == 'CLIMO_':                                                 # If forecaster name is CLIMO0
      climo_ = np.array( fcster.err_total );
    elif fcster.name == 'CLIMO0':
      climo0 = np.array( fcster.err_total );
    elif fcster.name == 'CONSEN':
      if fcster.school == 'xxx':
        consen_ntl = np.array( fcster.cum_err_total );
      else:
        consen = np.array( fcster.cum_err_total );
#   return climo_, climo0
  if climo_ is not None and climo0 is not None:                                 # If both climatologies are present
    climo = np.maximum.reduce( [climo_, climo0] );
  elif climo_ is not None:                                                      # If only one climo present
    climo = climo_                                                              # Use the climo
  elif climo0 is not None:                                                      # If only one climo present
    climo = climo0                                                              # Use the climo
  else:                                                                         # Else
    climo = None;                                                               # Set climo to None;

  if climo  is not None:     climo      = padReshape( climo );                                        # If climo is valid, pad and reshape the climatology
  if consen is not None:     consen     = padReshape( consen );
  if consen_ntl is not None: consen_ntl = padReshape( consen_ntl );

  first = True;
  for fcster in fcs:                                                            # Iterate over all forecasters
    if fcster.is_model or fcster.is_consen: continue;                           # If the forecaster is a model or consensus, skip it
    if first:
      first = False;
      seen = set();
      seen_add = seen.add
      sites = [x for x in fcster.identifier if not (x in seen or seen_add(x))]
      if verbose:
        text  = ['{:6}'.format(s) for s in sites]
        text  = ['Forecaster'] + text + ['{:6}'.format('Avg.')]
        print(  ' '.join( text ) );
    err    = padReshape( fcster.err_total );
    miss   = padReshape( [t != '' for t in fcster.type] );                                   # Pad and reshape the missed forecast flag; missed is either climo (C) or guidance (G); i.e., not ''
    score  = 100 - np.clip(miss.sum(axis=1)-2, 0, None)*14.286;                 # Compute score for missing; give them 2 free misses a week, after that subtract 14.286 (1/7th of 100) for every missed day
    if climo is not None: 
      score -= ((err > climo) & (miss == 0)).sum(axis=1)*6;                     # If climo is set, determine number of times that forecaster actually forecasted (missed == 0) and did NOT beat climo; multiply this number by 6 and subtract from score

    if book:
      id = 0;
      sheet = book.add_sheet(fcster.name)
      for s in range(len(sites)):
        offset = s * len(xls_cols);
        sheet.write(0, offset, sites[s])
        for i in range(len(xls_cols)): sheet.write(1, offset+i, xls_cols[i]);
        for i in range(8):
          if id >= len(fcster.day): break;
          row = fcster.day[id]+1;
#           print(s, i, row, offset)
          sheet.write(row, offset,   fcster.identifier[id])
          sheet.write(row, offset+1, fcster.day[id])
          sheet.write(row, offset+2, int(miss[s,i]))
          if climo is not None: 
            sheet.write(row, offset+3, int(err[s,i] > climo[s,i]) );
          id += 1
        print(s, row)
        sheet.write(row+1, offset+2, 'Score')
        sheet.write(row+1, offset+3, score[s])
        
    if verbose: 
      text = ['{:6.2f}'.format(s) for s in score]
      text = ['{:10}'.format(fcster.name)] + text + ['{:6.2f}'.format(score.mean())]
      print( ' '.join( text ) );
  book.save(spreadsheet);