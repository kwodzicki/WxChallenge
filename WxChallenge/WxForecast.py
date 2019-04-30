# Import column naming data
import logging

try:
  from data import forecastCols as cols;
  from data import grd_df_cols, miss_allowed, fcst_per_city, break_bonus;
except:
  from .data import forecastCols as cols;
  from .data import grd_df_cols, miss_allowed, fcst_per_city, break_bonus;
import pandas;
import numpy as np;

required       = fcst_per_city - miss_allowed
miss_penalize  = 100.0 / required;
climo_penalize =  30.0 / required;

##############################################################################
def get_level_list(input, levels):
  '''get list of MultiIndex levels'''
  lvl_vals = [];
  for i in range( len(input.index.codes) ):
    if input.index.names[i] not in levels: continue
    j = input.index.codes[i][0]
    lvl_vals.append( input.index.levels[i][j] );
  return lvl_vals;      

##############################################################################
def get_indices(values, check):
  '''get list of MultiIndex levels'''
  index = np.full( len(values[0]), True );
  for i in range( len(values) ): index = index & (values[i] == check[i]);
  return index; 

def calc_School_Norm( fcData ):
  '''
  This function returns the consensus cumulative error for
  a school and the standard deviation for the cumulative error 
  for the school using information for the latest forecast date
  in the DataFrame
  '''
  log       = logging.getLogger(__name__)
  schConsen = fcData.index.get_level_values('name') == 'CONSEN';                # Get consensus for the school for the given station
  schConsen = fcData.loc[ schConsen ];                                          # Get data for consensus for the school
  fcstDays  = schConsen.index.get_level_values('day');                          # Get the forecast days for the city, i.e., 1, 2, 3, etc.
  maxDay    = fcstDays.max();                                                   # Get latest forecast day
  id        = fcstDays == maxDay;                                               # Index of the last day
  schConErr = schConsen.loc[id]['cum_err_total'].values[0];                     # Value of the cumulative consensus error
  log.info( 'School consensus error: {}'.format( schConErr ) );
  
  fcstDays  = fcData.index.get_level_values('day');
  category  = fcData.index.get_level_values('category');
  id        = (fcstDays == maxDay) & (category < 9);
  fcConErr  = fcData.loc[id]['cum_err_total'].values;                           # Value of the cumulative consensus error
  fcConSTD  = np.std( fcConErr);                                                # Compute national cumulative error standard deviation
  log.info( 'Standard deviation of cumulative errors: {}'.format( fcConSTD ) );

  return schConErr, fcConSTD;

