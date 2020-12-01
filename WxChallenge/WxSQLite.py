import logging
import sqlite3, os

from pandas import DataFrame

from . import data as WxData
from .WxForecast import Forecaster, Forecasts
from .WxGrabber import WxGrabber
from .WxSchedule import WxSchedule


_dir = os.path.dirname(os.path.abspath(__file__));
_sql_file = os.path.join(_dir, 'WxChall.sql');

class WxSQLite( WxGrabber ):
  ##############################################################################
  def __init__(self, *args, file = _sql_file, verbose = False, **kwargs):
    super().__init__(*args, **kwargs)

    self.__log     = logging.getLogger( __name__ )
    self.verbose = verbose
    self.sqlFile = file
    self.db      = sqlite3.connect( self.sqlFile, detect_types=sqlite3.PARSE_DECLTYPES )
    self.cursor  = self.db.cursor()
    self.__createTables()

    self._schedule = WxSchedule()
    self.sql_Load_Schedule()
    
    if len(self._schedule) == 0: 
      self.__log.debug('No schedule found in database, downloading')
      self.download_Schedule(all=True)
    elif self._schedule.date > self._schedule.latest:                                      # If the current _date is greater than the latest date in the schedule
      self.__log.debug('Schedule is old, updating...')
      self.download_Schedule( year = self._schedule.date.year )                         # Update the schedule
    else:
      self.__log.debug('Schedule is current, nothing to do')
    self.__log.debug( self._schedule.date > self._schedule.latest )                                      # If the current _date is greater than the latest date in the schedule

  def add_verification( self, wxResult ):
    fcst_vars = [ ele['name'] for ele in WxData.verifyCols     ]                # List of variable names for all columns in the SQL forecasts table
    chck_vars = [ ele         for ele in WxData.verifyChckCols ]                # List of variable names for checking if a forecast exists
    whr       = self.__buildWhere( chck_vars )                                  # Build a 'WHERE (var1=? AND var2=?...)' statement based on the variables in the forecast check list
    ins       = self.__buildInsert( fcst_vars )                                 # Build a '() VALUES ()' statement based on the columns in the forecast table
    whr_cmd   = 'SELECT * from verifications {}'.format( whr )                  # Build full command to look for entry
    ins_cmd   = 'INSERT INTO verifications {}'.format(   ins )                  # Build full command to insert data

    chck_vals = [ wxResult.city, wxResult.state, wxResult.identifier, wxResult.date] # Get value to go in each column from the info dictionary
    fcst_vals = [ wxResult.max,  wxResult.min,   wxResult.wind,       wxResult.precip] # Get value to go in each column from the info dictionary
    fcst_vals = chck_vals + fcst_vals
    self.cursor.execute( whr_cmd, chck_vals );                                  # Execute the command
    fcst = self.cursor.fetchone();                                              # Attempt to get the forecast matching the conditions
    if not fcst:                                                                # If there is nothing found, then
      self.cursor.execute( ins_cmd, fcst_vals );                                # Execute the command
    else:                                                                       # Else, must check the values in the table 
      upd_var, upd_val = [], [];                                                # Lists to store key/value pairs for data that must be updated in the SQL forecasts table
      for i in range( len(fcst) ):                                              # Iterate over all the forecast values
        if fcst[i] != fcst_vals[i]:                                             # If the value from the SQL table does NOT match the current forecast value
          upd_var.append( fcst_vars[i] );                                       # Append the variable name to the upd_var list
          upd_val.append( fcst_vals[i] );                                       # Append the value to the upd_var list
      if len(upd_var) > 0:                                                      # If there are values to update
        upd = self.__buildUpdate( upd_var );                                    # Build a 'SET key=?, key=?' statement  based on the columns in 
        upd_cmd = 'UPDATE verifications {} {}'.format( upd, whr );              # Build the update command
        self.cursor.execute( upd_cmd, upd_val + chck_vals );                    # Update the values
    self.db.commit();                                                           # Write all changes to the database  

  def add_forecasts(self, forecasts):
    """
    Add forecast results to database

    Arguments:
      forecasts (dict) : Forecasts to add to database

    Keyword arguments:
      None.

    Returns:
      None.
    
    """

    if forecasts is None:
      self.__log.warning( 'Invalid forecast data input...Skipping' )
      return

    fcst_vars = [ ele['name'] for ele in WxData.forecastCols ]                  # List of variable names for all columns in the SQL forecasts table
    chck_vars = [ ele         for ele in WxData.fcstChckCols ]                  # List of variable names for checking if a forecast exists
    whr       = self.__buildWhere( chck_vars )                                  # Build a 'WHERE (var1=? AND var2=?...)' statement based on the variables in the forecast check list
    ins       = self.__buildInsert( fcst_vars )                                 # Build a '() VALUES ()' statement based on the columns in the forecast table
    whr_cmd   = 'SELECT * from forecasts {}'.format( whr )                      # Build full command to look for entry
    ins_cmd   = 'INSERT INTO forecasts {}'.format(   ins )                      # Build full command to insert data
    
    for tag in forecasts:                                                       # Iterate over all the forecasts
      chck_vals = [ forecasts[tag][v] for v in chck_vars ];                     # Get value to go in each column from the info dictionary
      fcst_vals = [ forecasts[tag][v] for v in fcst_vars ];                     # Get value to go in each column from the info dictionary
      self.cursor.execute( whr_cmd, chck_vals );                                # Execute the command
      fcst = self.cursor.fetchone();                                            # Attempt to get the forecast matching the conditions
      if not fcst:                                                              # If there is nothing found, then
        self.cursor.execute( ins_cmd, fcst_vals );                              # Execute the command
      else:                                                                     # Else, must check the values in the table 
        upd_var, upd_val = [], [];                                              # Lists to store key/value pairs for data that must be updated in the SQL forecasts table
        for i in range( len(fcst) ):                                            # Iterate over all the forecast values
          if fcst[i] != fcst_vals[i]:                                           # If the value from the SQL table does NOT match the current forecast value
            upd_var.append( fcst_vars[i] );                                     # Append the variable name to the upd_var list
            upd_val.append( fcst_vals[i] );                                     # Append the value to the upd_var list
        if len(upd_var) > 0:                                                    # If there are values to update
          upd = self.__buildUpdate( upd_var );                                  # Build a 'SET key=?, key=?' statement  based on the columns in 
          upd_cmd = 'UPDATE forecasts {} {}'.format( upd, whr );                # Build the update command
          self.cursor.execute( upd_cmd, upd_val + chck_vals );                  # Update the values
    self.db.commit();                                                           # Write all changes to the database  

  def get_forecasts(self, name = None, school = None, category = None, semester = None, year = None, models = False):
    '''
    Method for getting forecasts from the database
    Keywords:
      name     : Name of the forecaster; if only this used, all forecasts
                  for this forecaster returned.
      school   : School to filter by; if only this used, all forecasts
                  for this school are returned.
      category : category to filter by; if only this used, all forecasts
                  for this category are returned.
      semester : Subset data by given semester
      year     : Subset data by given year
      models   : Default to True: gets category 8, set to False to NOT get data
    '''
    vars, vals = [], [];                                                        # Initialize lists for var names and values to search by in the SQL table
    if name is not None:                                                        # If name is NOT None
      if type(name) is not list and type(name) is not tuple:                    # Ensure that name is type list; checking if not list and not tuple
        name = [name];    
      for n in name:                                                            # Iterate over all values in name
        vars.append('name');                                                    # Append 'name' string to vars list
        vals.append(n);                                                         # Append input name to vals list
    if models:                                                                  # If models is True
      vars.append('school');                                                    # Append 'school' string to vars list
      vals.append('xxx');                                                       # Append 'xxx' to vals list
    elif school is not None:                                                    # Else, if school is NOT None;
      if type(school) is not list and type(school) is not tuple:                # Ensure that school is type list; checking if not list and not tuple
        school = [school];
      for s in school:                                                          # Iterate over all values in school
        vars.append('school');                                                  # Append 'school' string to vars list
        vals.append(s);                                                         # Append input school to vals list
    if category is not None and models is False:                                # If category is NOT None
      if type(category) is not list and type(category) is not tuple:            # Ensure that category is type list; checking if not list and not tuple
        category = [category];
      for c in category:                                                        # Iterate over all values in category
        vars.append('category');                                                # Append 'category' string to vars list
        vals.append(c);                                                         # Append input category to vals list
    if semester is not None:
      if type(semester) is not list and type(semester) is not tuple:            # Because semYear IS a tuple or list because they are paired, make certain that zeroth element is NOT a list OR tuple. If it is, then already multiple values
        semester = [semester];                                                  # Convert to list
      for s in semester:                                                        # Iterate over all values in semYear
        vars.append('semester');                                                # Append 'semester' string to vars list
        vals.append(s);                                                         # Append input semester to vals list
    if year is not None:
      if type(year) is not list and type(year) is not tuple:                    # Because semYear IS a tuple or list because they are paired, make certain that zeroth element is NOT a list OR tuple. If it is, then already multiple values
        year = [year];                                                          # Convert to list
      for y in year:                                                            # Iterate over all values in semYear
        vars.append('year');                                                    # Append 'year' string to vars list
        vals.append(y);                                                         # Append input year to vals list
    
    
    if len(vars) == 0:                                                          # If the length of vars is zero
      cmd = 'SELECT * FROM forecasts';                                          # Set the command to select all forecasts
    else:                                                                       # Else,
      whr = self.__buildWhere( vars );                                          # Use the private method to build a where statement for the command
      cmd = 'SELECT * FROM forecasts {}'.format( whr );                         # Set command with where statment
    self.log.debug( 'SQL command: {}'.format( cmd  ) )
    self.log.debug( 'SQL values:  {}'.format( vals ) )
    self.cursor.execute(cmd, vals);                                             # Execute the command
    cols = [i['name'] for i in WxData.forecastCols];
    indx = ['' for col in cols];
    for i in WxData.forecastCols:
      if i['pandas_ind']:
        indx[ i['pandas_ind_num'] ] = i['name'];
    indx = [ind for ind in indx if ind != ''];
     
    return Forecasts( self.cursor.fetchall(), columns = cols, index = indx );   # Return a new forecasts object

  def get_verification( self, dates = None):
    tmp = {}
    if isinstance(dates, (list, tuple)):
      cmd = "SELECT * FROM verifications WHERE (date=?)"
      for date in dates:
        self.cursor.execute(cmd, (date,))
        entry = self.cursor.fetchone()
        if entry:
          entry = list(entry)
          key   = entry.pop(3)
          tmp[key] = entry
    else:
      cmd = "SELECT * FROM verifications"
      self.cursor.execute(cmd)
      entry = self.cursor.fetchall()
      for e in entry:
        e = list(e)
        key = e.pop(3)
        if key:
          tmp[key] = e

    return tmp

  def get_forecaster(self, name, sch, cat):
    """
    Method to get unique key for given forecaster based on 
    name, school, and category. If no forecaster is found matching 
    information, then None is returned.

    """

    cmd = "SELECT * FROM forecasts WHERE (name=? AND school=? AND category=?)";
    self.cursor.execute( cmd, (name, sch, cat,) );
    entry = self.cursor.fetchone();
    if entry:
      return entry[-1];
    else:
      return None;

  def download_Schedule(self, year = None, all = False):
    """
    A method to get the current; or previous, forecase schedule.
    If year is used, assumed to be year of Fall semester, so will
    get schedule for year/year+1 season.
    
    """

    if all:
      self._schedule.Clear();
      year = [y for y in range(2006, self._schedule.date.year)]
    
    if year == self._schedule.date.year or year is None or all:                 # If year is None (i.e., no year input) OR all is True
      season = self.getSchedule()                  # Set up url
      if season:
        self._schedule.Update( season.parse() );                                         # Parse the schedule
      if not all:                                                               # If all is NOT set
        self.sql_Update_Schedule( );
        return;
    elif not isinstance(year, list):                                            # Else, if year is not list instance
      year = [year];                                                            # Convert year to list

    for y in year:                                                              # Iterate over all years
      syear, eyear = str(y)[-2:], str(y+1)[-2:];
      self.__log.debug( 'syear: {}, eyear: {}'.format(syear, eyear) )
      season = self.getSchedule(syear, eyear)
      if season:
        self._schedule.Update( season.parse() )                                         # Parse the schedule
    self.sql_Update_Schedule( )

  def sql_Load_Schedule(self):
    """Method to get full schedule"""
    self.__log.debug('Loading schedule from SQL Database...')
    self.cursor.execute('SELECT * FROM schedule')
    sched = self.cursor.fetchall()
    if len(sched) > 0: 
      for city in sched:
        info = {}
        for col, val in zip(WxData.scheduleCols, city):
          info[col['name']] = val
        self._schedule.Update( info )

  def sql_Update_Schedule(self):
    """Method to update the schedule in the database"""
    for semYear in self._schedule:                                              # Iterate over the semester:year tags in schedDict
      for ident in self._schedule[semYear]:                                     # Iterate over the identifier tags in schedDict[semYear]
        info = self._schedule[semYear][ident];
        vars = [ ele['name'] for ele in WxData.scheduleCols ];                  # Get list of names for each column in the schedule table
        vals = [ info[ v ] for v in vars ];                                     # Get value to go in each column from the info dictionary
        whr  = self.__buildWhere( vars );                                       # Build a 'WHERE (var1=? AND var2=?...)' statement based on the columns in the schedule table
        cmd  = 'SELECT * FROM schedule {}'.format( whr );                       # Build full command to look for entry
        self.cursor.execute( cmd, vals );                                       # Execute the command
        if not self.cursor.fetchone():                                          # If there is nothing found, then
          ins = self.__buildInsert( vars );
          cmd = 'INSERT INTO schedule {}'.format( ins );
          self.cursor.execute( cmd, vals );
          self.db.commit();

  def __createTables(self):
    """Method to create tables if None exist in the file"""
    buildCols = lambda info: ['{} {}'.format(i['name'],i['type']) for i in info]
    table1 = 'forecasts ({})'.format(     ', '.join( buildCols(WxData.forecastCols) ) )
    table2 = 'schedule ({})'.format(      ', '.join( buildCols(WxData.scheduleCols) ) )
    table3 = 'verifications ({})'.format( ', '.join( buildCols(WxData.verifyCols) ) )
    self.cursor.execute( "CREATE TABLE IF NOT EXISTS {}".format(table1) )
    self.cursor.execute( "CREATE TABLE IF NOT EXISTS {}".format(table2) )
    self.cursor.execute( "CREATE TABLE IF NOT EXISTS {}".format(table3) )
    self.db.commit();

  def __check_city(self, city, state, ident, start, end):
    """
    Get unique key for given forecaster based on name, school, and category
    
    If no forecaster is found matching 
    information, then None is returned.

    """

    cmd = "SELECT * FROM schedule WHERE ({})";
    cmd = cmd.format( ','.join(['{}=?'.format(i[0]) for i in WxData.scheduleCols]) )
    self.cursor.execute( cmd, (city, state, ident, start, end,) );
    entry = self.cursor.fetchone();
    if entry:
      return entry[-1];
    else:
      return None;

  def __buildWhere(self, cols):
    """Build where function into the SQL table"""

    vars, i = [], 0;
    while i < len(cols):
      n = cols.count( cols[i] );
      if n == 1:
        vars.append( '{}=?'.format( cols[i] ) );
      else:
        tmp = ['{}=?'.format( cols[i] )] * n;
        tmp = ' OR '.join( tmp )
        vars.append( '({})'.format(tmp) );  
      i += n      
    return "WHERE ({})".format( ' AND '.join( vars ) );
  def __buildInsert(self, cols):
    vars = [ele for ele in cols];
    vals = ['?'] * len(vars)
    return "({}) VALUES ({})".format( ','.join( vars ), ','.join( vals ) );
  def __buildUpdate(self, cols):
    vars = ['{}=?'.format(ele) for ele in cols];
    return "SET {}".format( ','.join( vars ) );

  ##############################################################################
  def close(self): 
    self.db.commit();
    self.db.close();
