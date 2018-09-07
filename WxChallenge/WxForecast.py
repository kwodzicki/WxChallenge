# Import column naming data
try:
  from data import forecastCols as cols;
except:
  from .data import forecastCols as cols

from pandas import DataFrame;
################################################################################
################################################################################
################################################################################
class forecasts( object ):
  def __init__(self, forecasters):
    self.forecasters = forecasters;
  ##############################################################################
  def by_school(self, fcst_in = None):
    '''
    Generator method to iterate over forecasters by school.
    Inputs:
      fcst_in : list of forecasters; useful in secondary sorting.
    Outputs:
      Yields school code and list of forecasters
    '''
    tmp = fcst_in if fcst_in else self.forecasters
    schools = sorted( set([i.school for i in tmp]) );                           # Get unique list of schools and sort
    for school in schools:                                                      # Iterate over all schools
      forecasters = [i for i in tmp if i.school == school];                     # Get list of all forecasters from school
      yield school, forecasters;
  ##############################################################################
  def by_category(self, fcst_in = None):
    '''
    Generator method to iterate over forecasters by category.
    Inputs:
      fcst_in : list of forecasters; useful in secondary sorting.
    Outputs:
      Yields school code and list of forecasters
    '''
    tmp = fcst_in if fcst_in else self.forecasters
    categories = sorted( set([i.category for i in tmp]) );                      # Get unique list of schools and sort
    for category in categories:                                                 # Iterate over all schools
      forecasters = [i for i in tmp if i.category == category];                 # Get list of all forecasters from school
      yield category, forecasters;
  ##############################################################################
  def by_semester(self, fcst_in = None):
    '''
    Generator method to iterate over forecasters by semester.
    Inputs:
      fcst_in : list of forecasters; useful in secondary sorting.
    Outputs:
      Yields school code and list of forecasters
    '''
    tmp = fcst_in if fcst_in else self.forecasters
    semYears = sorted( set(['{} {}'.format(i.semester, i.year) for i in tmp]) );       # Get unique list of schools and sort
    for semYear in semYears:                                                           # Iterate over all schools
      forecasters = [i for i in tmp if '{} {}'.format(i.semester, i.year) == semYear]; # Get list of all forecasters from school
      yield semYear, forecasters;
    
    
################################################################################
################################################################################
################################################################################
class forecaster( object ):
  def __init__(self, name, category, school, semester, year):
    self.name      = name;
    self.category  = category;
    self.school    = school;
    self.semester  = semester;
    self.year      = year;
    self.is_model  = category == 8;
    self.is_consen = category == 9;
    self.nforecast = 0;
    for i in range(len(cols)):                                                  # Iterate over forecast data column names
      if cols[i]['name'] == 'date': self.__dateid = i;                          # Locate the date column
      if not hasattr(self, cols[i]['name']): setattr(self, cols[i]['name'], []);# Initialize attribute with forecast date column name as empty list
    
  ##############################################################################
  def add_forecast(self, forecast_data):
    '''
    Method to append forecast data to lists of forecast data.
    Inputs:
      forecast_data : List of forecast data for one forecast. 
                       Ideally this data has been returned by 
                       an SQL query.
    Outputs:
      Returns False if forecast is not for forecaster represented by class.
      Returns True if data was added.
    '''
    if len(forecast_data) != len(cols): 
      raise Exception('Data is not the correct length!');                       # Raise exception if data is not correct length
    if not self.__check_forecast(forecast_data): return False;                  # If forecast is NOT for the forecaster represented by this class, return False
    if self.nforecast == 0:                                                     # If there are no forecasts in the class yet
      self.__insert_data(0, forecast_data);                                     # Add the forecast data to the appropriate attributes
    elif forecast_data[self.__dateid] < self.__dict__['date'][0]:               # If the date of the forecast is less than the first date in the list of forecasts
      self.__insert_data(0, forecast_data);                                     # Add the forecast data to the appropriate attributes
    elif forecast_data[self.__dateid] > self.__dict__['date'][-1]:              # If the date of the forecast is greater than the last date in the list of forecasts
      self.__insert_data(self.nforecast, forecast_data);                        # Add the forecast data to the appropriate attributes
    else:                                                                       # Else, data goes somewhere in the middle
      dates = getattr(self, 'date');                                            # Get the date list
      for id in range( self.nforecast-1 ):                                      # Iterate over all the forecasts
        if dates[id] < forecast_data[self.__dateid] < dates[id+1]: break;       # If the date at i is less than the current date, and the date at i+1 is greater than the current date, break the loop
      id += 1;                                                                  # Increment id by one (1)
      self.__insert_data(id, forecast_data);                                    # Add the forecast data to the appropriate attributes
    self.nforecast += 1;                                                        # Increment the number of forecasts by one (1)
    return True;                                                                # Return True
  ##############################################################################
  def __check_forecast(self, data):
    '''
    Private method to check that a forecast is for the forecaster
    defined in the class.
    '''
    n = 0;                                                                      # Initialize n to zero
    for dd in data:                                                             # Iterate over all values in the data list
      if dd == self.name:                                                       # If the value matches the name attribute
        n += 1;                                                                 # Increment n by 1
      elif dd == self.category:                                                 # If the value matches the category attribute
        n += 1;                                                                 # Increment n by 1
      elif dd == self.school:                                                   # If the value matches the school attribute
        n += 1;                                                                 # Increment n by 1
      elif dd == self.semester:                                                 # If the value matches the semester attribute
        n += 1;                                                                 # Increment n by 1
      elif dd == self.year:                                                     # If the value matches the year attribute
        n += 1;                                                                 # Increment n by 1
    return n >= 5;                                                              # Return True if n is 5; i.e., all checks matched
  ##############################################################################
  def __insert_data(self, index, data):
    '''
    Private method for actually inserting data in to lists
    '''
    for i in range( len(data) ):                                                # Iterate over all columns
      if type(self.__dict__[ cols[i]['name'] ]) is list:                        # If the data is of type list
        self.__dict__[ cols[i]['name'] ].insert(index, data[i]);                # Append the data to the appropriate key in the class dictionary
  ##############################################################################
  def exists(self, name, category, school, semester, year):
    return (
      self.name     == name       and 
      self.category == category   and
      self.school   == school     and
      self.semester == semester   and
      self.year     == year
    )   
  ##############################################################################
  def __eq__(self, comp):
    '''
    Private method for determining if two forecasters match
    '''
    return (
      self.name     == comp.name       and 
      self.category == comp.category   and
      self.school   == comp.school     and
      self.semester == comp.semester   and
      self.year     == comp.year
    )   