################################################################################
class forecasts( pandas.DataFrame ):
  '''
  Sub-class of pandas DataFrame that stores all forecast data
  read in from the SQL database using multidimensional indexing.
  The index are as follows:
    school > year > semester > identifier > day > category > name
  '''
  def __init__(self, data, columns = None, index = None):
    '''
    Name:
       __init__
    Purpose:
       A method to initialize the class
    Inputs:
       data : List of data values used to construct the DataFrame
    Outputs:
       None.
    Keywords:
       columns  : List of names for columns
       index    : List of columns to use a indices
    '''
    pandas.DataFrame.__init__(self, data, columns = columns);                   # Initialize the DataFrame
    self.log = logging.getLogger(__name__)
    if index is not None:                                                       # If index is NOT None
      self.set_index( index, inplace=True );                                    # Set columns to use as indices; done inplace
      self.sort_index( inplace = True );                                        # Sort the data using indices; done inplace
    self.grades = None;                                                         # Set grades attribute to None;
  ##############################################################################
  def get_lvl_vals(self, names = None):
    data = [];
    if names is None: names = self.index.names;
    for name in names: 
      data.append( self.index.get_level_values( name ) );
    dates  = self['date'].values;                                               # Get date values for forecasts
    info   = sorted( set( zip( *data, dates ) ), key = lambda x: x[-1] );       # Zip up the index values with the dates, find unique tuples, then sort based on date
    uniq   = [];                                                                # Array for unique values
    for i in info:                                                              # Iterate over values in info
      if i[:-1] not in uniq:                                                    # If the list (excluding date) is NOT in the uniq list
        uniq.append( i[:-1] );                                                  # Append it
    return data, uniq;                                                          # Return all data AND the uniq values
  ##############################################################################
  def calc_grades(self, model = None, vacation = None):
    '''
    Purpose:
      Method for calculating grades for forecasters
    Inputs:
      None.
    Outputs:
      None; updates the grades attribute of this class
    Keywords:
      model    : Model data to compare to
      vacation : List of tuples with start and end dates of any vacations
    '''
    gradeCol, gradeInd = self.gradeColInd();                                    # Get the column and index names to be used in the final grades DataFrame
    grades = [];                                                                # Initialize a list to store grades during iteration
    levels = ['school','year','semester','identifier'];                         # List of levels to sort by when iterating
    stVal, stUNIQ = self.get_lvl_vals( levels );                                # Get complete list of levels and list of unique levels

    if model is not None:                                                       # If model is NOT None
      mdVal, mdUNIQ = model.get_lvl_vals( levels[1:] );                         # Get complete list of levels and list of unique levels; don't use the school value
      if len(stUNIQ) != len(mdUNIQ):                                            # If the length of unique values from the forecasts does NOT match that of the model
        self.log.warning( 'Forecaster and model data missmatch!' );             # Print a message
        model = None;                                                           # Disable model
    for stid in stUNIQ:                                                         # Iterate over the unique levels
      locStat   = get_indices( stVal, stid );                                   # Get location of unique station
      fcData    = self.loc[ locStat ];                                          # Subset the forecasts using the location
      schConErr, schErrSTD = calc_School_Norm( fcData );

      if model is not None:                                                     # If model is NOT None
        locStat     = get_indices( mdVal, stid[1:] );                           # Get location of unique station in the model data
        mdData      = model.loc[ locStat ];                                     # Subset the model data using the location
        mdNames     = mdData.index.get_level_values('name');                    # Get list of level names from the subset data
        ntlConsen   = mdNames == 'CONSEN';                                      # Get location of national consensus data for the location
        ntlConsen   = mdData.loc[ ntlConsen ];                                  # Subset national consensus data for the location
        climatology = mdNames == 'CLIMO0';                                      # Get location of climatology data for the location
        climatology = mdData.loc[ climatology ];                                # Subset climatology data for the location
      
      for fcstr in self.level_iter( 'name', fcData, ['CONSEN'] ):               # Iterate over all the forecasters for the station, skipping consensus
        numDays = len( fcstr );                                                 # Number of forecast days
        if numDays == 0: 
          self.log.warning( 'No forecasts found!' );
          continue;                                                             # If there are NO forecasts for the day, continue

        abse    = 0.0
        climo   = 0.0
        sch_con = 0.0
        ntl_con = 0.0;                              # Initialize absence, climatology, school consensus, and national consensus deductions/bonuses to zero (0.0)
        vacaN   = 0
        miss    = fcstr['abs'].values;                                          # Cumulative absence array
        miss    = np.insert( (miss[1:] - miss[0:-1]), 0, miss[0]);              # Binary flag for if forecaster missed a forecast day
        nmiss   = fcstr['abs'].values.max();                                    # Get the number of missed forecasts; the maximum number from the abs column
        
        if isinstance( vacation, (list, tuple,) ):                              # If there were vacations input
          for vaca in vacation:                                                 # Iterate over the vacations
            vacaID = ( (fcstr['date'].values >= vaca[0]) & 
                      (fcstr['date'].values <= vaca[1]) )                       # Indices for days at given forecast city that are within the break
            vacaN  = sum( vacaID )
            if vacaN > 0:
              self.log.debug( 'Found {} forecasts during break'.format(vacaN) )
              nmiss  -= vacaN;                                                  # Remove number of days of break from missed forecasts count
              vacaN  -= sum( miss[vacaID] )              
        nFcsts  = numDays - nmiss;                                              # Number of forecasts submitted
        abse    = -np.clip(nmiss-miss_allowed, 0, None) * miss_penalize;        # Compute absence deductions; 2 free misses before deductions
        err     = fcstr['cum_err_total'].values[-1];                            # Get cumulative error value

        sch_con = np.clip( (schConErr - err) / schErrSTD, 0.0, None );          # Normalized difference between school error and forecaster error
        ntl_con = fcstr['norm_city'].values[-1] / 10.0;
        if ntl_con > 1.0:
          ntl_con = 0.0
        else:
          ntl_con = -ntl_con + 1.5

        if model is not None:                                                   # If model is NOT none
          if len(climatology) == numDays:                                       # If the climatology data ar the same length as the forecaster data
            fcstErr   = fcstr[      'err_total'].values;                        # Daily error for the forecaster
            climoErr  = climatology['err_total'].values;                        # Daily error for climatology
            climoNorm = climatology['norm_city'].values / 10.0;                 # Cumulative normalized climatology error for the city; scaled back to standard deviations

            climo = (miss == False) & (climoErr < fcstErr) & (climoNorm > 2.0); # Boolean for forecast NOT missed, climatology error less than forecast error, and normalized climo error worse than 2 standard deviations from national consensus
            climo = -climo_penalize * np.clip(sum(climo), 0, required);         # Multiply by climo penalization

        score = 100.0 + abse + climo;                                           # Compute score; do NOT include beating national or school consensus
        indVals = get_level_list(fcstr, gradeInd);                              # Get the values for, what will be, the index columns
        grades.append( 
          indVals+[nFcsts, abse, vacaN, climo, sch_con, ntl_con, score]
        );# Append grades to the grades list
    self.grades = pandas.DataFrame(grades, columns = gradeCol);                 # Initialize DataFrame using grades list and gradeCols for columns
    if gradeInd is not None:                                                    # If columns to use as indices is NOT None
      self.grades.set_index(gradeInd, inplace=True);                            # Set columns to use as indices; inplace
    
    school_con = self.grades[ gradeCol[-3] ].values
    self.grades[ gradeCol[-3] ] = (school_con / school_con.max())
  ##############################################################################
  def iterForecasters(self, grades = False):
    '''
    Name:
       interForecasters
    Purpose:
       A method to create a generator that iterates over all unique
       forecasters in the DataFrame, returning a forecaster instance
       containing all the data associated with that forecaster
    Inputs:
       None.
    Outputs:
       Yields a forecaster instance
    Keywords:
       grades : Set to return forecaster instance containing grades.
                 Default is to return instance containing raw scores.
    '''
    if grades:
      names = self.grades.index.get_level_values( 'name' );                     # Get all unique forecaster names
    else:
      names = self.index.get_level_values( 'name' );                            # Get all unique forecaster names
    namesUNIQ = names.unique();
    for name in namesUNIQ:
      if grades:
        yield forecaster( self.grades.loc[ names == name ], name, grades);
      else:
        yield forecaster( self.loc[ names == name ], name, grades );
  ##############################################################################
  def gradeColInd(self):
    '''
    Name:
       gradeColInd
    Purpose:
       A method to obtain the column names and index names to use
       in the grades attribute DataFrame
    Inputs:
       None.
    Outputs:
       cols : List of column names to use in the grades attribute DataFrame
       inds : List of column names to be used a indices in grades attr.
    Keywords:
       None.
    '''
    cols, inds = grd_df_cols, self.index.names;                                 # Initialize columns using grd_df_cols values from data.py and initialize inds using the indices of the self DataFrame 
    if inds[0] is None:                                                         # If there are no indices currently defined for the self DataFrame
      inds = None;                                                              # Set inds to None
    else:                                                                       # Else
      inds = list(inds); inds.remove('day');                                    # Convert inds to a mutable list and remove the 'day' tag from it
      cols = inds + cols;                                                       # Set cols to inds + cols
    return cols, inds;                                                          # Return cols and inds
  ##############################################################################
  def name_iter(self, names, data = None):
    '''
    Purpose:
      Method for creating iterator over forecaster names
    Inputs:
      names: List of names
    Outputs:
      Returns iterator
    Keywords:
      data     : Dictionary of data
    '''
    if data is None:
      for name in names:
        yield self.loc[ self.index.get_level_values('name') == name ];
    else:
      for name in names:
        yield data[ data.index.get_level_values('name') == name ];
  ##############################################################################
  def identifier_iter(self, identifier, data = None):
    '''
    Purpose:
      Method for creating iterator over forecast cities
    Inputs:
      names: List of city identifiers
    Outputs:
      Returns iterator
    Keywords:
      data     : Dictionary of data
    '''
    if data is None:
      for ident in identifier:
        yield self.loc[ self.index.get_level_values('identifier') == ident ];
    else:
      for ident in identifier:
        yield data[ data.index.get_level_values('identifier') == ident ];
  ##############################################################################
  def level_iter(self, level, data = None, skip = []):
    '''
    Purpose:
      Method for creating iterator over forecaster level (freshman/sophomore, etc.)
    Inputs:
      names: List of forecaster levels
    Outputs:
      Returns iterator
    Keywords:
      data     : Dictionary of data
    '''
    if data is None:
      values = self.index.get_level_values(level);
      for val in values.unique(): 
        if val not in skip: yield self.loc[ values == val ];
    else:
      values = data.index.get_level_values(level);
      for val in values.unique(): 
        if val not in skip: yield data[ values == val ];
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
class forecaster( pandas.DataFrame ):
  _categories = {0 : 'Professional', 
                 1 : 'Faculty/Staff/Post-Doc',
                 2 : 'Grad-Student',
                 3 : 'Junior/Senior',
                 4 : 'Freshman/Sophomore'}

  def __init__(self, data = None, name = None, grades = False):

    pandas.DataFrame.__init__(self, 
      data    = data
    );

    self.name      = name;
    self.category  = self.index.get_level_values('category'  ).values[0];
    self.school    = self.index.get_level_values('school'    ).values[0];
    self.semester  = self.index.get_level_values('semester'  ).values[0];
    self.year      = self.index.get_level_values('year'      ).values[0];
    self.is_grades = grades;
    self.is_climo  = 'CLIMO' in self.name.upper();
    self.is_model  = self.category == 8;
    self.is_consen = self.category == 9;
        
  ##############################################################################
  def getCities(self):
    '''
    Name:
       getCities
    Purpose:
       A method to return all unique city names for the forecaster
    Inputs:
       None.
    Outputs:
       Returns a numpy ndarray containing unique city identifiers
    Keywords:
       None.
    '''
    vals = self.index.get_level_values('identifier').unique();                  # Get all 'identifier' values, find just unique
    return vals.values.astype( str );                                           # Get get the values as type str and return
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