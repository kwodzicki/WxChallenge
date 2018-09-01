#!/usr/bin/env python
import os, datetime;
import numpy as np;

# Handle both Python2 and Python3
try:
  from WxChall_SQLite import WxChall_SQLite;
  from utils import checkURL, updateSchedule, getSemester;
  from parsers import parse_schedule, parse_results_head, parse_results_body, parse_results_foot;
except:
  from .WxChall_SQLite import WxChall_SQLite;
  from .utils import checkURL, updateSchedule, getSemester;
  from .parsers import parse_schedule, parse_results_head, parse_results_body, parse_results_foot;
  
_dir = os.path.dirname(os.path.abspath(__file__));

class WxChallenge( WxChall_SQLite ):
  URL        = 'http://wxchallenge.com';
  categories = {0 : 'Professional', 
                1 : 'Faculty/Staff/Post-Doc',
                2 : 'Grad-Student',
                3 : 'Junior/Senior',
                4 : 'Freshman/Sophomore'}
  def __init__(self, datadir = _dir):
    self._date        = datetime.datetime.today().date()
    self.datadir      = datadir;
    self.sqlFile      = os.path.join(self.datadir, 'WxChall.sqlite');
    WxChall_SQLite.__init__(self, self.sqlFile);
    self._header      = None;
    self._forecasters = None;
    self._schedule    = self.get_schedule();
    if len(self._schedule) == 0: 
      self.download_Schedule(all=True);

  ###########################################################################
  def update_Semester(self, semester, year, schools = None):
    '''
    Name:
       update_Semester
    Purpose:
       A python function to download data
       from the WxChallenge.com webpage.
    Inputs:
       semester : Semester (spring, fall) to download, string
       year     : Year to download, int
       school   : School code; only get data from this school
    Ouputs:
       Some data
    Keywords:
       None.
    Author and History:
       Kyle R. Wodzicki     Created 29 Aug. 2018
    '''      
    tag = '{}:{}'.format(semester, year);                                       # Define tag for indexing _schedule
    if tag not in self._schedule:                                              # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule'.format(semester, year);
      raise Exception(err);

    identifiers = [id for id in self._schedule[tag]] 
    days        = [i for i in range(1, 9)];                                             # If day is not set, then generate numbers from 1-8, inclusive.

    urls, dates = self.__get_results_urls_dates(
      year, semester, identifiers, days, schools = schools
    );
    for i in range(len(urls)):                                                  # Iterate over all urls
      soup = checkURL(urls[i]);                                                 # Download the HTML
      if soup:                                                                  # If data download was successful 
        table   = soup.find('table');                                           # Find the table in the parsed data
        self._head = parse_results_head(table);                                 # Parse the results header
        ident, day = self.getIdentDay(tag, dates[i])
        forecasts  = parse_results_body(table, dates[i], ident, day)            # Parse results body
        models     = parse_results_foot(table, dates[i], ident, day)   
        self.add_forecasts( forecasts );
        self.add_forecasts( models    );
      else:                                                                     # Else, data download NOT successful
        print( 'URL not valid: {}'.format(urls[i]) );                           # Print a message

  ###########################################################################
  def update(self, school = None):
    '''
    Name:
       update
    Purpose:
       A python function to download and parse (using BeautifulSoup) data
       from the WxChallenge.com webpage.
    Inputs:
       semYears   : Tuple containing the 
                     (semester, year) to get data for.
       identifier : City identifier; i.e., KPDX for Portland, Or.
       day        : Day of the challenge.
       school     : School code
    Ouputs:
       Some data
    Keywords:
       None.
    Author and History:
       Kyle R. Wodzicki     Created 29 Aug. 2018
    '''
    def getForecastDay(tag):
      for identifier in self._schedule[tag]:
        tmp = self._schedule[tag][identifier];
        if tmp['start'] <= self._date and tmp['end'] >= self._date:
          return identifier, ((self._date - tmp['start']).days + 1) % 7;      # Determine the forecast day
      return None, None;
    semester = getSemester( self._date )
    year     = self._date.year

    tag = '{}:{}'.format(semester, year);                                       # Define tag for indexing _schedule
    if tag not in self._schedule:                                              # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule'.format(semester, year);
      raise Exception(err);

    identifier, day = getForecastDay(tag);                                  # Get identifier and day based on the tag info and today's date
      
    urls, dates = self.__get_results_urls_dates(year, semester, identifier, day)
    for i in range(len(urls)):                                                  # Iterate over all urls
      print( urls[i] );
      soup = checkURL(urls[i]);                                                 # Download the HTML
      if soup:                                                                  # If data download was successful 
        table   = soup.find('table');                                           # Find the table in the parsed data
        self._head = parse_results_head(table);                                 # Parse the results header
        forecasts  = parse_results_body(table, dates[i])                        # Parse results body
        self.add_forecasts( forecasts );
      else:                                                                     # Else, data download NOT successful
        print( 'URL not valid: {}'.format(urls[i]) );                           # Print a message
  ###########################################################################
  def getIdentDay(self, semYear, date):
    if semYear not in self._schedule:
      return None;
    for identifier in self._schedule[semYear]:
      tmp = self._schedule[semYear][identifier];
      if tmp['start'] <= date and tmp['end'] >= date:
        day = (date - tmp['start']).days + 1
        if day >= 7: day = (day % 7) + 4
        return identifier, day;                # Determine the forecast day
  ###########################################################################
