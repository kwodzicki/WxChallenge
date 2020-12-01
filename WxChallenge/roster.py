import os

COL_CONVERT = {'ID'       : 'forecaster_id',
               'PASSWORD' : 'password',
               'CAT'      : 'category',
               'REG_PER'  : 'fall_spring_both',
               'CLASS1'   : 'class_id_1',
               'CLASS2'   : 'class_id_2',
               'NAME'     : ['first_name', 'last_name',],
               'EMAIL'    : 'email'}
COL_ORDER   = [0, 1, 4, 5, 2, 3, 6, 7]

joinLine = lambda line: '{}{}'.format( ','.join(line), os.linesep )

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

def _fixHeader( head ):
  hh = []
  for index in COL_ORDER:
    tmp = COL_CONVERT[ head[index] ]
    if isinstance(tmp, list):
      hh.extend( tmp )
    else:
      hh.append( tmp )
  return hh

def _fixLine( line ):
  vals = line.rstrip().split(',')
  keys = list( COL_CONVERT.keys() )
  line = []
  for i, index in enumerate(COL_ORDER):
    key = keys[index]
    if isinstance(COL_CONVERT[key], list):
      tmp = vals[index].split()
      line.extend( [' '.join(tmp[:-1]), tmp[-1]] )
    elif key == 'REG_PER':
      line.append( _fixFallSpring( vals[index] ) ) 
    elif 'CLASS' in key:
      line.append( _fixClass( vals[index] ) ) 
    else:
      line.append( vals[index] )
  return line

def _fixFallSpring( val ):
  if val == 'Fall':
    return 'F'
  elif val == 'Spring':
    return 'S'
  elif val == 'Yearly':
    return'B'
  else:
    raise Exception('Unknown season type; Fall/Spring/Yearly')

def _fixClass( val ):
  if val == 'None':
    return 'No Class ID'
  return val

def rosterOldTo2020( filename ):
  """
  Convert new roster format (2020 website redesign) to old format

  Arguments:
    filename (str): path to roster file

  Keyword arguments:
    None.

  Returns:
    None.

  """
  with open( filename, 'r' ) as fid:
    lines = fid.readlines()
  head = lines[0].rstrip().split(',')
  if all( [h in COL_CONVERT for h in head] ):                                   # If all column headers exist in the COL_CONVERT dictionary
    with open( filename, 'w' ) as fid:
      fid.write( joinLine( _fixHeader( head ) ) )
      for i in range( 1, len(lines) ):
        fid.write( joinLine( _fixLine( lines[i] ) ) )


################################################################################
def fix_Roster_CSV( filename ):
  """
  Reformat the csv roster from the WChallenge website.

  Arguments:
    filename (str): Full path to the file to reformat

  Keywords:
    None.

  Returns:
    None. Fixes formatting within the file; i.e., overwrites the file.

  """

  if not os.path.isfile( filename ): return False                               # If the file does NOT exist, return false
  fid  = open( filename, 'r+' )                                                 # Open file in r+ mode
  data = fid.readline()                                                         # Read the first line from the file
  line = fid.tell()                                                             # Get the current position in the file
  fid.seek(0, 2)                                                                # Seek to the end of the file
  if fid.tell() == line:                                                        # If the current position (i.e., the end of the file) is the same as the position after reading a line, then read in all the data and must fix
    fid.seek(0, 0)                                                              # Seek to beginning of file
    head  = data.split()[0].split(',')                                          # First list of values on space split is header, split header on coma 
    nCol  = len(head)                                                           # Number of columns in the data
    data  = data.split(',')                                                     # Split all data on comma
    lines = []                                                                  # Empty array to store lines; this so can sort by last name
    i     = 0                                                                   # Counter for the while loop
    while i < len(data):                                                        # While i is less than the length of data
      id  = i+nCol-1                                                            # Index for last column of row
      tmp = data[ id ].split()                                                  # Split what should be the last column on space; the last column is separated from next row by space
      if len(tmp) == 2:                                                         # If two values obtained from split
        data[ id ] = tmp[0]                                                     # Place the first split value into the last column of the current row
        data.insert( id+1, tmp[1] )                                             # Insert second value of the split into the data list as first value of next row into the data list
      sub = [ val.strip() for val in data[i:i+nCol] ]                           # Iterate over all values from i to i+nCol and strip off any preceding/trailing spaces and save new sub list for the row in sub
      lines.append( sub )                                                       # Join the line on comma, append carriage return, and append to lines list
      i += nCol                                                                 # Increment i by nCol
    classIDs, fnameID, lnameID = _get_CSV_Indices( head )                       # Determine some indexing variables
    lines = sorted( lines[1:], key = lambda val: val[lnameID] )                 # Sort the list of lines (in place) by last name
    fid.write( joinLine( head ) )                                               # Write header information to file
    for line in lines: fid.write( joinLine( line ) )                            # Join the sub list using comma, append a return character (\n), and write to the input file
    fid.truncate() 
  fid.close()                                                                   # Close the file
  
  rosterOldTo2020( filename )
  
  return True                                                                   # Return True

