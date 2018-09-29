# Import column naming data
try:
  from data import forecastCols as cols;
except:
  from .data import forecastCols as cols;
import pandas;
import numpy as np;

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
class forecaster( pandas.DataFrame ):
  _categories = {0 : 'Professional', 
                 1 : 'Faculty/Staff/Post-Doc',
                 2 : 'Grad-Student',
                 3 : 'Junior/Senior',
                 4 : 'Freshman/Sophomore'}

  def __init__(self, data = None, index = None, columns = None, dtype = None, copy = False,
    name = None, school = None, category = None, semester = None, year = None):

    pandas.DataFrame.__init__(self, 
      data    = data, 
      index   = index,  
      columns = [i['name'] for i in cols if i['pandas_col']] if columns is None else columns,
      dtype   = dtype,
      copy    = copy
    );

    self.name      = name;
    self.category  = category;
    self.school    = school;
    self.semester  = semester;
    self.year      = year;
    self.grades    = None;
    self.is_climo  = 'CLIMO' in name.upper();
    self.is_model  = category == 8;
    self.is_consen = category == 9;
    
#     for i in range(len(cols)):                                                  # Iterate over forecast data column names
#       if cols[i]['name'] == 'date': self.__dateid = i;                          # Locate the date column
#       if not hasattr(self, cols[i]['name']): setattr(self, cols[i]['name'], []);# Initialize attribute with forecast date column name as empty list
    
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
    data = {};
    for i in range( len(forecast_data) ):                                       # Iterate over all columns
      if cols[i]['name'] == 'date': name = forecast_data[i];
      if cols[i]['pandas_col']: data[ cols[i]['name'] ] = forecast_data[i];
    self.loc[ name ] = data;
    self.sort_index(inplace=True);
    return True;                                                                # Return True
  ##############################################################################
  def calc_grade(self, climatology = None, sch_consensus = None, ntnl_consensus = None, verbose = False):
    '''
    Purpose:
       Method for computing grade for forecaster.
    Inputs:
       None.
    Keywords:
       climatology    : Single, or list of forecaster instance for climatology(ies)
       sch_consensus  : Forecaster instance for school consensus
       ntnl_consensus : Forecaster instance for national consensus
    '''
    climo, sch_con, ntl_con = 0.0, 0.0, 0.0;                                    # Initialize climo value to zero (0)
    self.grades = pandas.DataFrame(
      columns=['Forecasts', 'Absence', 'Climo', 'Consen. School', 'Consen. Ntnl', 'Total']
    );

    if verbose:
      head_FMT = '{:12}|{:^21}|{:^21}|\n{:5}| {:^4} |{:^10}|{:^10}|{:^10}|{:^10}|{:^10}';
      row_FMT  = '{:5}| {:4} |{:9.2f} |{:9.2f} |{:9.2f} |{:9.2f} |{:9.2f}';
      fmt      = 'Name: {}    School: {}   Semester: {} {}'
      line     = ''.join( ['-'] * 68 )
      if self.is_model: 
        fmt += ' (model)'
      elif self.is_consen:
        fmt += ' (consensus)'
      print( fmt.format(self.name, self.school, self.semester, self.year) );
      print( head_FMT.format('','Deductions','Bonus','ID', 'Forecasts', 'Absence','Climo','School','National','Total') )
      print( line );

    for id in self['identifier'].unique():                                      # Iterate over the unique station identifiers
      vals    = self.loc[ self['identifier'] == id ];                           # Locate all the rows with the identifier
      numDays = len(vals);
      if numDays > 0:
        miss    = vals['abs'].values != 0;                                      # Array of boolean values to check absence from game
        nFcsts  = numDays - miss.sum();                                         # Number of forecasted submitted
        abse    = -np.clip(miss.sum()-2, 0, None)*14.286;                       # Compute absence deductions; 2 free misses before deductions
        err     = vals.loc[ vals['day'] == numDays ];                           # Get row for the last day of the contest at given city
        err     = err['cum_err_total'].values[0];                               # Get cumulative error value
        if climatology is not None:                                             # If climatology is not None
          climo_err = [];                                                       # Initialize climo_err as a list
          if type(climatology) is not list and type(climatology) is not tuple:  # If climatology is NOT list and it is NOT tuple
            climatology = [climatology];                                        # Convert it to a list
          for cli in climatology:                                               # Iterate over DataFrames in the climatology list
            tmp = cli.loc[ cli['identifier'] == id ];                           # Locate all values for the station
            if len(tmp) > 0: climo_err.append( tmp['err_total'].values );       # If values are found above, then
#           tmp = np.array(climo_err).max(axis=0) < vals['err_total'].values;     # Compute max over the two climatologies
#           climo = -sum(tmp & (miss == False)) * 6;                              # Compute climatology deductions
        if sch_consensus is not None:                                           # If sch_consensus is not None
           tmp = sch_consensus.loc[ sch_consensus['identifier'] == id ];        # Locate all values for the station
           if len(tmp) > 0:                                                     # If values are found above, then
             tmp     = tmp.loc[ tmp['day'] == max( tmp['day'] ) ];              # Get row for the last day of the contest at given city
             sch_con = tmp['cum_err_total'].values[0];                          # Get cumulative error value
             sch_con = 0.5 if err < sch_con else 0.0;                           # If forecaster error is less than school consensus, set sch_con to 0.5, else, set it to zero
        if ntnl_consensus is not None:                                          # If ntnl_consensus is not None
           tmp = ntnl_consensus.loc[ ntnl_consensus['identifier'] == id ];      # Locate all values for the station
           if len(tmp) > 0:                                                     # If values are found above, then
             tmp     = tmp.loc[ tmp['day'] == max( tmp['day'] ) ];              # Get row for the last day of the contest at given city
             ntl_con = tmp['cum_err_total'].values[0];                          # Get cumulative error value
             ntl_con = 1.0 if err < ntl_con else 0.0;                           # If forecaster error is less than national consensus, set ntl_con to 1.0, else, set it to zero
  
        score = 100.0 + abse + climo + sch_con + ntl_con;                       # Compute score for missing; give them 2 free misses a week, after that subtract 14.286 (1/7th of 100) for every missed day
        self.grades.loc[id] = [nFcsts, abse, climo, sch_con, ntl_con, score];
        if verbose:
          print( row_FMT.format(id,nFcsts,abse,climo,sch_con,ntl_con,score) );
    if verbose:
      print( line );
      print( '{:>55} |{:9.2f}\n'.format('Average', self.grades['Total'].mean()) );
    return self.grades['Total'].mean()
             
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