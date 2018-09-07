from datetime import datetime;

# Handle python2 and python3
try:
  import data as WxData;
  from utils import getSemester, updateSchedule;
except:
  from . import data as WxData;
  from .utils import getSemester, updateSchedule;

getTemp = lambda x: int( x.split(u'\xb0')[0][1:] );                             # Lambda function to pull out temperature from string
getWind = lambda x: int( x[1:] );                                               # Lambda function to pull out wind from string
getPrec = lambda x: float( x.split('"')[0] );                                   # Lambda function to pull out precip from string

################################################################################
def convertMonth( month ):
  try:
    m = datetime.strptime(month,'%B').month;
  except:
    m = datetime.strptime(month,'%b').month;
  return m;

################################################################################
def parse_results_head( table ):
  '''Function to parse information from the table header of the HTML'''
  header = table.find('thead');                                                 # Get the table header    
  data = [];                                                                    # Empty list to store some data
  rows = header.find_all('tr');                                                 # Get all rows in the header
  for row in rows:                                                              # Iterate over all rows in the header
    cols = row.find_all('td');                                                  # Get all the columns in the row
    cols = [ele.text.strip() for ele in cols];                                  # Get the text for each column in the row
    if cols[0] != '': data.append( [ele for ele in cols if ele] );              # If the first element of cols is NOT empty, append list of all valid text to the data list

  # Get city, state, day information
  tmp = data[0][1].split();                                                     # Split second element of the first list in data on spaces
  info = {'city' : tmp[-4], 'state' : tmp[-3], 'day' : tmp[-1]}                 # Initialize a dictionary containing city, state, and day 
  
  # Get temperature, wind, precip verification  
  tmp = data[1][1].split();                                                     # Split the second element of the second list in data on spaces
  info['max']    = getTemp(tmp[1]);                                             # Add maximum temperature under max tag of info
  info['min']    = getTemp(tmp[3]);                                             # Add minimum temperature under min tag of info
  info['wind']   = getWind(tmp[5]);                                             # Add wind speed under wind tag of info
  info['precip'] = getPrec(tmp[8]);                                             # Add precipitation under precip tag of info
    
  # Decode first header line  
  tags = [];                                                                    # Initialize tags as empty list
  for ele in data[2]:                                                           # Iterate over all elements in the third list of data
    if ele != '|': tags.append( ele );                                          # If the element is NOT a vertical line (i.e., |), then append element to tags list
  
  # Decode the second header line  
  info['head1'], info['head2'] = [], [];                                        # Initialize empty lists under head1 and head2 tags of info
  index = -1;                                                                   # Set index to negative one (-1)
  for ele in data[3]:                                                           # Iterate over all elements in fourth list of data
    if ele == '|':                                                              # If element IS a vertical line (i.e., |)
      index += 1;                                                               # Increment index by one (1)
    else:                                                                       # Else
      info['head1'].append( tags[index] );                                      # Append the tag at index to the head1 list of info
      info['head2'].append( ele );                                              # Append the element to the head2 list of info
  return info;                                                                  # Return info dictionary 
################################################################################
def parse_results_body( table, date, ident, day, school = None ):
  '''Function to parse information from the table of the HTML'''
  body = table.find('tbody');                                                   # Get the table body
  forecasts = {};                                                               # Initialize forecasts
  rows = body.find_all('tr');                                                   # Get all rows of the table, i.e., all <tr> elements
  for row in rows:                                                              # Iterate over all rows
    cols = row.find_all('td');                                                  # Get all columns in the row; i.e., all <td> elements
    cols = [ele.text.strip() for ele in cols];                                  # Get text for each column in the row
    cols = [ele for ele in cols if ele != '|'];
    if len(cols) != len(WxData.resultsCols): continue;
    fc   = {};                                                                  # Initialize data to empty list
    for i in range( len(cols) ):                                                # Iterate over all elements in the column data
      if cols[i].isdigit():                                                     # If the element is a digit
        ele = int(cols[i]);                                                     # Set x to integer type of element
      else:                                                                     # Else
        try:                                                                    # Try to...
          ele = float(cols[i]);                                                 # Convert element to float
        except:                                                                 # If convert to float fails
          ele = cols[i];                                                        # Keep as string
      if WxData.resultsCols[i]['name'] == 'abs' and ele == '': ele = 0;
      fc[ WxData.resultsCols[i]['name'] ] = ele;
    if school is not None:                                                      # If the school keyword is set
      if fc['school'] != school: continue;                                      # If the current school name is NOT in the list of schools, then continue
    
    fc['date']       = date;
    fc['identifier'] = ident;
    fc['day']        = day;
    fc['semester']   = getSemester(date);
    fc['year']       = date.year;

    tag = '{}:{}:{}'.format( fc['name'], fc['school'], fc['category'] );        # Initialize a tag for the __forecasters dictionary
    forecasts[tag] = fc;                                                        # If the tag does NOT exist in the __forecasters dictionary, then initialize list under the tag
  return forecasts;