#   def scoring( self, fcs ):
# #     newRow = lambda: np.zeros( (8,1,), dtype=np.byte );
#     def padReshape( input ):
#       input = np.array(input);
#       if (input.size % 8) != 0:
#         input = np.pad(input, (0, 8-(input.size % 8),), 'constant')
#       return np.reshape( input, (8, input.size//8,), order='f' );
#       
#     if 'CLIMO0' in fcs['xxx'][8] and 'CLIMO_' in fcs['xxx'][8]:
#       climo = np.array( [f['xxx'][8]['CLIMO0']['err_total'],
#                          f['xxx'][8]['CLIMO_']['err_total']] ).max(axis=0);
#     elif 'CLIMO0' in fcs['xxx'][8] and 'CLIMO_' not in fcs['xxx'][8]:
#       climo = np.array( [f['xxx'][8]['CLIMO0']['err_total'] );
#     elif 'CLIMO0' not in fcs['xxx'][8] and 'CLIMO_' in fcs['xxx'][8]:
#       climo = np.array( [f['xxx'][8]['CLIMO_']['err_total'] );
#     else:
#       climo = None;
#     climo = padReshape( climo );
#     for sch in fcs:
#       if sch == 'xxx': continue;                                                # Skip xxx school
#       for cat in fcs[sch]:                                                      # Iterate over categories
#         for name in fcs[sch][cat]:                                              # Iterate over names
#           tmp    = fcs[sch][cat][name];                                         # Temporary data for school, category, forecaster
#           err    = padReshape( tmp['err_total'] );                              # Pad and reshape the forecaster error points
#           missed = padReshape( [t != '' for t in tmp['type']] );                # Pad and reshape the missed forecast flag; missed is either climo (C) or guidance (G); i.e., not ''
#           score  = 100 - np.clip(missed.sum(axis=0)-2, 0, None)*14.286;         # Compute score for missing; give them 2 free misses a week, after that subtract 14.286 (1/7th of 100) for every missed day
#           if climo: score -= ((err > climo) & (missed == 0)).sum(axis=0)*6;     # If climo is set, determine number of times that forecaster actually forecasted (missed == 0) and did NOT beat climo; multiply this number by 6 and subtract from score
#           tmp['score'] = score;

