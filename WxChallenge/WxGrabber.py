import logging
import requests
import warnings

from .utils import *
from . import data as WxData

class WxGrabber(object):
  _BASE_URL = 'https://wxchallenge.com'
  _RESULTS  = '{}/results.php'.format(  _BASE_URL )
  _SCHEDULE = '{}/schedule.php'.format( _BASE_URL )

  def __init__(self, *args, verify = False, **kwargs):
    super().__init__(*args, **kwargs)
    self.__log   = logging.getLogger( __name__ )
    self._verify = verify
    if not verify:
      warnings.warn('InsecureRequestWarning : You have chosen to allow insecure connection to the WxChallenge server')
      warnings.filterwarnings('ignore', message='Unverified HTTPS request')

  def getResults(self, semester, year, identifier, school, day):
    """
    Get BeautifulSoup parsed HTML results

    Arguments:
      semester   (str) : Semester to get resutls for (spring or fall)
      year       (int) : Year of the semester
      identifier (str) : 4-character station ID
      school     (str) : 3-character school code
      day        (int) : Forecast day

    Keyword arguments:
      None.

    Returns:
      BeautifulSoup parsed HTML data containing forecasting results

    """

    if semester.lower() == 'spring':
      year = year-1

    identifier = identifier.lower()
    params = {'year'   : self._getYear(year, year+1), 
              'school' : school, 
              'city'   : identifier,
              'day'    : day}

    soup = self._getHTML( self._RESULTS, params = params ) 
    return WxResults( soup, identifier )

  def getSchedule(self, sYear = None, eYear = None):
    """
    Get BeautifulSoup parsed HTML data for forecasting schedule

    This method will hit the php script and download the HTML of the web page
    containing the forecasting schedule for a given season. Default is to
    return schedule for current season, which is determined by the current
    UTC date. If the current date is AFTER July 1, then assume the season is
    'Current year'-'Next Year'. If date is BEFORE July 1, then assume season
    is 'Previous Year'-'Current year'.

    For example:
      July  2, 2020 -> current season is 20-21
      June 30, 2020 -> current season is 19-20

    Arguments:
      None.

    Keywords arguments:
      sYear (int) : Starting year of the forecast schedule, defaults to current season
      eYear (int) : Ending year of forecast schedule, defaults to current season

    Returns:
      str : HTML data from website

    """

    ref = datetime.datetime.utcnow()

    if sYear is None:                                                           # If sYear is None
      sYear = ref.year                                                          # Set sYear to current year
      if ref < datetime.datetime(ref.year, 7, 1): sYear -= 1                    # If ref date is before July 1, then set start date to previous year 
    if eYear is None:                                                           # If eYear is None
      eYear = sYear + 1                                                         # Set to year before sYear
    else:                                                                       # Else
      sYear = eYear - 1                                                         # Set sYear to year before eYear

    params = {'year' : self._getYear(sYear, eYear)}                             # Set parameters for php request

    soup = self._getHTML( self._SCHEDULE, params=params ) 
    return WxSeason( soup )                                                     # Try to get request

  def _getYear(self, sYear, eYear):
    """Format year span to string for posting to php"""
    sYear = str(sYear)[-2:]                                                     # Get last 2 digits of sYear 
    eYear = str(eYear)[-2:]                                                     # Get last 2 digits of eYear
    return '{}-{}'.format(sYear, eYear)                                         # Return formatted year

  def _getHTML(self, url, **kwargs):
    """
    Actually get the html data from the URL and parse with BeautifulSoup

    Arguments:
      url (str) : URL to use in request

    Keyword arguments:
      Any accepted by requests.post()

    Returns:
      BeautifulSoup parsed data

    """

    kwargs['verify'] = self._verify                                             # Set verify based on class attribute

    try:
      r = requests.post( url, **kwargs )                                        # Try to get request
    except Exception as err:                                                    # On exception
      self.__log.error( err )                                                     # Log error
      return None                                                               # Return None

    if not r.ok:                                                                # Check if request is Okay
      self.__log.error( 'Request is not okay' )                                   # Log error
      return None                                                               # Return None

    try:                                                                        # Try to
      html = r.content                                                          # Get content from request
    except Exception as err:                                                    # On exception
      self.__log.error( err )                                                     # Log error
      return None                                                               # Return None
    
    return BeautifulSoup(html, 'lxml')                                          # Parse the html data using the lxml format?


