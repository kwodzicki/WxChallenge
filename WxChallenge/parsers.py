import logging

import datetime

from . import data as WxData;
from .utils import getSemester, generateKey;#updateSchedule;

getTemp = lambda x: int( x.split(u'\xb0')[0][1:] )                              # Lambda function to pull out temperature from string
getWind = lambda x: int( x )                                                    # Lambda function to pull out wind from string
getPrec = lambda x: float( x.split('"')[0] )                                    # Lambda function to pull out precip from string

################################################################################
def getMonthInt( month ):
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
    return ','.join( citySt[:-1] ), citySt[-1] 
  return citySt[0], ''



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
      for i in range(len(tmp)):
        tmp[i] = tmp[i].split()[0]
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
        col = rows[-1].find('td')
        if col:
          self.date = datetime.datetime.strptime(col.text, '%Y%m%d')
          return
    raise Exception('No date parsed from results page!')

  def results(self, school = None):
    forecasts = {};                                                               # Initialize forecasts
    table = self._soup.find('table')
    if table is None: return None

    rows  = table.find_all('tr');                                                   # Get all rows of the table, i.e., all <tr> elements
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
      if school is not None:                                                    # If the school keyword is set
        if fc['school'] != school: continue;                                    # If the current school name is NOT in the list of schools, then continue
      
      fc['date']       = self.date
      fc['identifier'] = self.identifier
      fc['day']        = self.day
      fc['semester']   = getSemester(self.date)
      fc['year']       = self.date.year

      tag = '{}:{}:{}'.format( fc['name'], fc['school'], fc['category'] );        # Initialize a tag for the __forecasters dictionary
      forecasts[tag] = fc;                                                        # If the tag does NOT exist in the __forecasters dictionary, then initialize list under the tag
    return forecasts;


class WxSchedule( object ):
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

    sMonth = getMonthInt( eMonth ) 
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
  
def parse_schedule( soup ):
  """
  Parse information from the WxChallenge forecast schedule
  
  This function will parse the forecast city schedule from the weather
  challenge page to determine what city (id) goes with a given date.

  Arguments:
    soup (BeautifulSoup) : A bs4.BeautifulSoup object

  Keyword Arguments:
    None.

  Retunrs:
     dict : Parsed schedule information

  """

  log   = logging.getLogger(__name__)

  sched = {}                                                                    # Initialize empty dictionary
  table = soup.find('table')
  if table is None:
    log.error('Not table found, could not parse schedule!')
    return None

  rows  = table.find_all('tr');                                                 # Find all the rows in the table
  for row in rows:                                                              # Iterate over all the rows
    cols = [ele.text.strip() for ele in row.find_all('td') if ele]             # Iterate over all columns in the row and get the text if the column has information
    info = parse_city( *cols )
    if info is None: continue
    try:                                                                        # Try to
      city, state = cols[0].split(',')[:2];                                     # Get city and state by splitting on comma and taking first 2 values
    except:                                                                     # On exception
      city, state = cols[0], '';                                                # Get city as first column value and set state to empty string
    if len(cols[1]) != 4: cols[1] = 'K' + cols[1];                              # If the ID is NOT 4 characters long, then prepend a K
    info   = {WxData.scheduleCols[0]['name'] : city, 
              WxData.scheduleCols[1]['name'] : state, 
              WxData.scheduleCols[2]['name'] : cols[1], 
              WxData.scheduleCols[3]['name'] : start, 
              WxData.scheduleCols[4]['name'] : end};                            # Create info dictionary with all information for forecast city
    key = generateKey( end );                                                   # Generate key for sched dictionary using date for the end of the forecast city
    if key not in sched: sched[key] = {};                                       # If the key key is NOT in self, initialize empty dictionary under key
    sched[key][ info['ident'] ] = info;                                         # Add the info dictionary into the key dictionary using the identifier from info as the key
  return sched;                                                                 # Return the schedule dictionary