#           shape = ( max(tmp['day']), len(set(tmp['identifier'])), )     
#           tmp['absence'] = {'ident' : [], 
#                             'vals' : np.zeros( shape, dtype = np.byte ) };
#           n = 0;
#           tmp['absence']['ident'].append( tmp['identifier'][n] );
#           for i in range( len(tmp['date']) ):
#             if tmp['identifier'][i] != tmp['absence']['ident'][n]:
#               n += 1
#               tmp['absence']['ident'].append( tmp['identifier'][i] );
#             tmp['absence']['vals'][tmp['day'][i]-1,n] = \
#               tmp['type'][i].upper() == 'C';          
    return fcs;
  ###########################################################################
  def __update(self, semYear = None, identifier = None, day = None, school = None):
    '''
    Name:
       update
    Purpose:
       A python function to download and parse (using BeautifulSoup) data
       from the WxChallenge.com webpage.
    Inputs:
       semYears   : Tuple containing the 
                     (semester, year) to get data for.
       identifier : City identifier; i.e., KPDX for Portland, Or.
       day        : Day of the challenge.
       school     : School code
    Ouputs:
       Some data
    Keywords:
       None.
    Author and History:
       Kyle R. Wodzicki     Created 29 Aug. 2018
    '''
    def getForecastDay(tag):
      for identifier in self._schedule[tag]:
        tmp = self._schedule[tag][identifier];
        if tmp['start'] <= self._date and tmp['end'] >= self._date:
          return identifier, ((self._date - tmp['start']).days + 1) % 7;      # Determine the forecast day
      return None, None;
      
    if not semYear: 
      semester = getSemester(self._date)
      year     = self._date.year
    else:
      semester = semYear[0].lower()
      year     = semYear[1]
    
    tag = '{}:{}'.format(semester, year);                                       # Define tag for indexing _schedule
    print(tag);
    if tag not in self._schedule:                                              # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule'.format(semester, year);
      raise Exception(err);
      
    if not identifier:                                                          # If no identifier is input
      if not day:                                                               # If no day is input
        identifier, day = getForecastDay(tag);                                  # Get identifier and day based on the tag info and today's date
        if day is None:
          raise Exception('Something went wrong! Has the challenge started yet?');
    else:                                                                       # Identifier was input
      identifier = identifier.upper();
      if identifier not in self._schedule[tag]:                                 # If the identifier is NOT in the sem:year dictionary
        raise Exception('{} is NOT in {} {} schedule'.format(identifier, semester, year) );#Raise an exception
      if not day: day = [i for i in range(1, 9)];                               # If day is not set, then generate numbers from 1-8, inclusive.