class WxResults( object ):
  #def __init__(self, year, school, city, day, soup):
  def __init__(self, soup, identifier):
    self.__log         = logging.getLogger(__name__)
    #self._year         = year
    #self._school       = school
    #self._city         = city
    #self._day          = day
    self._soup         = soup
    self.identifier    = identifier.upper()

    self._verification = None
    self.max           = None
    self.min           = None
    self.wind          = None
    self.precip        = None
    self.year          = None 
    self.school        = None
    self.day           = None
    self.date          = None
    self.city          = None
    self.state         = None

    self._parseVerification()
    self._parseSelected()
    self._parseDate()

  def __repr__(self):
    return '< {} - {}, {} : {} >'.format(
            self.__class__.__name__, self.city, self.state, self._verification )

  def _parseVerification( self ):
    """Get verification data from the BeautifulSoup data"""
  
    tmp = self._soup.find('h5')
    if tmp:
      self._verification = tmp.text 
      tmp = tmp.text.split(':')[1].split('/')
      self.max    = getTemp(tmp[0])
      self.min    = getTemp(tmp[1])
      self.wind   = getWind(tmp[2])
      self.precip = getPrec(tmp[3])

  def _parseSelected( self ):
    """Get selected options in results page"""
    tmp = self._soup.find_all('option', selected=True)
    if tmp is not None:
      self.year   = tmp[0].text
      self.school = tmp[1].text.strip()
      city, state = splitCityState( tmp[2].text )
      self.day    = tmp[3].text

      self.city, self.state = city, state

  def _parseDate(self):

    tables = self._soup.find_all('table')
    if tables and len(tables) == 2:
      table = tables[1]
      rows  = table.find_all('tr')
      if rows:
        col = rows[0].find('td')
        if col:
          ref  = datetime.datetime.strptime(col.text, '%Y%m%d')
          ref += datetime.timedelta(days = len(rows)-1 )
          self.date = ref.date()
          return
        #col = rows[-1].find('td')
        #if col:
        #  print( col.text )
        #  self.date = datetime.datetime.strptime(col.text, '%Y%m%d').date()
        #  return
    self.__log.error('Failed to parse date from results page!')

  def _forecastTag( self, fc ):
    """Generate dictionary key based on forecast metadata"""
    return '{}:{}:{}'.format( fc['name'], fc['school'], fc['category'] )        # Initialize a tag for the __forecasters dictionary

  def _parseColumns( self, cols ):
    """
    Parse data from columns in table row

    All forecast information for columns in a given row are parsed into
    a dictionary

    Arguments:
      cols (bs4.element.ResultSet, list) : Column information

    Keyword argumnets:
      None.

    Returns:
      dict : Forecast data parsed to dictionary

    """

    cols = [ele.text.strip() for ele in cols]                                   # Get text for each column in the row
    cols = [ele for ele in cols if ele != '|']
    if len(cols) != len(WxData.resultsCols): return None
    fc   = {}                                                                   # Initialize data to empty list
    for i in range( len(cols) ):                                                # Iterate over all elements in the column data
      if cols[i].isdigit():                                                     # If the element is a digit
        ele = int(cols[i])                                                      # Set x to integer type of element
      else:                                                                     # Else
        try:                                                                    # Try to...
          ele = float(cols[i])                                                  # Convert element to float
        except:                                                                 # If convert to float fails
          ele = cols[i]                                                         # Keep as string
      if WxData.resultsCols[i]['name'] == 'abs' and ele == '': ele = 0 
      fc[ WxData.resultsCols[i]['name'] ] = ele 
    fc['date']       = self.date
    fc['identifier'] = self.identifier
    fc['day']        = self.day
    fc['semester']   = getSemester(self.date)
    fc['year']       = self.date.year

    return fc

  def _parseForecasts( self, table, school = None ):
    """
    Parse forecasts from table

    Arguments:
      table (bs4.element.Tag) : Table object from BeautifulSoup

    Keyword arguments:
      school (str) : 3-character code to filter by

    Returns:
      (dict) : Model forecast information

    """

    forecasts = {}
    rows  = table.find_all('tr')                                                # Get all rows of the table, i.e., all <tr> elements
    for row in rows:                                                            # Iterate over all rows
      cols = row.find_all('td')                                                 # Get all columns in the row; i.e., all <td> elements
      fc   = self._parseColumns( cols )                                         # Parse columns
      if fc is None: continue                                                   # If failed to parse columns, continue
      if school is not None:                                                    # If the school keyword is set
        if (fc['school'] != school):
          continue

      tag = self._forecastTag( fc )                                             # Generate tag for forecast
      forecasts[tag] = fc;                                                      # Add forecast to forecast dictionary

    return forecasts                                                            # Return forecasts


  def _parseModels( self, table, ncol = 27 ):
    """
    Parse model data from table

    Data returned from requests does NOT keep model data in a table row,
    so must parse individual columns from table.

    Arguments:
      table (bs4.element.Tag) : Table object from BeautifulSoup

    Keyword arguments:
      ncol (int) : Number of columns in table

    Returns:
      (dict) : Model forecast information

    """

    td = table.find_all('td', recursive = False)                                # Find all columns in table non-recursively
    forecasts = {}                                                              # Initialize forecasts dictionary

    for i in range(0, len(td), ncol):                                           # Iterate over rows (skip ncol so that get all columns in a row)
      cols = td[i:i+ncol]                                                       # Get columns in row
      fc   = self._parseColumns( cols )                                         # Parse the columns
      if fc is None: continue                                                   # If data NOT parsed, continue
      tag  = self._forecastTag( fc )                                            # Generate tag for storing data in dictionary
      forecasts[tag] = fc;                                                      # Add forecast data to dictionary

    return forecasts                                                            # Return forecasts dictionary

  def results(self, school = None):
    if self.date is None: return None

    table = self._soup.find('table')
    if table is None: return None

    forecasts = self._parseForecasts( table, school = school )                  # Initialize forecasts
    forecasts.update( self._parseModels( table ) )

    return forecasts


