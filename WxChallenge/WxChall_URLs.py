from bs4 import BeautifulSoup;

# Handle both Python2 and Python3
try:
  from urllib import urlopen;
except:
  from urllib.request import urlopen;

class WxChall_URLs(object):
  def __init__(self):
    self.base_URL    = 'http://wxchallenge.com';
    self.resultFMT   = '/history/results/{}/{}_results_{}_day{}.html';
    self.curSchedFMT = '{}/challenge/schedule.php'
    self.schedFMT    = '{}/challenge/schedule_{}{}.php'
  ##############################################################################
  def getResultsURL(self, semester, year, identifier, school, day, soup = False):
    if semester.lower() == 'spring':
      year = '{}-{}'.format(str(year-1)[-2:], str(year)[-2:]);                # Set up the year part of the url
    else:    
      year = '{}-{}'.format(str(year)[-2:], str(year+1)[-2:]);                # Set up the year part of the url
    url = self.resultFMT.format(year, identifier.lower(), school, day);
    if soup:
      return self.checkURL( self.base_URL + url );
    else:
      return self.base_URL + url;
  ##############################################################################
  def getScheduleURL(self, sYear = None, eYear = None, current = False, soup = False):
    if current:
      url = self.curSchedFMT.format( self.base_URL );
    elif sYear is not None and eYear is not None:
      url = self.schedFMT.format( self.base_URL, sYear, eYear );
    else:
      return None;
    if soup:
      return self.checkURL( url );
    else:
      return url
  ##############################################################################
  def checkURL(self, url):
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