#     dates = self.__get_dates(year, semester, identifier, day);                  # Generate URL to download data from
#     urls  = self.__results_url(year, identifier, day, schools = school);        # Generate URL to download data from
    urls, dates = self.__get_results_urls_dates(years, semesters, identifiers, days)
    for i in range(len(urls)):                                                  # Iterate over all urls
      soup = checkURL(urls[i]);                                                 # Download the HTML
      if soup:                                                                  # If data download was successful 
        table   = soup.find('table');                                           # Find the table in the parsed data
        self._head = parse_results_head(table);                                 # Parse the results header
        forecasts  = parse_results_body(table, dates[i])                        # Parse results body
        self.add_forecasts( forecasts );
      else:                                                                     # Else, data download NOT successful
        print( 'URL not valid: {}'.format(urls[i]) );                           # Print a message
  ##############################################################################
  def load_Data(self, year, school = None):
    files = [];
    for file in os.listdir(self.datadir):                                       # Iterate over all files in the directory
      if file.endswith('.csv'):                                                 # If the file ends with .csv
        if year not in file: continue;                                          # If file is NOT for the requested year
        if school is not None:                                                  # If the school keyword is set
          if isinstance(school, list):                                          # If school is a list instance
            if not any([s in file for s in school]):                            # If the file does NOT contain any of the school choices
              continue;                                                         # Continue to next file
          elif school not in file:                                              # Elif, school string not in file
            continue;                                                           # Continue to next file
        files.append( os.path.join(self.datadir, file) );                       # Create full file path and append to the files list
  ##############################################################################
  def download_Schedule(self, year = None, all = False):
    '''
    A method to get the current; or previous, forecase schedule.
    If year is used, assumed to be year of Fall semester, so will
    get schedule for year/year+1 season.
    '''
    if all:
      self._schedule = {};
      year = [y for y in range(2006, self._date.year)]
    
    if year is None or all:                                                     # If year is None (i.e., no year input) OR all is True
      url  = '{}/challenge/schedule.php'.format(self.URL);                      # Set up url
      soup = checkURL(url);                                                     # Attempt to get data
      if soup:
        table = soup.find_all('table')[-1];                                     # Find the table in the parsed data
        self._schedule.update( parse_schedule(table) );                         # Parse the schedule
      if not all:                                                               # If all is NOT set
        self.update_schedule( self._schedule );
        return;
    elif not isinstance(year, list):                                            # Else, if year is not list instance
      year = [year];                                                            # Convert year to list
    
    tags = ' '.join( [tag for tag in self._schedule] );                         # Get all tags from _schedule and convert to giant string
    if any([str(y) in tags for y in year]): return                              # If the year requested is already in one of the tags
    
    for y in year:                                                              # Iterate over all years
      syear, eyear = str(y)[-2:], str(y+1)[-2:];
      url  = '{}/challenge/schedule_{}{}.php'.format(self.URL,syear,eyear);
      soup = checkURL(url);
      if soup:
        table = soup.find_all('table')[-1];                                     # Find the table in the parsed data
        self._schedule.update( parse_schedule(table) );                         # Parse the schedule
    self.update_schedule( self._schedule );
  ##############################################################################
  def __get_results_urls_dates(self, years, semesters, identifiers, days, schools = None):
    '''
    Function to build URL for downloading the data. Returns a list.
    year is assumed to be the Fall semester year.
    school is defaulted to natl; for national information'''
    dir     = 'history/results'
    fileFMT = '{}_results_{}_day{}.html'
    urls    = [];
    dates   = [];
    if not isinstance(years,       list): years       = [years];                # Convert years to list if not already
    if not isinstance(semesters,   list): semesters   = [semesters];            # Convert years to list if not already
    if not isinstance(identifiers, list): identifiers = [identifiers];          # Convert identifiers to list if not already
    if not isinstance(days,        list): days        = [days];                 # Convert days to list if not already
    if schools is None:                                                         # If schools is None
      schools = ['natl'];                                                       # Set default value for schools
    elif not isinstance(schools, list):                                         # Else if schools is not a list instance
      schools     = [schools];                                                  # Convert schools to list
    for year, semester in zip(years, semesters):                                # Iterate over all years and semesters
      tag  = '{}:{}'.format(semester.lower(), year);      
      if semester.lower() == 'spring':
        year = '{}-{}'.format(str(year-1)[-2:], str(year)[-2:]);                # Set up the year part of the url
      else:    
        year = '{}-{}'.format(str(year)[-2:], str(year+1)[-2:]);                # Set up the year part of the url
      for identifier in identifiers:                                            # Iterate over all identifiers
        if identifier not in self._schedule[tag]: continue;
        start = self._schedule[tag][identifier]['start'];
        for day in days:                                                        # Iterate over all forecast days
          offset  = 7 if day > 4 else 0;
          offset += (day-1) % 4;
          dates.append( start + datetime.timedelta(days = offset) )
          for school in schools:                                                # Iterate over all schools
            file = fileFMT.format(identifier.lower(), school, day);             # Generate the file name
            urls.append( '{}/{}/{}/{}'.format(self.URL, dir, year, file) );     # Append full URL to the list of urls
    return urls, dates;                                                         # Return urls and dates variables

  ##############################################################################
  def __results_url(self, years, identifiers, days, schools = None):
    '''
    Function to build URL for downloading the data. Returns a list.
    year is assumed to be the Fall semester year.
    school is defaulted to natl; for national information'''
    dir     = 'history/results'
    fileFMT = '{}_results_{}_day{}.html'
    urls    = [];
    
    if not isinstance(years,       list): years       = [years];                # Convert years to list if not already
    if not isinstance(identifiers, list): identifiers = [identifiers];          # Convert identifiers to list if not already
    if not isinstance(days,        list): days        = [days];                 # Convert days to list if not already
    if schools is None:                                                         # If schools is None
      schools = ['natl'];                                                       # Set default value for schools
    elif not isinstance(schools, list):                                         # Else if schools is not a list instance
      schools     = [schools];                                                  # Convert schools to list
    for year in years:                                                          # Iterate over all years
      year = '{}-{}'.format(str(year)[-2:], str(year+1)[-2:]);                  # Set up the year part of the url
      for identifier in identifiers:                                            # Iterate over all identifiers
        for day in days:                                                        # Iterate over all forecast days
          for school in schools:                                                # Iterate over all schools
            file = fileFMT.format(identifier.lower(), school, day);             # Generate the file name
            urls.append( '{}/{}/{}/{}'.format(self.URL, dir, year, file) );     # Append full URL to the list of urls
    return urls;                                                                # Return urls variable
  ##############################################################################
  def __get_dates(self, years, semesters, identifiers, days):
    '''
    Function to build URL for downloading the data. Returns a list.
    year is assumed to be the Fall semester year.
    school is defaulted to natl; for national information'''    
    if not isinstance(years,       list): years       = [years];                # Convert years to list if not already
    if not isinstance(semesters,   list): semesters   = [semesters];            # Convert years to list if not already
    if not isinstance(identifiers, list): identifiers = [identifiers];          # Convert identifiers to list if not already
    if not isinstance(days,        list): days        = [days];                 # Convert days to list if not already
    dates = [];
    for year in years:                                                          # Iterate over all years
      for semester in semesters:
        tag = '{}:{}'.format(semester.lower(), year);      
        for identifier in identifiers:                                            # Iterate over all identifiers
          if identifier not in self._schedule[tag]: continue;
          start = self._schedule[tag][identifier]['start'];
          for day in days:                                                        # Iterate over all forecast days
            offset  = 7 if day > 4 else 0;
            offset += (day-1) % 4;
            dates.append( start + datetime.timedelta(days = offset) )
    return dates;                                                                # Return urls variable

  ##############################################################################
  def __load_forecaster( self, name, school ):
    tag = '{}:{}'.format( name, school );                                       # Initialize a tag for the __forecasters dictionary
    if tag not in self._forecasters: self._forecasters[tag] = [];               # If the tag does NOT exist in the __forecasters dictionary, then initialize list under the tag
    return tag;                                                                 # Return the tag
  ##############################################################################
