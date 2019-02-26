import logging 
try:
  from .utils import generateKey;#, updateSchedule;
  from parsers import parse_schedule;
except:
  from .utils import generateKey;#, updateSchedule;
  from .parsers import parse_schedule;

from datetime import date;

class WxChall_Schedule( dict ):
  def __init__(self):
    dict.__init__(self);
    self.date   = date.today()
    self.latest = None;                                                         # Initialize latest attribute to None
    self.log    = logging.getLogger( __name__ );
  ##############################################################################
  def Update(self, info):
    '''
    Name:
       Update
    Purpose:
       A method to update some information.
    Inputs:
       info  : A dictionary or BeautifulSoup table instance
    Outputs:
       None.
    Keywords:
       None.
    '''
    self.log.debug( type(info) );
    if not isinstance( info, dict ):                                            # If info is NOT a dictionary instance
      info = parse_schedule( info );                                            # Assume it is a BeautifulSoup table and parse it
    self.log.debug( info )
    for semYear in info:                                                        # Iterate over all semesters/years
      if not isinstance( info[semYear], dict ):                                 # If NOT a nested dictionary
        key  = generateKey( info['end'] );                                      # Generate key for 
        self.updateLatest( info['end'] )
        info = { key : {info['ident'] : info} };                                # Add the info dictionary into the key dictionary using the identifier from info as the key
        break;
      else:                                                                     # Else, is a nested dictionary
        for city in info[semYear]:                                              # Iterate over all identifiers
          self.updateLatest( info[semYear][city]['end'] )
    for key in info:
      if key in self:
        self[key].update( info[key] )
      else:
        self[key] = info[key];
  ##############################################################################
  def Clear(self):
    '''
    Name:
       Clear
    Purpose:
       A wrapper method for the dict.clear() method
    Inputs:
       None.
    Outputs:
       None.
    Keywords:
       None.
    '''
    self.clear();                                                               # Clear all information from the dictionary
    self.latest = None;                                                         # Set latest attribute to None
  ##############################################################################
  def updateLatest(self, date):
    if date <= self.date:                                                       # If the start date of the city is less than or equal to today's date
     if self.latest is None:                                                    # If the latest attribute is None
       self.latest = date;                                                      # Set the latest attribute to the start date of the info dictionary
     elif date > self.latest:                                                   # Else, if the latest attribute is before the start date in info dictionary
       self.latest = date;                                                      # Set latest to the start date in the info dictionary
 