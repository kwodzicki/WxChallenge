# Import column naming data
try:
  from data import forecastCols as cols;
  from data import grd_df_cols;
except:
  from .data import forecastCols as cols;
  from .data import grd_df_cols;
import pandas;
import numpy as np;


##############################################################################
def get_level_list(input, levels):
  '''get list of MultiIndex levels'''
  lvl_vals = [];
  for i in range( len(input.index.labels) ):
    if input.index.names[i] not in levels: continue
    j = input.index.labels[i][0]
    lvl_vals.append( input.index.levels[i][j] );
  return lvl_vals;      

##############################################################################
def get_indices(values, check):
  '''get list of MultiIndex levels'''
  index = np.full( len(values[0]), True );
  for i in range( len(values) ): index = index & (values[i] == check[i]);
  return index; 
  
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
    return data, set( [i for i in zip(*data)] );
  ##############################################################################
  def calc_grades(self, model = None):
    gradeCol, gradeInd = self.gradeColInd();                                    # Get the column and index names to be used in the final grades DataFrame
    grades = [];                                                                # Initialize a list to store grades during iteration
    levels = ['school','year','semester','identifier'];                         # List of levels to sort by when iterating
    stVal, stUNIQ = self.get_lvl_vals( levels );                                # Get complete list of levels and list of unique levels
    if model is not None:                                                       # If model is NOT None
      mdVal, mdUNIQ = model.get_lvl_vals( levels[1:] );                         # Get complete list of levels and list of unique levels; don't use the school value
      if len(stUNIQ) != len(mdUNIQ):                                            # If the length of unique values from the forecasts does NOT match that of the model
        print( 'Forecaster and model data missmatch!' );                        # Print a message
        model = None;                                                           # Disable model
    for stid in stUNIQ:                                                         # Iterate over the unique levels
      locStat   = get_indices( stVal, stid );                                   # Get location of unique station
      fcData    = self.loc[ locStat ];                                          # Subset the forecasts using the location
      schConsen = fcData.index.get_level_values('name') == 'CONSEN';            # Get consensus for the school for the given station
      schConsen = fcData.loc[ schConsen ];                                      # Get data for consensus for the school

      if model is not None:                                                     # If model is NOT None
        locStat     = get_indices( mdVal, stid[1:] );                           # Get location of unique station in the model data
        mdData      = model.loc[ locStat ];                                     # Subset the modeld data using the location
        mdNames     = mdData.index.get_level_values('name');                    # Get list of level names from the subset data
        ntlConsen   = mdNames == 'CONSEN';                                      # Get location of national consensus data for the location
        ntlConsen   = mdData.loc[ ntlConsen ];                                  # Subset national consensus data for the location
        climatology = mdNames == 'CLIMO0';                                      # Get location of climatology data for the location
        climatology = mdData.loc[ climatology ];                                # Subset climatology data for the location
      
      for fcstr in self.level_iter( 'name', fcData, ['CONSEN'] ):               # Iterate over all the forecasters for the station, skipping consensus
        numDays = len( fcstr );                                                 # Number of forecast days
        if numDays == 0: continue;                                              # If there are NO forecasts for the day, continue
        abse    = climo = sch_con = ntl_con = 0.0;                              # Initialize absence, climatology, school consensus, and national consensus deductions/bonuses to zero (0.0)
        miss    = fcstr['abs'].values != 0;                                     # Array of boolean values to check absence from game
        nmiss   = fcstr['abs'].values.max();                                    # Get the number of missed forecasts; the maximum number from the abs column
        nFcsts  = numDays - nmiss;                                              # Number of forecasted submitted
        abse    = -np.clip(nmiss-2, 0, None)*14.286;                            # Compute absence deductions; 2 free misses before deductions
        err     = fcstr['cum_err_total'].values[-1];                            # Get cumulative error value
        if len(schConsen) == numDays:                                           # If the school consensus data are the same length as the forecaster data
          sch_con = schConsen['cum_err_total'].values[-1];                      # Get row for the last day of the contest at given city
          sch_con = 0.5 if err < sch_con else 0.0;                              # If forecaster error is less than school consensus, set sch_con to 0.5, else, set it to 0.0
        if model is not None:                                                   # If model is NOT none
          if len(ntlConsen) == numDays:                                         # If the national consensus data are the same length as the forecaster data
            ntl_con = ntlConsen['cum_err_total'].values[-1];                    # Get cumulative national consensus error on last day of city
            ntl_con = 1.0 if err < ntl_con else 0.0;                            # If forecaster error is less than national consensus, set ntl_con to 1.0, else, set it to 0.0
          if len(climatology) == numDays:                                       # If the climatology data ar the same length as the forecaster data
            fcstErr  = fcstr[      'err_total'].values;                         # Daily error for the forecaster
            climoErr = climatology['err_total'].values;                         # Daily error for climatology
            climo    = -6 * sum( (miss == False) & (climoErr < fcstErr) );      # Compute boolean array that is True when forecaster DID forecast but did NOT beat climatology. Sum number of True, multiply by -6
        score = 100.0 + abse + climo + sch_con + ntl_con;                       # Compute score for missing; give them 2 free misses a week, after that subtract 14.286 (1/7th of 100) for every missed day
        indVals = get_level_list(fcstr, gradeInd);                              # Get the values for, what will be, the index columns
        grades.append( indVals+[nFcsts, abse, climo, sch_con, ntl_con, score] );# Append grades to the grades list
    self.grades = pandas.DataFrame(grades, columns = gradeCol);                 # Initialize DataFrame using grades list and gradeCols for columns
    if gradeInd is not None:                                                    # If columns to use as indices is NOT None
      self.grades.set_index(gradeInd, inplace=True);                            # Set columns to use as indices; inplace
      self.grades.sort_index(inplace=True);                                     # Sort based on index; inplace
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
    if data is None:
      for name in names:
        yield self.loc[ self.index.get_level_values('name') == name ];
    else:
      for name in names:
        yield data[ data.index.get_level_values('name') == name ];
  ##############################################################################
  def identifier_iter(self, identifier, data = None):
    if data is None:
      for ident in identifier:
        yield self.loc[ self.index.get_level_values('identifier') == ident ];
    else:
      for ident in identifier:
        yield data[ data.index.get_level_values('identifier') == ident ];
  ##############################################################################
  def level_iter(self, level, data = None, skip = []):
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