################################################################################
def parse_results_foot( table, date, ident, day):
  '''Function to parse information from the table of the HTML'''
  foot = table.find('tfoot');                                                   # Get the table body
  forecasts = {};                                                               # Initialize forecasts
  rows = foot.find_all('tr');                                                   # Get all rows of the table, i.e., all <tr> elements
  for row in rows:                                                              # Iterate over all rows
    cols = row.find_all('td');                                                  # Get all columns in the row; i.e., all <td> elements
    cols = [ele.text.strip() for ele in cols];                                  # Get text for each column in the row
    cols = [ele for ele in cols if ele != '|'];
    if len(cols) != len(WxData.resultsCols): continue;
    fc   = {};                                                                  # Initialize data to empty list
    for i in range( len(cols) ):                                                # Iterate over all elements in the column data
      if cols[i].isdigit():                                                     # If the element is a digit
        ele = int(cols[i]);                                                     # Set x to integer type of element
      else:                                                                     # Else
        try:                                                                    # Try to...
          ele = float(cols[i]);                                                 # Convert element to float
        except:                                                                 # If convert to float fails
          ele = cols[i];                                                        # Keep as string
      fc[ WxData.resultsCols[i]['name'] ] = ele;
    
    fc['date']       = date;
    fc['identifier'] = ident;
    fc['day']        = day;
    fc['semester']   = getSemester(date);
    fc['year']       = date.year;

    tag = '{}:{}:{}'.format( fc['name'], fc['school'], fc['category'] );        # Initialize a tag for the __forecasters dictionary
    forecasts[tag] = fc;                                                        # If the tag does NOT exist in the __forecasters dictionary, then initialize list under the tag
  return forecasts;

################################################################################
def parse_schedule( table ):
  '''Function to parse information form the schedule'''
  schedule = {}
  rows  = table.find_all('tr');
  for row in rows:
    cols = [ele.text.strip() for ele in row.find_all('td') if ele];
    if cols[0] == '': continue;
    if cols[0].split()[-1].isdigit():
      year = int(cols[0].split()[1]);
      continue;
    elif any(['DATES' in i.upper() for i in cols]) or cols[0] == '' or cols[1].upper() == 'TBD':
      continue;
    start, end = cols[-1].split('-')
    sMonth, sDay = start.split()[:2];
    end = end.split();
    if len(end) == 1:
      eMonth, eDay = sMonth, end[0];
    else:
      eMonth, eDay = end[:2];
    sMonth, sDay = convertMonth(sMonth), int(sDay)
    eMonth, eDay = convertMonth(eMonth), int(eDay)
    start  = datetime(int(year), sMonth, sDay).date()
    end    = datetime(int(year), eMonth, eDay).date()
    try:
      city, state = cols[0].split(',')[:2];
    except:
      city, state = cols[0], '';
    if cols[1][0] != 'K': cols[1] = 'K' + cols[1];
    info   = {WxData.scheduleCols[0]['name'] : city, 
              WxData.scheduleCols[1]['name'] : state, 
              WxData.scheduleCols[2]['name'] : cols[1], 
              WxData.scheduleCols[3]['name'] : start, 
              WxData.scheduleCols[4]['name'] : end}
              
    schedule = updateSchedule( schedule, info );
  return schedule;