#   def __parse_schedule( self, table ):
#     '''Private method to parse information form the schedule'''
#     def convertMonth( month ):
#       try:
#         m = datetime.datetime.strptime(month,'%B').month;
#       except:
#         m = datetime.datetime.strptime(month,'%b').month;
#       return m;
#     schedule = {}
#     rows  = table.find_all('tr');
#     for row in rows:
#       cols = [ele.text.strip() for ele in row.find_all('td') if ele];
#       if cols[0] == '': continue;
#       if cols[0].split()[-1].isdigit():
#         year = int(cols[0].split()[1]);
#         continue;
#       elif any(['CITY' in i.upper() for i in cols]) or cols[0] == '' or cols[1].upper() == 'TBD':
#         continue;
#       start, end = cols[-1].split('-')
#       sMonth, sDay = start.split()[:2];
#       end = end.split();
#       if len(end) == 1:
#         eMonth, eDay = sMonth, end[0];
#       else:
#         eMonth, eDay = end[:2];
#       sMonth, sDay = convertMonth(sMonth), int(sDay)
#       eMonth, eDay = convertMonth(eMonth), int(eDay)
#       start  = datetime.datetime(int(year), sMonth, sDay).date()
#       end    = datetime.datetime(int(year), eMonth, eDay).date()
#       info   = cols[0].split(',')[:2] + cols[1:2] + [start, end]       
#       schedule = updateSchedule( schedule, info );
#     self._schedule.update( schedule );

  ##############################################################################
#   def __parse_results_head( self, table, id ):
#     '''Function to parse information from the table header of the HTML'''
#     getTemp = lambda x: int( x.split(u'\xb0')[0][1:] );                         # Lambda function to pull out temperature from string
#     getWind = lambda x: int( x[1:] );                                           # Lambda function to pull out wind from string
#     getPrec = lambda x: float( x.split('"')[0] );                               # Lambda function to pull out precip from string
#   
#     header = table.find('thead');                                          # Get the table header    
#     data = [];                                                                  # Empty list to store some data
#     rows = header.find_all('tr');                                               # Get all rows in the header
#     for row in rows:                                                            # Iterate over all rows in the header
#       cols = row.find_all('td');                                                # Get all the columns in the row
#       cols = [ele.text.strip() for ele in cols];                                # Get the text for each column in the row
#       if cols[0] != '': data.append( [ele for ele in cols if ele] );            # If the first element of cols is NOT empty, append list of all valid text to the data list
# 
#     # Get city, state, day information
#     tmp = data[0][1].split();                                                   # Split second element of the first list in data on spaces
#     info = {'city' : tmp[-4], 'state' : tmp[-3], 'id' : id, 'day' : tmp[-1]}    # Initialize a dictionary containing city, state, id, and day 
#   
#     # Get temperature, wind, precip verification
#     tmp = data[1][1].split();                                                   # Split the second element of the second list in data on spaces
#     info['max']    = getTemp(tmp[1]);                                           # Add maximum temperature under max tag of info
#     info['min']    = getTemp(tmp[3]);                                           # Add minimum temperature under min tag of info
#     info['wind']   = getWind(tmp[5]);                                           # Add wind speed under wind tag of info
#     info['precip'] = getPrec(tmp[8]);                                           # Add precipitation under precip tag of info
#     
#     # Decode first header line
#     tags = [];                                                                  # Initialize tags as empty list
#     for ele in data[2]:                                                         # Iterate over all elements in the third list of data
#       if ele != '|': tags.append( ele );                                        # If the element is NOT a vertical line (i.e., |), then append element to tags list
# 
#     # Decode the second header line
#     info['head1'], info['head2'] = [], [];                                      # Initialize empty lists under head1 and head2 tags of info
#     index = -1;                                                                 # Set index to negative one (-1)
#     for ele in data[3]:                                                         # Iterate over all elements in fourth list of data
#       if ele == '|':                                                            # If element IS a vertical line (i.e., |)
#         index += 1;                                                             # Increment index by one (1)
#       else:                                                                     # Else
#         info['head1'].append( tags[index] );                                    # Append the tag at index to the head1 list of info
#         info['head2'].append( ele );                                            # Append the element to the head2 list of info
#     self._header = info;                                                        # Return info dictionary
  ##############################################################################
