import logging 
from datetime import date

from .utils import generateKey#, updateSchedule;
from .parsers import parse_schedule


class WxSchedule( dict ):
  def __init__(self):
    super().__init__()
    self.date   = date.today()
    self.latest = None;                                                         # Initialize latest attribute to None
    self.log    = logging.getLogger( __name__ );
  ##############################################################################
  def Update(self, season):
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
    self.log.debug( type(season) );
    self.log.debug( season )
    for semYear in season:                                                        # Iterate over all semesters/years
      if not isinstance( season[semYear], dict ):                                 # If NOT a nested dictionary
        key  = generateKey( season['end'] );                                      # Generate key for 
        self.updateLatest( season['end'] )
        season = { key : {season['ident'] : season} };                                # Add the info dictionary into the key dictionary using the identifier from info as the key
        break;
      else:                                                                     # Else, is a nested dictionary
        for city in season[semYear]:                                              # Iterate over all identifiers
          self.updateLatest( season[semYear][city]['end'] )
    for key in season:
      if key in self:
        self[key].update( season[key] )
      else:
        self[key] = season[key];
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
 