class WxSeason( object ):
  TBD = 'To Be Determined'

  def __init__(self, soup):
    self.__log = logging.getLogger( __name__ )
    self.soup  = soup
    self.years = None

    tmp = self.soup.find_all('option', selected=True)
    if tmp is not None:
      year = int( tmp[0].text.split('-')[0] )
      self.years = [year, year+1]

  def __repr__(self):
    return '< {} : {}-{} >'.format( self.__class__.__name__, *self.years )

  def _splitCityState(self, citySt):
    """
    Split City, ST string on comma
    
    Arguments:
      citySt (str) : Contains City, ST information
    
    Keyword arguments:
       None.
    
    Returns:
      dict : City and state information under standardized keys

    """
    self.__log.debug('Parsing city/state from schedule row')

    city, state = splitCityState( citySt )

    return {WxData.scheduleCols[0]['name'] : city, 
            WxData.scheduleCols[1]['name'] : state} 

  def _formatID(self, identifier):
    """Ensure that station ID is 4 characters, starting with 'K'"""
    self.__log.debug('Checking station identifier from schedule row')
    if len(identifier) != 4:
      identifier = 'K{}'.format(identifier)
    return {WxData.scheduleCols[2]['name'] : identifier.upper()}

  def _parseClimo(self, climo):
    """Parse climatology information into ints/floats"""
    self.__log.debug('Parsing climo data from schedule row')
    climo = climo.split('/')
    return {'max'    : int(climo[0]),
            'min'    : int(climo[1]),
            'wind'   : int(climo[2]),
            'precip' : float(climo[3])}

  def _parseDates(self, dates):
    self.__log.debug('Parsing date information from schedule row')

    start, end   = dates.split('-');                                              # Get start and end dates by splitting last column on hyphen
    sMonth, sDay = start.split()[:2];                                           # Get start month and day
    end = end.split();                                                          # Get end month and day
    if len(end) == 1:                                                           # If the length of end is one
      eMonth, eDay = sMonth, end[0];                                            # Then the end month is the same as the start month
    else:                                                                       # Else
      eMonth, eDay = end[:2];                                                   # Get end month and day

    sMonth = getMonthInt( sMonth ) 
    eMonth = getMonthInt( eMonth ) 

    year = self.years[0] if sMonth >= 7 else self.years[1]
    start  = datetime.date(year, sMonth, int(sDay))                             # Create start datetime object
    end    = datetime.date(year, eMonth, int(eDay))                             # Create start datetime object

    return {WxData.scheduleCols[-2]['name'] : start,
            WxData.scheduleCols[-1]['name'] : end}

  def _parseRow(self, city, identifier, climo, dates):
    if self.TBD in city: return None
    self.__log.debug('Parsing row from schedule')
    info = self._splitCityState( city )
    info.update( self._formatID( identifier ) )
    info.update( self._parseClimo( climo) )
    info.update( self._parseDates( dates ) )
    return info

  def parse(self):
    if self.years is None:
      raise Exception('No years defined for schedule!')
 
    table = self.soup.find('table')
    if table is None:
      log.error('Not table found, could not parse schedule!')
      return None

    sched = {}
    rows  = table.find_all('tr');                                               # Find all the rows in the table
    for row in rows:                                                            # Iterate over all the rows
      cols = [ele.text.strip() for ele in row.find_all('td') if ele]            # Iterate over all columns in the row and get the text if the column has information
      info = self._parseRow( *cols )
      if info is not None:
        key  = generateKey( info['end'] )                                         # Generate key for sched dictionary using date for the end of the forecast city
        if key not in sched: sched[key] = {}                                      # If the key key is NOT in self, initialize empty dictionary under key
        sched[key][ info['ident'] ] = info                                        # Add the info dictionary into the key dictionary using the identifier from info as the key

    return sched                                                                # Return the schedule dictionary    sched = {}