#   def __parse_results_body( self, table, date, school = None ):
#     '''Function to parse information from the table of the HTML'''
#     body = table.find('tbody');                                                 # Get the table body
#     if self._forecasters is None: self._forecasters = {};                       # If __forecasters is None, set to empty dictionary
#     nameID, schID, catID, absID = None, None, None, None;                       # Initialize nameID and schID to None; these determine where in the data list the forecaster name and school are
#     nHead = len(self._header['head1']);                                         # Set nHead to the number of elements in the __header['head1'] list
#     for i in range( nHead ):                                                    # Iterate from 0 to nHead-1
#       if self._header['head2'][i].lower() == 'name':                            # If the value of __header['head2'] at i is name
#         nameID = i;                                                             # Set the index for nameID to i
#       elif self._header['head2'][i].lower() == 'sch':                           # If the value of __header['head2'] at i is sch
#         schID = i;                                                              # Set the index for schID to i
#       elif self._header['head2'][i].lower() == 'gr':                            # If the value of __header['head2'] at i is sch
#         catID = i;                                                              # Set the index for schID to i
#       elif self._header['head2'][i].lower() == 'abs':                           # If the value of __header['head2'] at i is sch
#         absID = i;                                                              # Set the index for schID to i
#     rows = body.find_all('tr');                                                 # Get all rows of the table, i.e., all <tr> elements
#     for row in rows:                                                            # Iterate over all rows
#       cols  = row.find_all('td');                                               # Get all columns in the row; i.e., all <td> elements
#       cols  = [ele.text.strip() for ele in cols];                               # Get text for each column in the row
#       data  = [];                                                               # Initialize data to empty list
#       i, n, nMax = 0, 0, 0;                                                     # Initialize i, n, and nMax to zero
#       for ele in cols:                                                          # Iterate over all elements in the column data
#         if ele == '|':                                                          # If the element is a vertical bar (i.e., '|')
#           i   += nMax;                                                          # Increment i by nMax
#           if i >= nHead: break;                                                 # If i is greater/equal to nHead, then break the for loop
#           n    = 0;                                                             # Set n to zero (0)
#           nMax = sum([j == self._header['head1'][i] for j in self._header['head1']]);# Compute nMax based on number of strings that match string at i
#         elif n < nMax:                                                          # Else, if n is less than nMax
#           if ele.isdigit():                                                     # If the element is a digit
#             x = int(ele);                                                       # Set x to integer type of element
#           else:                                                                 # Else
#             try:                                                                # Try to...
#               x = float(ele);                                                   # Convert element to float
#             except:                                                             # If convert to float fails
#               x = ele;                                                          # Keep as string
#           data.append(x);                                                       # Append x to data
#           n += 1;                                                               # Increment n by 1
#       if len(data) != nHead: continue;                                          # If the length of the data list is NOT equal to nHead, then continue
#       if school is not None:                                                    # If the school keyword is set
#         if data[schID] != school: continue;                                     # If the current school name is NOT in the list of schools, then continue
#       tag = self.__load_forecaster(data[nameID], data[schID]);                  # Initialize a tag for the __forecasters dictionary
#       self._forecasters[tag].append( data );                                    # Append the data list to the 
#       if data[absID] == '': data[absID] = 0
#       cat  = data.pop(catID);
#       sch  = data.pop(schID);
#       name = data.pop(nameID);
#       data.append(date)
#       self.add_forecast(name, sch, cat, data);                         # Add the forecast to the database
  ##############################################################################

if __name__ == "__main__":
  
  year     = '17-18'
  city     = 'kpvd'
  day      = 1
  d = WxChallenge(year, city, day);
  