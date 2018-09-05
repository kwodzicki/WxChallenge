#!/usr/bin/env python
import os;
import numpy as np;
from datetime import datetime, timedelta;
# Handle both Python2 and Python3
try:
  from WxChall_SQLite import WxChall_SQLite;
  from utils import checkURL, updateSchedule, getSemester;
  from parsers import parse_schedule, parse_results_head, parse_results_body, parse_results_foot;
except:
  from .WxChall_SQLite import WxChall_SQLite;
  from .utils import checkURL, updateSchedule, getSemester;
  from .parsers import parse_schedule, parse_results_head, parse_results_body, parse_results_foot;
  

class WxChallenge( WxChall_SQLite ):
  URL        = 'http://wxchallenge.com';
  categories = {0 : 'Professional', 
                1 : 'Faculty/Staff/Post-Doc',
                2 : 'Grad-Student',
                3 : 'Junior/Senior',
                4 : 'Freshman/Sophomore'}
  def __init__(self):
    self._date        = datetime.today().date()-timedelta(days=1)
    WxChall_SQLite.__init__(self);
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
  def update_Daily(self, schools = None):
    '''
    Name:
       update_Daily
    Purpose:
       A python function to download and parse (using BeautifulSoup) data
       from the WxChallenge.com webpage using todays date as the forecast
       day.
    Inputs:
       None.
    Ouputs:
       Some data
    Keywords:
       schools     : School code(s)
    '''
    semester = getSemester( self._date )
    year     = self._date.year
    tag = '{}:{}'.format(semester, year);                                       # Define tag for indexing _schedule
    if tag not in self._schedule:                                               # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule'.format(semester, year);
      raise Exception(err);

    identifier, day = self.getIdentDay(tag, self._date);                        # Get identifier and day based on the tag info and today's date
      
    urls, dates = self.__get_results_urls_dates(
      year, semester, identifier, day, schools = schools
    )
    if urls is None or len(urls) == 0:
      err = 'No varification for: {}!'.format(self._date)
      print(err);
      return False;
    for i in range(len(urls)):                                                  # Iterate over all urls
      print( urls[i] );
      soup = checkURL(urls[i]);                                                 # Download the HTML
      if soup:                                                                  # If data download was successful 
        table   = soup.find('table');                                           # Find the table in the parsed data
        self._head = parse_results_head(table);                                 # Parse the results header
        forecasts  = parse_results_body(table, dates[i], identifier, day);      # Parse results body
        self.add_forecasts( forecasts );
      else:                                                                     # Else, data download NOT successful
        print( 'URL not valid: {}'.format(urls[i]) );                           # Print a message
        return False
    return True
  ###########################################################################
  def getIdentDay(self, semYear, date):
    '''
    A method for determineing the forecast day and the station identifier.
    '''
    if semYear not in self._schedule:
      return None;
    for identifier in self._schedule[semYear]:
      tmp = self._schedule[semYear][identifier];
      if tmp['start'] <= date and tmp['end'] >= date:
        day = (date - tmp['start']).days + 1
        if day == 5 or day == 6: return None, None;        # If day is 5 or 6, then return; no forecasting on Saturday/Sunday
        if day >= 7: day = (day % 7) + 5;                  # If the day is greater or equal 7, then mod 7 and add 4
        if day >= 9: return None, None;                    # If the day is greater or equal 9, no forecasting on Saturday/Sunday
        return identifier, day;                # Determine the forecast day
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
          dates.append( start + timedelta(days = offset) )
          for school in schools:                                                # Iterate over all schools
            file = fileFMT.format(identifier.lower(), school, day);             # Generate the file name
            urls.append( '{}/{}/{}/{}'.format(self.URL, dir, year, file) );     # Append full URL to the list of urls
    return urls, dates;                                                         # Return urls and dates variables


if __name__ == "__main__":
  
  year     = '17-18'
  city     = 'kpvd'
  day      = 1
  d = WxChallenge(year, city, day);
  