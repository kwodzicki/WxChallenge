import logging

from datetime import timedelta;

from .WxSQLite import WxSQLite;
from .utils import checkURL, getSemester;
#from .parsers import parse_results_head, parse_results_body, parse_results_foot;

class WxChallenge( WxSQLite ):
  def __init__(self, verbose = False, **kwargs):
    super().__init__(verbose=verbose, **kwargs)
    self.__log        = logging.getLogger( __name__ )
    self._header      = None
    self._forecasters = None

  ###########################################################################
  def update_Semester(self, semester = None, year = None, schools = None):
    """
    Download data from the WxChallenge.com for a given semester in a given year.

    Arguments:
       None.

    Keyword arguments:
       semester (str): Semester (spring, fall) to download.
         Default is current semester based on today's date
       year (int) : Year to download
         Default is current year based on today's date
       school (str) : School code; only get data from this school
    
    Returns:
       bool

    """

    if semester is None or year is None:
      year     = self.__schedule.date
      semester = getSemester(self._schedule.date)

    tag = '{}:{}'.format(semester, year);                                       # Define tag for indexing _schedule
    if tag not in self._schedule:                                              # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule'.format(semester, year);
      raise Exception(err);

    identifiers = [id for id in self._schedule[tag]] 
    days        = [i for i in range(1, 9)];                                             # If day is not set, then generate numbers from 1-8, inclusive.

    args, dates = self.__get_results_args_dates(
      year, semester, identifiers, days, schools = schools
    );
    for i in range(len(args)):                                                  # Iterate over all urls
      self.__log.debug( 'Arguments for results: {}'.format(args[i]) )
      res = self.getResults( *args[i] )                                        # Download the HTML
      if res:                                                                  # If data download was successful 
        forecasts = res.results()
        self.add_forecasts( forecasts )
        self.add_verification( res )
    return True;

  def update_Day(self, semester, year, identifier, day, schools = None):
    '''
    Name:
       update_Day
    Purpose:
       A method to download and parse (using BeautifulSoup) data
       from the WxChallenge.com webpage for a specific forecast day
    Inputs:
       semester   : Semester to download for (fall or spring)
       year       : Year to download for
       identifier : Identifier for the forecast city
       day        : Forecast day number (1-8)
    Ouputs:
       True/False
    Keywords:
       schools     : School code(s) as scalar string or list of strings
    '''
    identifier = identifier.upper();
    tag = '{}:{}'.format(semester, year);                                       # Define tag for indexing _schedule
    if tag not in self._schedule:                                               # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule';                     # Formatting for exception
      raise Exception( err.format(semester, year) );                            # Raise the exception
      
    urls, dates = self.__get_results_args_dates(
      year, semester, identifier, day, schools = schools
    )
    if urls is None or len(urls) == 0:
      err = 'No varification for: {} ID: {}, Day: {}!'.format( tag, identifier, day )
      self.__log.error(err)
      return False;
    for i in range(len(urls)):                                                  # Iterate over all urls
      self.__log.debug( urls[i] )
      soup = checkURL(urls[i])                                                  # Download the HTML
      if soup:                                                                  # If data download was successful 
        table   = soup.find('table');                                           # Find the table in the parsed data
        self._head = parse_results_head(table);                                 # Parse the results header
        forecasts  = parse_results_body(table, dates[i], identifier, day);      # Parse results body
        models     = parse_results_foot(table, dates[i], identifier, day)   
        self.add_forecasts( forecasts );
        self.add_forecasts( models    );
      else:                                                                     # Else, data download NOT successful
        self.__log.error( 'URL not valid: {}'.format(urls[i]) )                 # Print a message
        return False
    return True

  ###########################################################################
  def update_Daily(self, schools = None):
    '''
    Name:
       update_Daily
    Purpose:
       A method to download and parse (using BeautifulSoup) data
       from the WxChallenge.com webpage using the date from 3 days
       ago, i.e., if run on Wednesday, will get data for Monday
    Inputs:
       None.
    Ouputs:
       True/False
    Keywords:
       schools     : School code(s)
    '''
    date     = self._schedule.date - timedelta(days=3);                         # Set date to 3 days before today's date
    semester = getSemester( date );                                             # Get semester; i.e., spring or fall
    tag = '{}:{}'.format(semester, date.year);                                  # Define tag for indexing _schedule
    if tag not in self._schedule:                                               # If the sem:year tag is NOT found in the schedule, raise an exception: should be able to fix later with try download of that time
      err = 'Error finding {} {} in the forecast schedule';                     # Formatting for exception
      raise Exception( err.format(semester, date.year) );                       # Raise the exception

    identifier, day = self.getIdentDay(tag, date);                              # Get identifier and day based on the tag info and today's date
      
    urls, dates = self.__get_results_args_dates(
      date.year, semester, identifier, day, schools = schools
    )
    if urls is None or len(urls) == 0:
      err = 'No varification for: {}!'.format( date )
      self.__log.error(err)
      return False;
    for i in range(len(urls)):                                                  # Iterate over all urls
      self.__log.debug( urls[i] )
      soup = checkURL(urls[i]);                                                 # Download the HTML
      if soup:                                                                  # If data download was successful 
        table   = soup.find('table');                                           # Find the table in the parsed data
        self._head = parse_results_head(table);                                 # Parse the results header
        forecasts  = parse_results_body(table, dates[i], identifier, day);      # Parse results body
        models     = parse_results_foot(table, dates[i], identifier, day)   
        self.add_forecasts( forecasts );
        self.add_forecasts( models    );
      else:                                                                     # Else, data download NOT successful
        self.__log.error( 'URL not valid: {}'.format(urls[i]) );                           # Print a message
        return False
    return True
  ###########################################################################
  def getIdentDay(self, semYear, date):
    """
    Determine the forecast day and the station identifier.

    Arguments:
       semYear (str)   : "semester:year" to be used as a key for the _schedule dictionary
       date (datetime) : A datetime object for the date of interest

    Keyword arguments:
      None.

    Returns
       Returns a station identifier and forecast day number OR None if
       nothing found

    """

    out_id, out_day = None, None;
    if semYear in self._schedule:                                               # If the semester and year are NOT in the schedule
      for identifier in self._schedule[semYear]:                                # Else, iterate over all the identifiers in the semester/year that are in the schedule
        tmp = self._schedule[semYear][identifier];                              # Get the data for a given identifier in a given semester/year
        if tmp['start'] <= date and tmp['end'] >= date:                         # If the date input is between the starting/ending dates for the station
          day = (date - tmp['start']).days + 1;                                 # Compute rough forecast day
          if day == 5 or day == 6: break;                                       # If day is 5 or 6, then break; no forecasting on Saturday/Sunday
          if day >= 7: day = (day % 7) + 4;                                     # If the day is greater or equal 7, then mod 7 and add 4
          if day >= 9: break;                                                   # If the day is greater or equal 9, no forecasting on Saturday/Sunday
          out_id, out_day = identifier, day;                                    # Determine the forecast day
          break;                                                                # Break the loop
    return out_id, out_day;                                                     # Determine the forecast day

  ##############################################################################
  def __get_results_args_dates(self, years, semesters, identifiers, days, schools = None):
    '''
    Function to build URL for downloading the data. Returns a list.
    year is assumed to be the Fall semester year.
    school is defaulted to natl; for national information'''
    args    = [] 
    dates   = [] 
    if not isinstance(years,       list): years       = [years]                 # Convert years to list if not already
    if not isinstance(semesters,   list): semesters   = [semesters]             # Convert years to list if not already
    if not isinstance(identifiers, list): identifiers = [identifiers]           # Convert identifiers to list if not already
    if not isinstance(days,        list): days        = [days]                  # Convert days to list if not already
    if schools is None:                                                         # If schools is None
      schools = ['natl']                                                        # Set default value for schools
    elif not isinstance(schools, list):                                         # Else if schools is not a list instance
      schools     = [schools]                                                   # Convert schools to list
    for year, semester in zip(years, semesters):                                # Iterate over all years and semesters
      tag  = '{}:{}'.format(semester.lower(), year);      
      for identifier in identifiers:                                            # Iterate over all identifiers
        if identifier not in self._schedule[tag]: continue;
        start = self._schedule[tag][identifier]['start'];
        for day in days:                                                        # Iterate over all forecast days
          offset  = 7 if day > 4 else 0;
          offset += (day-1) % 4;
          dates.append( start + timedelta(days = offset) )
          for school in schools:                                                # Iterate over all schools
            args.append( 
              (semester, year, identifier, school, day,)
            )
    return args, dates                                                          # Return urls and dates variables
